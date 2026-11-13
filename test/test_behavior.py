"""Tests for one-shot emotion-to-action behavior."""

import pytest

from tbe4_face_recognition.behavior import BehaviorController
from tbe4_face_recognition.emotion_filter import FilterResult


def result(emotion=None, *, changed=True, stop_reason=None):
    return FilterResult(
        normalized=emotion or 'unknown',
        stable_emotion=emotion,
        changed=changed,
        stop_reason=stop_reason,
    )


def arm(controller, now=0.0):
    decision = controller.receive(result('neutral'), now, odometry_ready=True)
    assert decision.start_action is None
    assert controller.state == 'ARMED'


@pytest.mark.parametrize(
    ('emotion', 'action'),
    [
        ('happy', 'arc_left'),
        ('sad', 'arc_right'),
        ('angry', 'reverse'),
        ('surprise', 'rotate_full'),
        ('fear', 'forward'),
    ],
)
def test_stable_emotions_map_to_exactly_one_action(emotion, action):
    controller = BehaviorController(preview_only=False)
    arm(controller)

    decision = controller.receive(result(emotion), 1.0, odometry_ready=True)

    assert decision.start_action == action
    assert decision.cancel_motion is False
    assert controller.state == 'EXECUTING'
    assert controller.receive(
        result(emotion, changed=False), 1.1, odometry_ready=True
    ).start_action is None


def test_neutral_stops_motion_and_rearms():
    controller = BehaviorController(preview_only=False)
    arm(controller)
    controller.receive(result('happy'), 1.0, odometry_ready=True)

    decision = controller.receive(result('neutral'), 1.1, odometry_ready=True)

    assert decision.cancel_motion is True
    assert decision.start_action is None
    assert controller.state == 'ARMED'
    assert controller.reason == 'rearmed'


def test_different_expression_during_execution_cancels_without_queueing():
    controller = BehaviorController(preview_only=False)
    arm(controller)
    controller.receive(result('happy'), 1.0, odometry_ready=True)

    decision = controller.receive(result('sad'), 1.1, odometry_ready=True)

    assert decision.start_action is None
    assert decision.cancel_motion is True
    assert controller.state == 'DISARMED'
    assert controller.active_action is None
    assert controller.reason == 'emotion_changed'


def test_completion_requires_rearm_before_same_emotion_runs_again():
    controller = BehaviorController(preview_only=False)
    arm(controller)
    controller.receive(result('fear'), 1.0, odometry_ready=True)
    controller.complete(1.2)

    assert controller.receive(
        result('fear'), 1.3, odometry_ready=True
    ).start_action is None
    arm(controller, 2.0)
    assert controller.receive(
        result('fear'), 3.0, odometry_ready=True
    ).start_action == 'forward'


def test_unsafe_result_cancels_active_motion():
    controller = BehaviorController(preview_only=False)
    arm(controller)
    controller.receive(result('angry'), 1.0, odometry_ready=True)

    decision = controller.receive(
        result(None, stop_reason='observation_timeout'),
        1.1,
        odometry_ready=True,
    )

    assert decision.cancel_motion is True
    assert controller.state == 'DISARMED'
    assert controller.reason == 'observation_timeout'


def test_stable_no_face_can_rearm_after_motion_is_stopped():
    controller = BehaviorController(preview_only=False)
    arm(controller)
    controller.receive(result('happy'), 1.0, odometry_ready=True)

    decision = controller.receive(
        result('unknown', stop_reason='no_face'), 2.0, odometry_ready=True
    )

    assert decision.cancel_motion is True
    assert controller.state == 'ARMED'
    assert controller.reason == 'rearmed'


def test_preview_consumes_trigger_and_reports_preview_completed():
    controller = BehaviorController(preview_only=True)
    arm(controller)

    decision = controller.receive(result('surprise'), 1.0, odometry_ready=False)

    assert decision.start_action is None
    assert decision.cancel_motion is False
    assert controller.state == 'DISARMED'
    assert controller.reason == 'preview_completed'


def test_missing_odometry_consumes_trigger_without_delayed_start():
    controller = BehaviorController(preview_only=False)
    arm(controller)

    blocked = controller.receive(result('fear'), 1.0, odometry_ready=False)
    assert blocked.start_action is None
    assert controller.reason == 'odometry_unavailable'
    assert controller.state == 'DISARMED'
    assert controller.receive(
        result('fear', changed=False), 1.1, odometry_ready=True
    ).start_action is None

    arm(controller, 2.0)
    assert controller.receive(
        result('fear'), 3.0, odometry_ready=True
    ).start_action == 'forward'


def test_new_session_stops_and_requires_rearm():
    controller = BehaviorController(preview_only=False)
    arm(controller)
    controller.receive(result('happy'), 1.0, odometry_ready=True)

    restart = controller.receive(
        result(None, stop_reason='recognition_restarted'),
        1.1,
        odometry_ready=True,
    )

    assert restart.cancel_motion is True
    assert controller.state == 'DISARMED'
    assert controller.receive(
        result('sad'), 1.7, odometry_ready=True
    ).start_action is None
    arm(controller, 2.0)
    assert controller.receive(
        result('sad'), 3.0, odometry_ready=True
    ).start_action == 'arc_right'


def test_snapshot_reports_public_behavior_state():
    controller = BehaviorController(preview_only=False)
    arm(controller)
    controller.receive(result('happy'), 1.0, odometry_ready=True)

    snapshot = controller.snapshot(odometry_ready=True, motion_progress=0.4)

    assert snapshot.state == 'EXECUTING'
    assert snapshot.stable_emotion == 'happy'
    assert snapshot.active_action == 'arc_left'
    assert snapshot.motion_progress == 0.4
