"""One-shot emotion behavior state machine, independent of ROS."""

from dataclasses import dataclass
import math
from typing import Optional

from tbe4_face_recognition.emotion_filter import FilterResult
from tbe4_face_recognition.protocol import BehaviorStatus


ACTION_BY_EMOTION = {
    'happy': 'arc_left',
    'sad': 'arc_right',
    'angry': 'reverse',
    'surprise': 'rotate_full',
    'fear': 'forward',
}


@dataclass(frozen=True)
class BehaviorDecision:
    """Side effects requested by one state-machine transition."""

    start_action: Optional[str] = None
    cancel_motion: bool = False


class BehaviorController:
    """Consume stable emotions once, requiring neutral/unknown to re-arm."""

    def __init__(self, preview_only: bool):
        if type(preview_only) is not bool:
            raise TypeError('preview_only must be a boolean')
        self.preview_only = preview_only
        self.state = 'ARMED'
        self.stable_emotion = None
        self.active_action = None
        self.reason = 'startup_armed'
        self.last_time = None

    def _valid_time(self, now):
        return (
            isinstance(now, (int, float))
            and not isinstance(now, bool)
            and math.isfinite(now)
            and (self.last_time is None or now >= self.last_time)
        )

    def _disarm(self, reason):
        self.state = 'DISARMED'
        self.active_action = None
        self.reason = reason

    def receive(
        self,
        result: FilterResult,
        now: float,
        odometry_ready: bool,
    ) -> BehaviorDecision:
        """Apply one filter result and return requested motion side effects."""
        if not isinstance(result, FilterResult):
            raise TypeError('result must be a FilterResult')
        if type(odometry_ready) is not bool:
            raise TypeError('odometry_ready must be a boolean')
        if not self._valid_time(now):
            cancel = self.state == 'EXECUTING'
            self._disarm('invalid_time')
            self.last_time = None
            return BehaviorDecision(cancel_motion=cancel)
        self.last_time = now
        self.stable_emotion = result.stable_emotion

        if result.stop_reason is not None:
            cancel = self.state == 'EXECUTING'
            self._disarm(result.stop_reason)
            if result.stable_emotion in {'neutral', 'unknown'}:
                self.state = 'ARMED'
                self.reason = 'rearmed'
            return BehaviorDecision(cancel_motion=cancel)

        if result.stable_emotion in {'neutral', 'unknown'}:
            cancel = self.state == 'EXECUTING'
            self.state = 'ARMED'
            self.active_action = None
            self.reason = 'rearmed'
            return BehaviorDecision(cancel_motion=cancel)

        if (
            result.stable_emotion not in ACTION_BY_EMOTION
            or not result.changed
        ):
            return BehaviorDecision()

        if self.state == 'EXECUTING':
            self._disarm('emotion_changed')
            return BehaviorDecision(cancel_motion=True)
        if self.state != 'ARMED':
            self.reason = 'awaiting_rearm'
            return BehaviorDecision()

        action = ACTION_BY_EMOTION[result.stable_emotion]
        if self.preview_only:
            self._disarm('preview_completed')
            return BehaviorDecision()
        if not odometry_ready:
            self._disarm('odometry_unavailable')
            return BehaviorDecision()

        self.state = 'EXECUTING'
        self.active_action = action
        self.reason = 'started'
        return BehaviorDecision(start_action=action)

    def complete(self, now: float) -> None:
        """Finish the current action without automatically re-arming."""
        if not self._valid_time(now):
            self._disarm('invalid_time')
            self.last_time = None
            return
        self.last_time = now
        if self.state == 'EXECUTING':
            self._disarm('completed')

    def cancel(self, reason: str) -> None:
        """Cancel any active action and require re-arm."""
        if not isinstance(reason, str) or not reason:
            raise ValueError('reason must be a non-empty string')
        self._disarm(reason)

    def snapshot(
        self, odometry_ready: bool, motion_progress: float = 0.0
    ) -> BehaviorStatus:
        """Return the public controller status."""
        return BehaviorStatus(
            state=self.state,
            stable_emotion=self.stable_emotion,
            active_action=self.active_action,
            reason=self.reason,
            preview_only=self.preview_only,
            odometry_ready=odometry_ready,
            motion_progress=motion_progress,
        )
