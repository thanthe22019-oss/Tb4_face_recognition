"""Behavioral tests for the ROS string JSON protocol."""

import json
import math

import pytest

from tbe4_face_recognition.protocol import (
    BehaviorStatus,
    Observation,
    decode_observation,
    decode_status,
    encode_observation,
    encode_status,
)


def test_observation_round_trip_is_compact_and_complete():
    value = Observation('session-a', 42, 'happy', 0.91, 1)

    payload = encode_observation(value)

    assert ' ' not in payload
    assert json.loads(payload) == {
        'confidence': 0.91,
        'emotion': 'happy',
        'face_count': 1,
        'sequence': 42,
        'session_id': 'session-a',
    }
    assert decode_observation(payload) == value


@pytest.mark.parametrize(
    'payload',
    [
        'not-json',
        '{}',
        '{"session_id":"s","sequence":0,"emotion":"happy",'
        '"confidence":0.9,"face_count":1,"extra":true}',
        '{"session_id":"","sequence":0,"emotion":"happy",'
        '"confidence":0.9,"face_count":1}',
        '{"session_id":"s","sequence":-1,"emotion":"happy",'
        '"confidence":0.9,"face_count":1}',
        '{"session_id":"s","sequence":true,"emotion":"happy",'
        '"confidence":0.9,"face_count":1}',
        '{"session_id":"s","sequence":0,"emotion":"joy",'
        '"confidence":0.9,"face_count":1}',
        '{"session_id":"s","sequence":0,"emotion":"happy",'
        '"confidence":1.1,"face_count":1}',
        '{"session_id":"s","sequence":0,"emotion":"happy",'
        '"confidence":NaN,"face_count":1}',
        '{"session_id":"s","sequence":0,"emotion":"happy",'
        '"confidence":true,"face_count":1}',
        '{"session_id":"s","sequence":0,"emotion":"happy",'
        '"confidence":0.9,"face_count":-1}',
        '{"session_id":"s","sequence":0,"emotion":"happy",'
        '"confidence":0.9,"face_count":true}',
    ],
)
def test_invalid_observation_payloads_are_rejected(payload):
    with pytest.raises((TypeError, ValueError, json.JSONDecodeError)):
        decode_observation(payload)


def test_observation_constructor_rejects_nonfinite_confidence():
    with pytest.raises(ValueError):
        Observation('session-a', 0, 'neutral', math.inf, 1)


def test_behavior_status_round_trip_preserves_nullable_fields():
    value = BehaviorStatus(
        state='EXECUTING',
        stable_emotion='surprise',
        active_action='rotate_full',
        reason='started',
        preview_only=False,
        odometry_ready=True,
        motion_progress=0.25,
    )

    assert decode_status(encode_status(value)) == value


@pytest.mark.parametrize('progress', [-0.01, 1.01, math.nan, math.inf, True])
def test_behavior_status_rejects_invalid_progress(progress):
    with pytest.raises((TypeError, ValueError)):
        BehaviorStatus(
            state='ARMED',
            stable_emotion=None,
            active_action=None,
            reason='ready',
            preview_only=True,
            odometry_ready=False,
            motion_progress=progress,
        )


def test_status_decoder_rejects_unknown_fields():
    payload = encode_status(
        BehaviorStatus('DISARMED', None, None, 'startup', True, False, 0.0)
    )
    document = json.loads(payload)
    document['unexpected'] = 1

    with pytest.raises(ValueError):
        decode_status(json.dumps(document))
