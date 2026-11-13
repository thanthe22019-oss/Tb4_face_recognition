"""Tests for the ROS adapter boundary and safety control core."""

import math

import pytest
from nav_msgs.msg import Odometry

from tbe4_face_recognition.emotion_controller_node import (
    ControlCore,
    pose_from_odometry,
    publish_velocity,
)
from tbe4_face_recognition.motion import Pose
from tbe4_face_recognition.protocol import Observation


class PublisherSpy:
    def __init__(self):
        self.messages = []

    def publish(self, message):
        self.messages.append(message)


def odometry(x=0.0, y=0.0, z=0.0, w=1.0, stamp=1.0):
    message = Odometry()
    message.pose.pose.position.x = x
    message.pose.pose.position.y = y
    message.pose.pose.orientation.z = z
    message.pose.pose.orientation.w = w
    message.header.stamp.sec = int(stamp)
    message.header.stamp.nanosec = int((stamp - int(stamp)) * 1e9)
    return message


def observation(sequence, emotion, confidence=0.9):
    return Observation('session-a', sequence, emotion, confidence, 1)


def start_happy_motion(core):
    core.update_odometry(Pose(0.0, 0.0, 0.0), stamp=1.0, now=0.0)
    core.receive_observation(observation(0, 'neutral'), 0.0)
    core.receive_observation(observation(1, 'neutral'), 0.75)
    core.receive_observation(observation(2, 'happy'), 0.80)
    core.update_odometry(Pose(0.0, 0.0, 0.0), stamp=2.0, now=1.29)
    core.receive_observation(observation(3, 'happy'), 1.30)
    assert core.behavior.state == 'EXECUTING'


def test_pose_from_odometry_normalizes_quaternion_and_extracts_stamp():
    message = odometry(x=1.25, y=-2.5, z=math.sqrt(2), w=math.sqrt(2), stamp=12.34)

    pose, stamp = pose_from_odometry(message)

    assert pose.x == pytest.approx(1.25)
    assert pose.y == pytest.approx(-2.5)
    assert pose.yaw == pytest.approx(math.pi / 2.0)
    assert stamp == pytest.approx(12.34, abs=1e-8)


@pytest.mark.parametrize(
    ('z', 'w'),
    [(0.0, 0.0), (math.nan, 1.0), (0.0, math.inf)],
)
def test_pose_from_odometry_rejects_invalid_quaternion(z, w):
    with pytest.raises(ValueError):
        pose_from_odometry(odometry(z=z, w=w))


def test_stale_observation_stops_execution():
    core = ControlCore(preview_only=False)
    start_happy_motion(core)

    moving = core.compute_control(1.31)
    stopped = core.compute_control(2.06)
    publisher = PublisherSpy()
    message = publish_velocity(publisher, stopped)

    assert moving.linear_x > 0.0
    assert (stopped.linear_x, stopped.angular_z) == (0.0, 0.0)
    assert (message.linear.x, message.angular.z) == (0.0, 0.0)
    assert publisher.messages == [message]
    assert core.behavior.reason == 'observation_timeout'


def test_odometry_jump_cancels_motion_and_returns_zero():
    core = ControlCore(preview_only=False)
    start_happy_motion(core)

    reason = core.update_odometry(Pose(0.6, 0.0, 0.0), stamp=3.0, now=1.31)
    velocity = core.compute_control(1.32)

    assert reason == 'odom_jump'
    assert (velocity.linear_x, velocity.angular_z) == (0.0, 0.0)
    assert core.behavior.reason == 'odom_jump'


def test_cleanup_cancels_motion_and_publishes_zero():
    core = ControlCore(preview_only=False)
    start_happy_motion(core)
    publisher = PublisherSpy()

    stopped = core.stop('shutdown')
    message = publish_velocity(publisher, stopped)

    assert core.behavior.state == 'DISARMED'
    assert core.behavior.reason == 'shutdown'
    assert (message.linear.x, message.angular.z) == (0.0, 0.0)
