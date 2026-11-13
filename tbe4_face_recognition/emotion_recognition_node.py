"""Webcam FER recognition node with a live OpenCV overlay."""

import math
import signal
import time
import uuid

import cv2
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import String

from tbe4_face_recognition.emotion_model import (
    DetectedFace,
    FerEmotionModel,
    make_observation,
)
from tbe4_face_recognition.protocol import (
    BehaviorStatus,
    Observation,
    decode_status,
    encode_observation,
)


class InferenceScheduler:
    """Separate display cadence from completed-inference sequence numbers."""

    def __init__(self, inference_period: float, session_id: str):
        if (
            not isinstance(inference_period, (int, float))
            or isinstance(inference_period, bool)
            or not math.isfinite(inference_period)
            or inference_period <= 0.0
        ):
            raise ValueError('inference_period must be finite and positive')
        if not isinstance(session_id, str) or not session_id:
            raise ValueError('session_id must be a non-empty string')
        self.inference_period = float(inference_period)
        self.session_id = session_id
        self.next_due = 0.0
        self.pending = False
        self.sequence = 0
        self.last_time = None

    def _validate_time(self, now):
        if (
            not isinstance(now, (int, float))
            or isinstance(now, bool)
            or not math.isfinite(now)
            or (self.last_time is not None and now < self.last_time)
        ):
            raise ValueError('scheduler time must be finite and monotonic')
        self.last_time = float(now)

    def should_infer(self, now: float) -> bool:
        """Reserve an inference slot when its wall-time period is due."""
        self._validate_time(now)
        if self.pending or now < self.next_due:
            return False
        self.pending = True
        return True

    def complete(
        self, faces: list[DetectedFace], now: float
    ) -> Observation:
        """Publishable observation for one completed reserved inference."""
        self._validate_time(now)
        if not self.pending:
            raise RuntimeError('no inference is pending')
        observation = make_observation(faces, self.session_id, self.sequence)
        self.sequence += 1
        self.pending = False
        self.next_due = float(now) + self.inference_period
        return observation

    def fail(self, now: float) -> Observation:
        """Create one fresh unknown observation before recognition exits."""
        self._validate_time(now)
        observation = make_observation([], self.session_id, self.sequence)
        self.sequence += 1
        self.pending = False
        self.next_due = float(now) + self.inference_period
        return observation


def try_decode_status(payload: str):
    """Return validated controller status or None for a malformed update."""
    try:
        return decode_status(payload)
    except (TypeError, ValueError):
        return None


def draw_overlay(
    frame,
    faces: list[DetectedFace],
    observation: Observation,
    status: BehaviorStatus | None,
):
    """Draw face, inference and robot state on a copy of a BGR frame."""
    if not hasattr(frame, 'shape') or len(frame.shape) != 3:
        raise ValueError('frame must be a color image')
    output = frame.copy()
    height, width = output.shape[:2]
    for face in faces:
        x, y, box_width, box_height = face.box
        left = max(0, min(width - 1, x))
        top = max(0, min(height - 1, y))
        right = max(0, min(width - 1, x + box_width))
        bottom = max(0, min(height - 1, y + box_height))
        if right <= left or bottom <= top:
            continue
        cv2.rectangle(output, (left, top), (right, bottom), (0, 220, 255), 2)
        label_y = min(height - 4, max(12, top + 14))
        cv2.putText(
            output,
            f'{face.emotion}: {face.confidence:.2f}',
            (left + 2, label_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 255, 0),
            1,
            cv2.LINE_AA,
        )

    cv2.putText(
        output,
        f'Emotion: {observation.emotion} ({observation.confidence:.2f}) '
        f'faces={observation.face_count}',
        (6, 18),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )
    if status is None:
        state_text = 'Robot: waiting for status'
    else:
        action = status.active_action or '-'
        stable = status.stable_emotion or '-'
        state_text = (
            f'Robot: {status.state} stable={stable} action={action} '
            f'reason={status.reason} '
            f'{status.motion_progress:.0%}'
        )
    cv2.putText(
        output,
        state_text,
        (6, min(height - 2, 38)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (255, 220, 0),
        1,
        cv2.LINE_AA,
    )
    return output


class EmotionRecognitionNode(Node):
    """Own a laptop webcam and publish completed FER observations."""

    def __init__(self, model=None, camera=None):
        super().__init__('emotion_recognition_node')
        defaults = {
            'camera_index': 0,
            'width': 640,
            'height': 480,
            'capture_rate_hz': 20.0,
            'inference_rate_hz': 5.0,
            'show_window': True,
            'mirror': True,
        }
        for name, default in defaults.items():
            self.declare_parameter(name, default)
        value = lambda name: self.get_parameter(name).value
        capture_rate = float(value('capture_rate_hz'))
        inference_rate = float(value('inference_rate_hz'))
        if (
            not math.isfinite(capture_rate)
            or not 1.0 <= capture_rate <= 60.0
            or not math.isfinite(inference_rate)
            or not 0.5 <= inference_rate <= capture_rate
        ):
            raise ValueError('camera rates are outside supported bounds')
        width = int(value('width'))
        height = int(value('height'))
        if width <= 0 or height <= 0:
            raise ValueError('camera dimensions must be positive')

        self.show_window = bool(value('show_window'))
        self.mirror = bool(value('mirror'))
        self.window_name = 'TurtleBot 4 - Facial Emotions'
        self.model = model or FerEmotionModel()
        self.camera = camera or cv2.VideoCapture(
            int(value('camera_index')), cv2.CAP_V4L2
        )
        self.closed = False
        self.window_created = False
        self.latest_status = None
        self.latest_faces = []
        session_id = uuid.uuid4().hex[:8]
        self.scheduler = InferenceScheduler(1.0 / inference_rate, session_id)
        self.latest_observation = Observation(
            session_id, 0, 'unknown', 0.0, 0
        )
        try:
            if not self.camera.isOpened():
                raise RuntimeError(
                    f'Cannot open /dev/video{int(value("camera_index"))}'
                )
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            if self.show_window:
                cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
                self.window_created = True
            self.observation_publisher = self.create_publisher(
                String, '/emotion_observation', 1
            )
            self.status_subscription = self.create_subscription(
                String,
                '/emotion_behavior_status',
                self._on_status,
                1,
            )
            self.timer = self.create_timer(1.0 / capture_rate, self._on_frame)
        except Exception:
            self.close()
            raise
        self.get_logger().info(
            f'Webcam ready: session={session_id}, inference={inference_rate:.1f} Hz'
        )

    def _on_status(self, message):
        status = try_decode_status(message.data)
        if status is not None:
            self.latest_status = status

    def _on_frame(self):
        ok, frame = self.camera.read()
        if not ok or frame is None:
            observation = self.scheduler.fail(time.monotonic())
            self.observation_publisher.publish(
                String(data=encode_observation(observation))
            )
            raise RuntimeError('Camera frame lost')
        if self.mirror:
            frame = cv2.flip(frame, 1)
        now = time.monotonic()
        if self.scheduler.should_infer(now):
            faces = self.model.analyze(frame)
            completed_at = time.monotonic()
            observation = self.scheduler.complete(faces, completed_at)
            self.latest_faces = faces
            self.latest_observation = observation
            self.observation_publisher.publish(
                String(data=encode_observation(observation))
            )

        if self.show_window:
            overlay = draw_overlay(
                frame,
                self.latest_faces,
                self.latest_observation,
                self.latest_status,
            )
            cv2.imshow(self.window_name, overlay)
            if cv2.waitKey(1) & 0xFF in (ord('q'), ord('Q')):
                self.close()
                self.timer.cancel()
                rclpy.shutdown()

    def close(self):
        """Release webcam and GUI resources exactly once."""
        if self.closed:
            return
        self.closed = True
        if self.camera is not None:
            self.camera.release()
        if self.window_created:
            cv2.destroyWindow(self.window_name)
            self.window_created = False


def main(args=None):
    """Run webcam recognition until Q, Ctrl+C or ROS shutdown."""
    rclpy.init(args=args)
    node = None
    failed = False
    try:
        node = EmotionRecognitionNode()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    except Exception as error:
        failed = True
        if node is not None:
            node.get_logger().fatal(str(error))
        else:
            print(f'Emotion recognition failed: {error}', flush=True)
    finally:
        previous = signal.signal(signal.SIGINT, signal.SIG_IGN)
        try:
            if node is not None:
                node.close()
                node.destroy_node()
            rclpy.try_shutdown()
        finally:
            signal.signal(signal.SIGINT, previous)
    if failed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
