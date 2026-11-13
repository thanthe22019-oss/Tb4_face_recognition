"""Tests for webcam-node helpers without opening a camera."""

import numpy as np

from tbe4_face_recognition.emotion_model import DetectedFace
from tbe4_face_recognition.emotion_recognition_node import (
    EmotionRecognitionNode,
    InferenceScheduler,
    draw_overlay,
    try_decode_status,
)
from tbe4_face_recognition.protocol import BehaviorStatus, Observation, encode_status


def test_overlay_is_a_clipped_copy_with_required_state_text():
    frame = np.zeros((60, 80, 3), dtype=np.uint8)
    faces = [DetectedFace((-10, -5, 40, 30), 'happy', 0.91)]
    observation = Observation('session', 4, 'happy', 0.91, 1)
    status = BehaviorStatus(
        'EXECUTING', 'happy', 'arc_left', 'started', False, True, 0.4
    )

    overlay = draw_overlay(frame, faces, observation, status)

    assert overlay.shape == frame.shape
    assert overlay.dtype == frame.dtype
    assert overlay is not frame
    assert np.count_nonzero(frame) == 0
    assert np.count_nonzero(overlay) > 0


def test_overlay_tolerates_no_status_and_no_faces():
    frame = np.zeros((40, 60, 3), dtype=np.uint8)
    observation = Observation('session', 0, 'unknown', 0.0, 0)

    overlay = draw_overlay(frame, [], observation, None)

    assert overlay.shape == frame.shape
    assert np.count_nonzero(overlay) > 0


def test_malformed_status_is_ignored_but_valid_status_round_trips():
    assert try_decode_status('not-json') is None
    assert try_decode_status('{}') is None
    value = BehaviorStatus('ARMED', 'neutral', None, 'rearmed', True, False, 0.0)
    assert try_decode_status(encode_status(value)) == value


def test_inference_sequence_advances_only_after_completed_periodic_inference():
    scheduler = InferenceScheduler(0.2, session_id='abc12345')
    face = DetectedFace((0, 0, 10, 10), 'happy', 0.9)

    assert scheduler.should_infer(0.0) is True
    assert scheduler.should_infer(0.05) is False
    first = scheduler.complete([face], 0.08)
    assert first.sequence == 0
    assert scheduler.should_infer(0.19) is False
    assert scheduler.should_infer(0.28) is True
    second = scheduler.complete([face], 0.32)

    assert second.sequence == 1
    assert second.session_id == 'abc12345'


def test_scheduler_rejects_invalid_time_and_double_completion():
    scheduler = InferenceScheduler(0.2, session_id='abc12345')

    try:
        scheduler.complete([], 0.0)
    except RuntimeError as error:
        assert str(error) == 'no inference is pending'
    else:
        raise AssertionError('completion without scheduling must fail')

    assert scheduler.should_infer(0.0) is True
    scheduler.complete([], 0.1)
    try:
        scheduler.complete([], 0.2)
    except RuntimeError as error:
        assert str(error) == 'no inference is pending'
    else:
        raise AssertionError('double completion must fail')


def test_cleanup_does_not_destroy_a_window_that_was_never_created(monkeypatch):
    class Camera:
        released = False

        def release(self):
            self.released = True

    camera = Camera()
    node = EmotionRecognitionNode.__new__(EmotionRecognitionNode)
    node.closed = False
    node.camera = camera
    node.show_window = True
    node.window_created = False
    node.window_name = 'unused'
    monkeypatch.setattr(
        'tbe4_face_recognition.emotion_recognition_node.cv2.destroyWindow',
        lambda name: (_ for _ in ()).throw(AssertionError(name)),
    )

    node.close()

    assert camera.released is True
    assert node.closed is True
