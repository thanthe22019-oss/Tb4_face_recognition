"""Start webcam recognition with an explicit Python interpreter."""

from pathlib import Path
import sys

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    """Build the recognition-only launch description."""
    share = Path(get_package_share_directory('tbe4_face_recognition'))
    return LaunchDescription([
        DeclareLaunchArgument('python_executable', default_value=sys.executable),
        DeclareLaunchArgument('camera_index', default_value='0'),
        DeclareLaunchArgument(
            'show_window', default_value='true', choices=['true', 'false']
        ),
        Node(
            package='tbe4_face_recognition',
            executable='emotion_recognition_node',
            name='emotion_recognition_node',
            output='screen',
            prefix=[LaunchConfiguration('python_executable')],
            parameters=[
                str(share / 'config' / 'recognition.yaml'),
                {
                    'camera_index': ParameterValue(
                        LaunchConfiguration('camera_index'), value_type=int
                    ),
                    'show_window': ParameterValue(
                        LaunchConfiguration('show_window'), value_type=bool
                    ),
                },
            ],
        ),
    ])

