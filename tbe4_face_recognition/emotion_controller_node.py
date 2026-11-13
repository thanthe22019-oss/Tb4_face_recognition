"""ROS adapter for filtered emotion behavior and odometry motion."""

import math
import signal
import time

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from std_msgs.msg import String

from tbe4_face_recognition.behavior import BehaviorController, BehaviorDecision
from tbe4_face_recognition.emotion_filter import EmotionFilter
from tbe4_face_recognition.motion import (
    MotionConfig,
    MotionExecutor,
    OdometryGuard,
    Pose,
    Velocity,
)
from tbe4_face_recognition.protocol import (
    Observation,
    decode_observation,
    encode_status,
)


def pose_from_odometry(message: Odometry) -> tuple[Pose, float]:
    """Convert a ROS odometry message into a normalized planar pose."""
    position = message.pose.pose.position
    orientation = message.pose.pose.orientation
    values = [
        position.x,
        position.y,
        orientation.x,
        orientation.y,
        orientation.z,
        orientation.w,
    ]
    if not all(math.isfinite(value) for value in values):
        raise ValueError('odometry contains non-finite values')
    norm = math.sqrt(
        orientation.x ** 2
        + orientation.y ** 2
        + orientation.z ** 2
        + orientation.w ** 2
    )
    if norm < 1e-8:
        raise ValueError('odometry quaternion has zero norm')
    x = orientation.x / norm
    y = orientation.y / norm
    z = orientation.z / norm
    w = orientation.w / norm
    yaw = math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))
    stamp = (
        float(message.header.stamp.sec)
        + float(message.header.stamp.nanosec) * 1e-9
    )
    if not math.isfinite(stamp) or stamp < 0.0:
        raise ValueError('odometry timestamp is invalid')
    return Pose(position.x, position.y, yaw), stamp


def publish_velocity(publisher, velocity: Velocity) -> Twist:
    """Publish one pure velocity result as a ROS Twist."""
    if not isinstance(velocity, Velocity):
        raise TypeError('velocity must be a Velocity')
    message = Twist()
    message.linear.x = velocity.linear_x
    message.angular.z = velocity.angular_z
    publisher.publish(message)
    return message


class ControlCore:
    """Compose filter, behavior and motion without ROS callback coupling."""

    def __init__(
        self,
        preview_only=True,
        filter_=None,
        motion_config=None,
        odometry_guard=None,
    ):
        self.filter = filter_ or EmotionFilter()
        self.behavior = BehaviorController(preview_only=preview_only)
        self.motion_config = motion_config or MotionConfig()
        self.odometry = odometry_guard or OdometryGuard()
        self.motion = None
        self.last_velocity = Velocity(0.0, 0.0, False, 0.0)

    @staticmethod
    def _zero(progress=0.0):
        return Velocity(0.0, 0.0, False, progress)

    def _apply_decision(self, decision: BehaviorDecision, now: float):
        if decision.cancel_motion:
            self.motion = None
        if decision.start_action is not None:
            if self.odometry.pose is None:
                self.behavior.cancel('odometry_unavailable')
                self.motion = None
            else:
                self.motion = MotionExecutor(
                    decision.start_action,
                    self.odometry.pose,
                    now,
                    self.motion_config,
                )

    def receive_observation(self, observation: Observation, now: float):
        """Apply one decoded inference observation."""
        result = self.filter.observe(observation, now)
        decision = self.behavior.receive(
            result, now, self.odometry.ready(now)
        )
        self._apply_decision(decision, now)
        return decision

    def update_odometry(self, pose: Pose, stamp: float, now: float):
        """Update fresh pose and cancel motion on discontinuity."""
        reason = self.odometry.update(pose, stamp, now)
        if reason is not None:
            self.behavior.cancel(reason)
            self.motion = None
            self.last_velocity = self._zero()
        return reason

    def compute_control(self, now: float) -> Velocity:
        """Compute one safe 20 Hz control result."""
        stale = self.filter.tick(now)
        if stale is not None:
            decision = self.behavior.receive(
                stale, now, self.odometry.ready(now)
            )
            self._apply_decision(decision, now)

        if self.behavior.state != 'EXECUTING':
            self.motion = None
            self.last_velocity = self._zero()
            return self.last_velocity
        if not self.odometry.ready(now) or self.odometry.pose is None:
            self.behavior.cancel('odometry_unavailable')
            self.motion = None
            self.last_velocity = self._zero()
            return self.last_velocity
        if self.motion is None:
            self.behavior.cancel('motion_unavailable')
            self.last_velocity = self._zero()
            return self.last_velocity

        try:
            velocity = self.motion.step(self.odometry.pose, now)
        except (TypeError, ValueError, RuntimeError) as error:
            self.behavior.cancel(str(error))
            self.motion = None
            self.last_velocity = self._zero()
            return self.last_velocity
        if velocity.done:
            self.behavior.complete(now)
            self.motion = None
            self.last_velocity = self._zero(progress=1.0)
            return self.last_velocity
        self.last_velocity = velocity
        return velocity

    def stop(self, reason='shutdown') -> Velocity:
        """Synchronously cancel motion and return an explicit zero command."""
        self.behavior.cancel(reason)
        self.motion = None
        self.last_velocity = self._zero()
        return self.last_velocity


class EmotionControllerNode(Node):
    """Publish the sole `/cmd_vel` stream for emotion interaction."""

    def __init__(self):
        super().__init__('emotion_controller_node')
        defaults = {
            'preview_only': True,
            'rate_hz': 20.0,
            'confidence_threshold': 0.60,
            'stable_seconds': 0.0,
            'rearm_seconds': 0.75,
            'observation_timeout': 0.75,
            'odom_timeout': 0.5,
            **vars(MotionConfig()),
        }
        for name, default in defaults.items():
            self.declare_parameter(name, default)
        value = lambda name: self.get_parameter(name).value
        if self.get_parameter('use_sim_time').value:
            raise ValueError('controller must use wall time: use_sim_time=false')
        rate_hz = float(value('rate_hz'))
        if not math.isfinite(rate_hz) or not 1.0 <= rate_hz <= 100.0:
            raise ValueError('rate_hz must be in [1, 100]')
        filter_ = EmotionFilter(
            confidence_threshold=float(value('confidence_threshold')),
            stable_seconds=float(value('stable_seconds')),
            rearm_seconds=float(value('rearm_seconds')),
            max_observation_gap=float(value('observation_timeout')),
        )
        motion_config = MotionConfig(**{
            name: float(value(name)) for name in vars(MotionConfig())
        })
        odometry = OdometryGuard(float(value('odom_timeout')))
        self.core = ControlCore(
            preview_only=bool(value('preview_only')),
            filter_=filter_,
            motion_config=motion_config,
            odometry_guard=odometry,
        )
        self.velocity_publisher = self.create_publisher(Twist, '/cmd_vel', 1)
        self.status_publisher = self.create_publisher(
            String, '/emotion_behavior_status', 1
        )
        self.observation_subscription = self.create_subscription(
            String, '/emotion_observation', self._on_observation, 1
        )
        self.odometry_subscription = self.create_subscription(
            Odometry, '/odom', self._on_odometry, qos_profile_sensor_data
        )
        self.timer = self.create_timer(1.0 / rate_hz, self._on_timer)
        mode = 'PREVIEW: zero velocity only' if self.core.behavior.preview_only else 'MOTION ENABLED'
        self.get_logger().info(mode)

    def _on_observation(self, message):
        now = time.monotonic()
        try:
            self.core.receive_observation(decode_observation(message.data), now)
        except (TypeError, ValueError) as error:
            self.core.stop('invalid_observation')
            self.get_logger().error(f'Invalid emotion observation: {error}')

    def _on_odometry(self, message):
        now = time.monotonic()
        try:
            pose, stamp = pose_from_odometry(message)
            reason = self.core.update_odometry(pose, stamp, now)
            if reason is not None:
                self.get_logger().warning(f'Odometry discontinuity: {reason}')
        except (TypeError, ValueError) as error:
            self.core.stop('invalid_odometry')
            self.get_logger().error(f'Invalid odometry: {error}')

    def _on_timer(self):
        now = time.monotonic()
        velocity = self.core.compute_control(now)
        publish_velocity(self.velocity_publisher, velocity)
        status = self.core.behavior.snapshot(
            self.core.odometry.ready(now), velocity.progress
        )
        self.status_publisher.publish(String(data=encode_status(status)))

    def close(self):
        """Publish a final stop before ROS entities are destroyed."""
        publish_velocity(self.velocity_publisher, self.core.stop('shutdown'))


def main(args=None):
    """Run the controller until ROS shutdown."""
    rclpy.init(args=args)
    node = None
    failed = False
    try:
        node = EmotionControllerNode()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    except Exception as error:
        failed = True
        if node is not None:
            node.get_logger().fatal(str(error))
        else:
            print(f'Emotion controller failed: {error}', flush=True)
    finally:
        previous = signal.signal(signal.SIGINT, signal.SIG_IGN)
        try:
            if node is not None:
                if rclpy.ok():
                    node.close()
                node.destroy_node()
            rclpy.try_shutdown()
        finally:
            signal.signal(signal.SIGINT, previous)
    if failed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
