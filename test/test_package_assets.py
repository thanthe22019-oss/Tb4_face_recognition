"""Installation and launch-contract checks for the operator workflow."""

import importlib.util
import os
from pathlib import Path

os.environ.setdefault('ROS_LOG_DIR', '/tmp/tbe4_face_recognition_test_logs')

from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch_ros.actions import Node


ROOT = Path(__file__).resolve().parents[1]


def load_launch(name):
    path = ROOT / 'launch' / name
    spec = importlib.util.spec_from_file_location(name.replace('.', '_'), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if hasattr(module, 'get_package_share_directory'):
        module.get_package_share_directory = lambda package: str(ROOT)
    return module.generate_launch_description()


def declared_arguments(description):
    return {
        entity.name
        for entity in description.entities
        if isinstance(entity, DeclareLaunchArgument)
    }


def test_required_install_assets_exist_and_setup_collects_them():
    required = [
        'config/controller.yaml',
        'config/recognition.yaml',
        'launch/recognition.launch.py',
        'launch/interaction.launch.py',
        'launch/simulation.launch.py',
    ]
    assert all((ROOT / path).is_file() for path in required)

    setup_source = (ROOT / 'setup.py').read_text(encoding='utf-8')
    assert "glob('launch/*.launch.py')" in setup_source
    assert "glob('config/*.yaml')" in setup_source
    assert "tests_require=['pytest']" in setup_source


def test_operator_scripts_are_executable_and_never_invoke_sudo():
    for name in ['build.sh', 'run_recognition.sh', 'run_interaction.sh']:
        path = ROOT / 'scripts' / name
        assert path.is_file()
        assert os.access(path, os.X_OK)
        assert 'sudo' not in path.read_text(encoding='utf-8')


def test_interaction_launch_exposes_operator_arguments_and_one_controller():
    description = load_launch('interaction.launch.py')

    assert declared_arguments(description) >= {
        'python_executable', 'camera_index', 'show_window', 'preview_only'
    }
    controller_nodes = [
        entity for entity in description.entities
        if isinstance(entity, Node)
        and 'emotion_controller_node' in str(entity.node_executable)
    ]
    assert len(controller_nodes) == 1


def test_recognition_launch_prefixes_only_the_ai_node():
    description = load_launch('recognition.launch.py')
    nodes = [entity for entity in description.entities if isinstance(entity, Node)]

    assert declared_arguments(description) >= {
        'python_executable', 'camera_index', 'show_window'
    }
    assert len(nodes) == 1
    assert 'emotion_recognition_node' in str(nodes[0].node_executable)
    prefixes = nodes[0].process_description.prefix
    assert len(prefixes) == 1
    assert ''.join(part.text for part in prefixes[0].variable_name) == 'python_executable'


def test_simulation_launch_disables_navigation_stack():
    description = load_launch('simulation.launch.py')
    includes = [
        entity for entity in description.entities
        if isinstance(entity, IncludeLaunchDescription)
    ]

    assert len(includes) == 1
    arguments = dict(includes[0].launch_arguments)
    assert str(arguments['nav2']) == 'false'
    assert str(arguments['slam']) == 'false'
    assert str(arguments['localization']) == 'false'
