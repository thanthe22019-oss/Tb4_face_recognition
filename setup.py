"""Setuptools entry point for the ROS 2 package."""

from glob import glob
import os

from setuptools import find_packages, setup


PACKAGE_NAME = 'tbe4_face_recognition'

setup(
    name=PACKAGE_NAME,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        (
            'share/ament_index/resource_index/packages',
            ['resource/' + PACKAGE_NAME],
        ),
        ('share/' + PACKAGE_NAME, ['package.xml']),
        (os.path.join('share', PACKAGE_NAME, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', PACKAGE_NAME, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    tests_require=['pytest'],
    zip_safe=True,
    maintainer='thanthe22019-oss',
    maintainer_email='232276355+thanthe22019-oss@users.noreply.github.com',
    description='Webcam facial emotion control for TurtleBot 4',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'emotion_recognition_node = '
            'tbe4_face_recognition.emotion_recognition_node:main',
            'emotion_controller_node = '
            'tbe4_face_recognition.emotion_controller_node:main',
        ],
    },
)
