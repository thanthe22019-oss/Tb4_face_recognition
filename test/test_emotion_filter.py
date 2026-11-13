"""Tests for temporal filtering and inference freshness."""

import math

import pytest

from tbe4_face_recognition.emotion_filter import EmotionFilter
from tbe4_face_recognition.protocol import Observation


def observation(
    sequence, emotion='happy', confidence=0.9, face_count=1, session='session-a'
):
    return Observation(session, sequence, emotion, confidence, face_count)


def test_non_neutral_emotion_stabilizes_after_half_second():
    filter_ = EmotionFilter()

    assert filter_.observe(observation(0), 0.0).stable_emotion is None
    assert filter_.observe(observation(1), 0.49).stable_emotion is None
    result = filter_.observe(observation(2), 0.50)

    assert result.stable_emotion == 'happy'
    assert result.changed is True
    assert filter_.observe(observation(3), 0.60).changed is False


def test_label_change_restarts_candidate_duration():
    filter_ = EmotionFilter()
    filter_.observe(observation(0, 'happy'), 0.0)
    filter_.observe(observation(1, 'happy'), 0.4)

    assert filter_.observe(observation(2, 'sad'), 0.5).stable_emotion is None
    assert filter_.observe(observation(3, 'sad'), 0.99).stable_emotion is None
    assert filter_.observe(observation(4, 'sad'), 1.0).stable_emotion == 'sad'


@pytest.mark.parametrize('emotion', ['neutral', 'unknown'])
def test_rearm_emotions_need_three_quarters_second(emotion):
    filter_ = EmotionFilter()

    filter_.observe(observation(0, emotion, 0.9 if emotion == 'neutral' else 0.0,
                                1 if emotion == 'neutral' else 0), 0.0)
    assert filter_.observe(
        observation(1, emotion, 0.9 if emotion == 'neutral' else 0.0,
                    1 if emotion == 'neutral' else 0),
        0.74,
    ).stable_emotion is None
    assert filter_.observe(
        observation(2, emotion, 0.9 if emotion == 'neutral' else 0.0,
                    1 if emotion == 'neutral' else 0),
        0.75,
    ).stable_emotion == emotion


@pytest.mark.parametrize(
    ('value', 'reason'),
    [
        (observation(0, 'unknown', 0.0, 0), 'no_face'),
        (observation(0, 'unknown', 0.0, 2), 'multiple_faces'),
        (observation(0, 'happy', 0.54, 1), 'low_confidence'),
        (observation(0, 'disgust', 0.9, 1), 'unsupported_emotion'),
    ],
)
def test_invalid_face_observations_request_immediate_stop(value, reason):
    result = EmotionFilter().observe(value, 0.0)

    assert result.normalized == 'unknown'
    assert result.stable_emotion is None
    assert result.stop_reason == reason


def test_duplicate_or_backward_sequence_does_not_refresh_watchdog():
    filter_ = EmotionFilter()
    filter_.observe(observation(2), 0.0)

    assert filter_.observe(observation(2), 0.4).stop_reason == 'invalid_sequence'
    assert filter_.observe(observation(1), 0.5).stop_reason == 'invalid_sequence'
    assert filter_.tick(0.76).stop_reason == 'observation_timeout'


def test_stale_observation_stops_execution():
    filter_ = EmotionFilter(max_observation_gap=0.75)
    filter_.observe(observation(0), 10.0)

    assert filter_.tick(10.749) is None
    result = filter_.tick(10.751)

    assert result.normalized == 'unknown'
    assert result.stop_reason == 'observation_timeout'


def test_new_session_stops_and_requires_new_stability_window():
    filter_ = EmotionFilter()
    filter_.observe(observation(0), 0.0)
    assert filter_.observe(observation(1), 0.5).stable_emotion == 'happy'

    restarted = filter_.observe(observation(0, session='session-b'), 0.6)
    assert restarted.stop_reason == 'recognition_restarted'
    assert restarted.stable_emotion is None
    assert filter_.observe(
        observation(1, 'neutral', session='session-b'), 0.7
    ).stable_emotion is None
    assert filter_.observe(
        observation(2, 'neutral', session='session-b'), 1.45
    ).stable_emotion == 'neutral'


@pytest.mark.parametrize('now', [math.nan, math.inf, -0.1])
def test_invalid_or_backward_time_requests_stop(now):
    filter_ = EmotionFilter()
    filter_.observe(observation(0), 0.0)

    assert filter_.tick(now).stop_reason == 'invalid_time'


@pytest.mark.parametrize(
    'kwargs',
    [
        {'confidence_threshold': 0.0},
        {'confidence_threshold': 1.1},
        {'stable_seconds': 0.0},
        {'rearm_seconds': math.inf},
        {'max_observation_gap': -1.0},
    ],
)
def test_invalid_filter_configuration_is_rejected(kwargs):
    with pytest.raises(ValueError):
        EmotionFilter(**kwargs)
