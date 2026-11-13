"""Strict JSON contracts transported through ROS ``std_msgs/String``."""

from dataclasses import asdict, dataclass
import json
import math
from typing import Optional


RAW_EMOTIONS = frozenset(
    {'happy', 'sad', 'neutral', 'angry', 'surprise', 'fear', 'disgust', 'unknown'}
)
OBSERVATION_KEYS = {
    'session_id', 'sequence', 'emotion', 'confidence', 'face_count'
}
STATUS_KEYS = {
    'state', 'stable_emotion', 'active_action', 'reason', 'preview_only',
    'odometry_ready', 'motion_progress'
}


def _is_integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _require_exact_keys(document, expected):
    if not isinstance(document, dict) or set(document) != expected:
        raise ValueError(f'Expected exactly these fields: {sorted(expected)}')


@dataclass(frozen=True)
class Observation:
    """One completed emotion inference result."""

    session_id: str
    sequence: int
    emotion: str
    confidence: float
    face_count: int

    def __post_init__(self):
        if not isinstance(self.session_id, str) or not self.session_id:
            raise ValueError('session_id must be a non-empty string')
        if not _is_integer(self.sequence) or self.sequence < 0:
            raise TypeError('sequence must be a non-negative integer')
        if not isinstance(self.emotion, str) or self.emotion not in RAW_EMOTIONS:
            raise ValueError('emotion is not supported by the protocol')
        if (
            not _is_number(self.confidence)
            or not math.isfinite(self.confidence)
            or not 0.0 <= self.confidence <= 1.0
        ):
            raise ValueError('confidence must be finite and in [0, 1]')
        if not _is_integer(self.face_count) or self.face_count < 0:
            raise TypeError('face_count must be a non-negative integer')


@dataclass(frozen=True)
class BehaviorStatus:
    """Controller state rendered by the recognition overlay."""

    state: str
    stable_emotion: Optional[str]
    active_action: Optional[str]
    reason: str
    preview_only: bool
    odometry_ready: bool
    motion_progress: float

    def __post_init__(self):
        if not isinstance(self.state, str) or not self.state:
            raise ValueError('state must be a non-empty string')
        if self.stable_emotion is not None and self.stable_emotion not in RAW_EMOTIONS:
            raise ValueError('stable_emotion is invalid')
        if self.active_action is not None and (
            not isinstance(self.active_action, str) or not self.active_action
        ):
            raise ValueError('active_action must be null or a non-empty string')
        if not isinstance(self.reason, str) or not self.reason:
            raise ValueError('reason must be a non-empty string')
        if type(self.preview_only) is not bool or type(self.odometry_ready) is not bool:
            raise TypeError('preview_only and odometry_ready must be booleans')
        if (
            not _is_number(self.motion_progress)
            or not math.isfinite(self.motion_progress)
            or not 0.0 <= self.motion_progress <= 1.0
        ):
            raise ValueError('motion_progress must be finite and in [0, 1]')


def _encode(value):
    return json.dumps(
        asdict(value), allow_nan=False, separators=(',', ':'), sort_keys=True
    )


def encode_observation(value: Observation) -> str:
    """Serialize an observation with stable JSON formatting."""
    if not isinstance(value, Observation):
        raise TypeError('value must be an Observation')
    return _encode(value)


def decode_observation(payload: str) -> Observation:
    """Parse and validate a complete observation payload."""
    document = json.loads(payload)
    _require_exact_keys(document, OBSERVATION_KEYS)
    return Observation(**document)


def encode_status(value: BehaviorStatus) -> str:
    """Serialize controller status with stable JSON formatting."""
    if not isinstance(value, BehaviorStatus):
        raise TypeError('value must be a BehaviorStatus')
    return _encode(value)


def decode_status(payload: str) -> BehaviorStatus:
    """Parse and validate a complete controller-status payload."""
    document = json.loads(payload)
    _require_exact_keys(document, STATUS_KEYS)
    return BehaviorStatus(**document)
