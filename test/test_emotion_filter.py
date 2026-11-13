"""Tests for temporal filtering and inference freshness."""

import math

import pytest

from tbe4_face_recognition.emotion_filter import EmotionFilter
from tbe4_face_recognition.protocol import Observation


def observation(
    sequence, emotion='happy', confidence=0.9, face_count=1, session='session-a'
):
    return Observation(session, sequence, emotion, confidence, face_count)


def test_confident_non_neutral_emotion_is_stable_immediately():
    filter_ = EmotionFilter()

    result = filter_.observe(observation(0, confidence=0.61), 0.0)

    assert result.stable_emotion == 'happy'
    assert result.changed is True
    assert filter_.observe(observation(1, confidence=0.61), 0.01).changed is False


def test_confident_label_change_is_stable_immediately():
    filter_ = EmotionFilter()
    filter_.observe(observation(0, 'happy', 0.61), 0.0)

    result = filter_.observe(observation(1, 'sad', 0.61), 0.01)

    assert result.stable_emotion == 'sad'
    assert result.changed is True


def test_confident_neutral_is_stable_immediately():
    filter_ = EmotionFilter()

    result = filter_.observe(observation(0, 'neutral', 0.61), 0.0)

    assert result.stable_emotion == 'neutral'
    assert result.changed is True


def test_unknown_still_needs_three_quarters_second_to_rearm():
    filter_ = EmotionFilter()

    filter_.observe(observation(0, 'unknown', 0.0, 0), 0.0)
    assert filter_.observe(
        observation(1, 'unknown', 0.0, 0),
        0.74,
    ).stable_emotion is None
    assert filter_.observe(
        observation(2, 'unknown', 0.0, 0),
        0.75,
    ).stable_emotion == 'unknown'


@pytest.mark.parametrize(
    ('value', 'reason'),
    [
        (observation(0, 'unknown', 0.0, 0), 'no_face'),
        (observation(0, 'unknown', 0.0, 2), 'multiple_faces'),
        (observation(0, 'happy', 0.60, 1), 'low_confidence'),
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


def test_new_session_stops_and_requires_new_observation():
    filter_ = EmotionFilter()
    assert filter_.observe(observation(0), 0.0).stable_emotion == 'happy'

    restarted = filter_.observe(observation(0, session='session-b'), 0.6)
    assert restarted.stop_reason == 'recognition_restarted'
    assert restarted.stable_emotion is None
    assert filter_.observe(
        observation(1, 'neutral', confidence=0.61, session='session-b'), 0.7
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
        {'stable_seconds': -0.1},
        {'rearm_seconds': math.inf},
        {'max_observation_gap': -1.0},
    ],
)
def test_invalid_filter_configuration_is_rejected(kwargs):
    with pytest.raises(ValueError):
        EmotionFilter(**kwargs)
