"""Bounded odometry-feedback motion profiles with no ROS dependency."""

from dataclasses import dataclass
import math
from numbers import Real


def _finite_number(value):
    return (
        isinstance(value, Real)
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def wrap(angle):
    """Wrap an angle to [-pi, pi]."""
    if not _finite_number(angle):
        raise ValueError('angle must be finite')
    return math.atan2(math.sin(angle), math.cos(angle))


@dataclass(frozen=True)
class Pose:
    """Planar odometry pose."""

    x: float
    y: float
    yaw: float

    def __post_init__(self):
        if not all(_finite_number(value) for value in (self.x, self.y, self.yaw)):
            raise ValueError('pose values must be finite')


@dataclass(frozen=True)
class Velocity:
    """One bounded velocity command and profile status."""

    linear_x: float
    angular_z: float
    done: bool
    progress: float

    def __post_init__(self):
        if not all(_finite_number(value) for value in (self.linear_x, self.angular_z)):
            raise ValueError('velocity values must be finite')
        if type(self.done) is not bool:
            raise TypeError('done must be a boolean')
        if not _finite_number(self.progress) or not 0.0 <= self.progress <= 1.0:
            raise ValueError('progress must be finite and in [0, 1]')


@dataclass(frozen=True)
class MotionConfig:
    """Conservative TurtleBot 4 demo motion limits."""

    linear_speed: float = 0.10
    reverse_speed: float = 0.08
    angular_speed: float = 0.40
    arc_radius: float = 0.40
    arc_angle: float = math.pi / 3.0
    travel_distance: float = 0.20
    distance_tolerance: float = 0.008
    angle_tolerance: float = 0.025
    settle_seconds: float = 0.30
    segment_timeout: float = 30.0

    def __post_init__(self):
        if any(
            not _finite_number(value) or value <= 0.0
            for value in vars(self).values()
        ):
            raise ValueError('motion configuration must be finite and positive')
        if self.linear_speed > 0.20 or self.reverse_speed > 0.20:
            raise ValueError('linear speed must not exceed 0.20 m/s')
        if self.angular_speed > 0.60:
            raise ValueError('angular speed must not exceed 0.60 rad/s')
        if self.travel_distance <= self.distance_tolerance:
            raise ValueError('travel target must exceed distance tolerance')
        if self.arc_angle <= self.angle_tolerance:
            raise ValueError('angular target must exceed angle tolerance')


class MotionExecutor:
    """Execute one relative line, arc or full-turn profile."""

    ACTIONS = frozenset(
        {'arc_left', 'arc_right', 'reverse', 'rotate_full', 'forward'}
    )

    def __init__(
        self,
        action: str,
        start_pose: Pose,
        now: float,
        config: MotionConfig = None,
    ):
        if action not in self.ACTIONS:
            raise ValueError('unknown motion action')
        if not isinstance(start_pose, Pose):
            raise TypeError('start_pose must be a Pose')
        if not _finite_number(now):
            raise ValueError('start time must be finite')
        self.action = action
        self.start_pose = start_pose
        self.config = config or MotionConfig()
        if not isinstance(self.config, MotionConfig):
            raise TypeError('config must be a MotionConfig')
        self.started_at = float(now)
        self.last_time = float(now)
        self.previous_yaw = start_pose.yaw
        self.turn_progress = 0.0
        self.settle_until = None
        self.done = False

    @staticmethod
    def _zero(done=False, progress=0.0):
        return Velocity(0.0, 0.0, done, progress)

    def _progress(self, pose):
        config = self.config
        if self.action in {'forward', 'reverse'}:
            traveled = math.hypot(
                pose.x - self.start_pose.x, pose.y - self.start_pose.y
            )
            return min(1.0, traveled / config.travel_distance)
        target = 2.0 * math.pi if self.action == 'rotate_full' else config.arc_angle
        direction = -1.0 if self.action == 'arc_right' else 1.0
        return min(1.0, max(0.0, direction * self.turn_progress / target))

    def step(self, pose: Pose, now: float) -> Velocity:
        """Return the next velocity from current odometry."""
        if not isinstance(pose, Pose):
            raise TypeError('pose must be a Pose')
        if not _finite_number(now) or now < self.last_time:
            raise ValueError('motion time must be finite and monotonic')
        if self.done:
            return self._zero(done=True, progress=1.0)
        if now - self.started_at > self.config.segment_timeout:
            raise RuntimeError('motion_timeout')
        self.last_time = float(now)
        self.turn_progress += wrap(pose.yaw - self.previous_yaw)
        self.previous_yaw = pose.yaw
        progress = self._progress(pose)

        if self.settle_until is not None:
            if now >= self.settle_until:
                self.done = True
                return self._zero(done=True, progress=1.0)
            return self._zero(progress=1.0)

        config = self.config
        if self.action in {'forward', 'reverse'}:
            traveled = math.hypot(
                pose.x - self.start_pose.x, pose.y - self.start_pose.y
            )
            remaining = config.travel_distance - traveled
            if remaining > config.distance_tolerance:
                limit = (
                    config.reverse_speed
                    if self.action == 'reverse'
                    else config.linear_speed
                )
                direction = -1.0 if self.action == 'reverse' else 1.0
                linear = direction * min(limit, max(0.02, remaining))
                heading_error = wrap(self.start_pose.yaw - pose.yaw)
                angular = max(-0.20, min(0.20, 1.5 * heading_error))
                return Velocity(linear, angular, False, progress)
        else:
            target = (
                2.0 * math.pi
                if self.action == 'rotate_full'
                else config.arc_angle
            )
            direction = -1.0 if self.action == 'arc_right' else 1.0
            remaining = target - direction * self.turn_progress
            if remaining > config.angle_tolerance:
                if self.action == 'rotate_full':
                    angular_limit = config.angular_speed
                    linear = 0.0
                else:
                    angular_limit = min(
                        config.angular_speed,
                        config.linear_speed / config.arc_radius,
                    )
                    linear = config.arc_radius * min(
                        angular_limit, max(0.05, remaining)
                    )
                angular = direction * min(
                    angular_limit, max(0.05, remaining)
                )
                return Velocity(linear, angular, False, progress)

        self.settle_until = now + config.settle_seconds
        return self._zero(progress=1.0)


class OdometryGuard:
    """Validate odometry continuity and wall-time freshness."""

    def __init__(self, timeout_seconds: float = 0.5):
        if not _finite_number(timeout_seconds) or timeout_seconds <= 0.0:
            raise ValueError('odometry timeout must be finite and positive')
        self.timeout_seconds = float(timeout_seconds)
        self.pose = None
        self.stamp = None
        self.received_at = None

    def update(self, pose: Pose, stamp: float, received_at: float):
        """Accept a fresh sample and report discontinuities."""
        if not isinstance(pose, Pose):
            raise TypeError('pose must be a Pose')
        if not _finite_number(stamp) or stamp < 0.0:
            raise ValueError('odometry stamp must be finite and non-negative')
        if not _finite_number(received_at) or received_at < 0.0:
            raise ValueError('received time must be finite and non-negative')
        if self.stamp is not None and stamp == self.stamp:
            return None

        reason = None
        if self.stamp is not None and stamp < self.stamp:
            reason = 'odom_reset'
        elif self.pose is not None and (
            math.hypot(pose.x - self.pose.x, pose.y - self.pose.y) > 0.5
            or abs(wrap(pose.yaw - self.pose.yaw)) > 1.0
        ):
            reason = 'odom_jump'
        self.pose = pose
        self.stamp = float(stamp)
        self.received_at = float(received_at)
        return reason

    def ready(self, now: float) -> bool:
        """Return whether a unique sample arrived recently in wall time."""
        if not _finite_number(now) or self.received_at is None:
            return False
        return 0.0 <= now - self.received_at < self.timeout_seconds
