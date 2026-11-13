"""Start webcam recognition and the preview-safe TurtleBot controller."""

from pathlib import Path
import sys

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    """Build the two-node interaction launch description."""
    share = Path(get_package_share_directory('tbe4_face_recognition'))
    recognition = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            str(share / 'launch' / 'recognition.launch.py')
        ),
        launch_arguments={
            'python_executable': LaunchConfiguration('python_executable'),
            'camera_index': LaunchConfiguration('camera_index'),
            'show_window': LaunchConfiguration('show_window'),
        }.items(),
    )
    controller = Node(
        package='tbe4_face_recognition',
        executable='emotion_controller_node',
        name='emotion_controller_node',
        output='screen',
        parameters=[
            str(share / 'config' / 'controller.yaml'),
            {
                'preview_only': ParameterValue(
                    LaunchConfiguration('preview_only'), value_type=bool
                )
            },
        ],
    )
    return LaunchDescription([
        DeclareLaunchArgument('python_executable', default_value=sys.executable),
        DeclareLaunchArgument('camera_index', default_value='0'),
        DeclareLaunchArgument(
            'show_window', default_value='true', choices=['true', 'false']
        ),
        DeclareLaunchArgument(
            'preview_only', default_value='true', choices=['true', 'false']
        ),
        recognition,
        controller,
    ])
