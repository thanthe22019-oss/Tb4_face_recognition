"""Tests for normalizing the FER library's public result format."""

import math

import numpy as np
import pytest

from tbe4_face_recognition.emotion_model import (
    DetectedFace,
    FerEmotionModel,
    make_observation,
)


class FakeDetector:
    def __init__(self, result):
        self.result = result
        self.received = None

    def detect_emotions(self, frame):
        self.received = frame
        return self.result


def test_adapter_selects_highest_emotion_and_preserves_box():
    frame = object()
    detector = FakeDetector([
        {
            'box': [12, 8, 60, 80],
            'emotions': {
                'angry': 0.01,
                'disgust': 0.0,
                'fear': 0.02,
                'happy': 0.91,
                'sad': 0.01,
                'surprise': 0.04,
                'neutral': 0.01,
            },
        }
    ])

    faces = FerEmotionModel(detector).analyze(frame)

    assert detector.received is frame
    assert faces == [DetectedFace((12, 8, 60, 80), 'happy', 0.91)]
    assert make_observation(faces, 'abc12345', 7).emotion == 'happy'
    assert make_observation(faces, 'abc12345', 7).confidence == 0.91


def test_adapter_accepts_opencv_numpy_box_from_real_fer_detector():
    detector = FakeDetector([
        {
            'box': np.array([12, 8, 60, 80], dtype=np.int32),
            'emotions': {'happy': 0.91, 'neutral': 0.09},
        }
    ])

    faces = FerEmotionModel(detector).analyze(object())

    assert faces == [DetectedFace((12, 8, 60, 80), 'happy', 0.91)]


@pytest.mark.parametrize(
    ('faces', 'face_count'),
    [
        ([], 0),
        ([DetectedFace((0, 0, 10, 10), 'happy', 0.8),
          DetectedFace((20, 0, 10, 10), 'neutral', 0.7)], 2),
    ],
)
def test_non_single_face_observation_is_unknown(faces, face_count):
    observation = make_observation(faces, 'session', 3)

    assert observation.emotion == 'unknown'
    assert observation.confidence == 0.0
    assert observation.face_count == face_count


@pytest.mark.parametrize(
    'result',
    [
        [{'box': [0, 0, 10], 'emotions': {'happy': 1.0}}],
        [{'box': [0, 0, 0, 10], 'emotions': {'happy': 1.0}}],
        [{'box': [0, 0, 10, 10], 'emotions': {'joy': 1.0}}],
        [{'box': [0, 0, 10, 10], 'emotions': {'happy': math.nan}}],
        [{'box': [0, 0, 10, 10], 'emotions': {'happy': 1.2}}],
        [{'box': [0, 0, 10, 10], 'emotions': {}}],
        [{'box': [0, 0, 10, 10]}],
    ],
)
def test_adapter_rejects_malformed_fer_results(result):
    with pytest.raises((TypeError, ValueError)):
        FerEmotionModel(FakeDetector(result)).analyze(object())


def test_adapter_rejects_non_list_detector_result():
    with pytest.raises(TypeError):
        FerEmotionModel(FakeDetector({'box': []})).analyze(object())
