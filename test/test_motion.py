"""Deterministic kinematic tests for bounded TurtleBot motion."""

import math

import pytest

from tbe4_face_recognition.motion import (
    MotionConfig,
    MotionExecutor,
    OdometryGuard,
    Pose,
    wrap,
)


DT = 0.02


def simulate(action, start=None):
    pose = start or Pose(0.0, 0.0, 0.0)
    executor = MotionExecutor(action, pose, 0.0)
    velocities = []
    progresses = []
    for index in range(4000):
        now = index * DT
        velocity = executor.step(pose, now)
        velocities.append((velocity.linear_x, velocity.angular_z))
        progresses.append(velocity.progress)
        pose = Pose(
            pose.x + velocity.linear_x * math.cos(pose.yaw) * DT,
            pose.y + velocity.linear_x * math.sin(pose.yaw) * DT,
            wrap(pose.yaw + velocity.angular_z * DT),
        )
        if velocity.done:
            return pose, executor, velocities, progresses
    raise AssertionError(f'{action} did not complete')


@pytest.mark.parametrize(
    ('action', 'yaw_sign', 'y_sign'),
    [('arc_left', 1.0, 1.0), ('arc_right', -1.0, -1.0)],
)
def test_arc_profiles_follow_point_four_meter_radius(action, yaw_sign, y_sign):
    pose, _, velocities, progresses = simulate(action)
    target = math.pi / 3.0

    assert wrap(pose.yaw) == pytest.approx(yaw_sign * target, abs=0.04)
    assert pose.x == pytest.approx(0.4 * math.sin(target), abs=0.025)
    assert pose.y == pytest.approx(y_sign * 0.4 * (1.0 - math.cos(target)), abs=0.025)
    assert max(abs(value[0]) for value in velocities) <= 0.10
    assert max(abs(value[1]) for value in velocities) <= 0.40
    assert all(0.0 <= value <= 1.0 for value in progresses)


@pytest.mark.parametrize(
    ('action', 'expected_x', 'speed'),
    [('forward', 0.20, 0.10), ('reverse', -0.20, 0.08)],
)
def test_line_profiles_travel_twenty_centimeters(action, expected_x, speed):
    pose, _, velocities, _ = simulate(action)

    assert pose.x == pytest.approx(expected_x, abs=0.012)
    assert abs(pose.y) < 0.005
    assert max(abs(value[0]) for value in velocities) <= speed


def test_full_rotation_completes_across_yaw_wrap():
    start = Pose(1.0, -2.0, 3.0)
    pose, executor, velocities, progresses = simulate('rotate_full', start)

    assert pose.x == pytest.approx(start.x)
    assert pose.y == pytest.approx(start.y)
    assert wrap(pose.yaw - start.yaw) == pytest.approx(0.0, abs=0.04)
    assert executor.turn_progress == pytest.approx(2.0 * math.pi, abs=0.04)
    assert max(abs(value[1]) for value in velocities) <= 0.40
    assert progresses[-1] == 1.0
    stopped = executor.step(pose, 100.0)
    assert (stopped.linear_x, stopped.angular_z, stopped.done) == (0.0, 0.0, True)


def test_stuck_motion_times_out():
    pose = Pose(0.0, 0.0, 0.0)
    executor = MotionExecutor('forward', pose, 0.0)

    with pytest.raises(RuntimeError, match='motion_timeout'):
        executor.step(pose, 30.01)


@pytest.mark.parametrize(
    'factory',
    [
        lambda: Pose(math.nan, 0.0, 0.0),
        lambda: MotionConfig(linear_speed=0.0),
        lambda: MotionConfig(angular_speed=0.61),
        lambda: MotionConfig(arc_radius=math.inf),
        lambda: MotionExecutor('unknown', Pose(0.0, 0.0, 0.0), 0.0),
    ],
)
def test_invalid_pose_configuration_or_action_is_rejected(factory):
    with pytest.raises((TypeError, ValueError)):
        factory()


def test_repeated_odometry_stamp_does_not_refresh_freshness():
    guard = OdometryGuard(timeout_seconds=0.5)
    pose = Pose(0.0, 0.0, 0.0)

    assert guard.update(pose, stamp=1.0, received_at=0.0) is None
    assert guard.update(pose, stamp=1.0, received_at=0.4) is None
    assert guard.ready(0.49) is True
    assert guard.ready(0.51) is False


def test_odometry_reset_and_large_jumps_are_reported():
    guard = OdometryGuard()
    guard.update(Pose(0.0, 0.0, 0.0), stamp=2.0, received_at=0.0)
    assert guard.update(
        Pose(0.0, 0.0, 0.0), stamp=1.0, received_at=0.1
    ) == 'odom_reset'
    assert guard.update(
        Pose(0.51, 0.0, 0.0), stamp=3.0, received_at=0.2
    ) == 'odom_jump'
    assert guard.update(
        Pose(0.51, 0.0, 1.01), stamp=4.0, received_at=0.3
    ) == 'odom_jump'


@pytest.mark.parametrize('bad', [math.nan, math.inf, -1.0])
def test_odometry_guard_rejects_invalid_times(bad):
    guard = OdometryGuard()
    with pytest.raises(ValueError):
        guard.update(Pose(0.0, 0.0, 0.0), stamp=bad, received_at=0.0)
