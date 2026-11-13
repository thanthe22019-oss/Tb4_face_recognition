"""Immediate confidence filtering independent of ROS and TensorFlow."""

from dataclasses import dataclass
import math
from typing import Optional

from tbe4_face_recognition.protocol import Observation


CONTROL_EMOTIONS = frozenset(
    {'happy', 'sad', 'neutral', 'angry', 'surprise', 'fear'}
)


@dataclass(frozen=True)
class FilterResult:
    """One normalized filter transition."""

    normalized: str
    stable_emotion: Optional[str]
    changed: bool
    stop_reason: Optional[str]


class EmotionFilter:
    """Expose confident labels immediately while enforcing transport freshness."""

    def __init__(
        self,
        confidence_threshold=0.60,
        stable_seconds=0.0,
        rearm_seconds=0.75,
        max_observation_gap=0.75,
    ):
        positive_values = [rearm_seconds, max_observation_gap]
        if (
            not math.isfinite(confidence_threshold)
            or not 0.0 < confidence_threshold <= 1.0
            or not math.isfinite(stable_seconds)
            or stable_seconds < 0.0
            or any(
                not math.isfinite(value) or value <= 0.0
                for value in positive_values
            )
        ):
            raise ValueError('filter thresholds must be finite and positive')
        self.confidence_threshold = float(confidence_threshold)
        self.stable_seconds = float(stable_seconds)
        self.rearm_seconds = float(rearm_seconds)
        self.max_observation_gap = float(max_observation_gap)
        self.reset()

    def reset(self):
        """Forget transport freshness and candidate state."""
        self.session_id = None
        self.last_sequence = None
        self.last_observation_time = None
        self.last_time = None
        self.candidate = None
        self.candidate_since = None
        self.stable_emotion = None

    def _valid_time(self, now):
        return (
            isinstance(now, (int, float))
            and not isinstance(now, bool)
            and math.isfinite(now)
            and (self.last_time is None or now >= self.last_time)
        )

    @staticmethod
    def _stop(reason):
        return FilterResult('unknown', None, False, reason)

    def _normalize(self, observation):
        if observation.face_count == 0:
            return 'unknown', 'no_face'
        if observation.face_count != 1:
            return 'unknown', 'multiple_faces'
        if observation.emotion == 'disgust':
            return 'unknown', 'unsupported_emotion'
        if observation.emotion not in CONTROL_EMOTIONS:
            return 'unknown', 'unknown_emotion'
        if observation.confidence <= self.confidence_threshold:
            return 'unknown', 'low_confidence'
        return observation.emotion, None

    def observe(self, observation: Observation, now: float) -> FilterResult:
        """Accept one completed inference and update the stable label."""
        if not isinstance(observation, Observation):
            raise TypeError('observation must be an Observation')
        if not self._valid_time(now):
            return self._stop('invalid_time')

        if self.session_id is not None and observation.session_id != self.session_id:
            self.session_id = observation.session_id
            self.last_sequence = observation.sequence
            self.last_observation_time = now
            self.last_time = now
            self.candidate = 'unknown'
            self.candidate_since = now
            self.stable_emotion = None
            return self._stop('recognition_restarted')

        if self.session_id is None:
            self.session_id = observation.session_id
        elif observation.sequence <= self.last_sequence:
            self.last_time = now
            return self._stop('invalid_sequence')

        self.last_sequence = observation.sequence
        self.last_observation_time = now
        self.last_time = now
        normalized, stop_reason = self._normalize(observation)

        if normalized != self.candidate:
            self.candidate = normalized
            self.candidate_since = now
            self.stable_emotion = None

        threshold = (
            self.rearm_seconds if normalized == 'unknown' else self.stable_seconds
        )
        changed = False
        if now - self.candidate_since >= threshold:
            changed = self.stable_emotion != normalized
            self.stable_emotion = normalized

        return FilterResult(
            normalized, self.stable_emotion, changed, stop_reason
        )

    def tick(self, now: float) -> Optional[FilterResult]:
        """Return a safety stop when inference freshness expires."""
        if not self._valid_time(now):
            return self._stop('invalid_time')
        self.last_time = now
        if self.last_observation_time is None:
            return None
        if now - self.last_observation_time > self.max_observation_gap:
            return self._stop('observation_timeout')
        return None
