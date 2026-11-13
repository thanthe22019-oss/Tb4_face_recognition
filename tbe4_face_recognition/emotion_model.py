"""Small, injectable adapter around FER's emotion-result format."""

from dataclasses import dataclass
import math
from numbers import Integral, Real

from tbe4_face_recognition.protocol import Observation


FER_EMOTIONS = frozenset(
    {'angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral'}
)


@dataclass(frozen=True)
class DetectedFace:
    """Normalized FER result for one face."""

    box: tuple[int, int, int, int]
    emotion: str
    confidence: float

    def __post_init__(self):
        if (
            not isinstance(self.box, tuple)
            or len(self.box) != 4
            or not all(isinstance(value, int) for value in self.box)
            or self.box[2] <= 0
            or self.box[3] <= 0
        ):
            raise ValueError('box must be an integer (x, y, width, height) tuple')
        if self.emotion not in FER_EMOTIONS:
            raise ValueError('emotion is not a FER label')
        if (
            isinstance(self.confidence, bool)
            or not isinstance(self.confidence, Real)
            or not math.isfinite(self.confidence)
            or not 0.0 <= self.confidence <= 1.0
        ):
            raise ValueError('confidence must be finite and in [0, 1]')


class FerEmotionModel:
    """Run FER while allowing tests to inject a lightweight detector."""

    def __init__(self, detector=None):
        if detector is None:
            from fer.fer import FER

            detector = FER(use_tflite=True, mtcnn=False)
        if not callable(getattr(detector, 'detect_emotions', None)):
            raise TypeError('detector must provide detect_emotions(frame)')
        self.detector = detector

    def analyze(self, frame) -> list[DetectedFace]:
        """Return validated faces from one BGR frame."""
        raw_faces = self.detector.detect_emotions(frame)
        if not isinstance(raw_faces, list):
            raise TypeError('FER result must be a list')
        return [self._normalize_face(face) for face in raw_faces]

    @staticmethod
    def _normalize_face(face) -> DetectedFace:
        if not isinstance(face, dict) or set(face) != {'box', 'emotions'}:
            raise ValueError('each FER face must contain box and emotions')
        box = face['box']
        if isinstance(box, (str, bytes, dict)):
            raise ValueError('FER box must contain four integers')
        try:
            box_values = tuple(box)
        except TypeError as error:
            raise ValueError('FER box must contain four integers') from error
        if (
            len(box_values) != 4
            or not all(isinstance(value, Integral) and not isinstance(value, bool)
                       for value in box_values)
        ):
            raise ValueError('FER box must contain four integers')
        normalized_box = tuple(int(value) for value in box_values)
        if normalized_box[2] <= 0 or normalized_box[3] <= 0:
            raise ValueError('FER box width and height must be positive')

        scores = face['emotions']
        if not isinstance(scores, dict) or not scores:
            raise ValueError('FER emotions must be a non-empty mapping')
        if not set(scores).issubset(FER_EMOTIONS):
            raise ValueError('FER result contains an unknown emotion')
        normalized_scores = {}
        for emotion, score in scores.items():
            if (
                isinstance(score, bool)
                or not isinstance(score, Real)
                or not math.isfinite(score)
                or not 0.0 <= score <= 1.0
            ):
                raise ValueError('FER scores must be finite and in [0, 1]')
            normalized_scores[emotion] = float(score)
        emotion = max(normalized_scores, key=normalized_scores.get)
        return DetectedFace(
            normalized_box, emotion, normalized_scores[emotion]
        )


def make_observation(
    faces: list[DetectedFace], session_id: str, sequence: int
) -> Observation:
    """Convert normalized faces into the single-operator wire contract."""
    if not isinstance(faces, list) or not all(
        isinstance(face, DetectedFace) for face in faces
    ):
        raise TypeError('faces must be a list of DetectedFace values')
    if len(faces) == 1:
        emotion = faces[0].emotion
        confidence = faces[0].confidence
    else:
        emotion = 'unknown'
        confidence = 0.0
    return Observation(session_id, sequence, emotion, confidence, len(faces))
