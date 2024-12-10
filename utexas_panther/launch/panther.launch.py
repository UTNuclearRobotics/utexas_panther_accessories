import yaml
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
)
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    LaunchConfiguration,
    PathJoinSubstitution,
    PythonExpression,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def launch_setup(context, *args, **kwargs):
    # ros2 launch depthai_ros_driver camera.launch.py
    depthai_camera = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('depthai_ros_driver'),
                'launch',
                'camera.launch.py'
            ])
        ]),
        launch_arguments={
            'frame_rate': '30.0'
        }.items()
        ,
    )

    return [
        depthai_camera,
    ]


def generate_launch_description():
    declared_arguments = []

    # declared_arguments.append(
    #     DeclareLaunchArgument(
    #         'robot_configs',
    #         default_value=PathJoinSubstitution([
    #             FindPackageShare('turret_aim_control'),
    #             'config',
    #             'default',
    #             'turret.yaml',
    #         ]),
    #         description="the file path to the 'turret config' YAML file.",
    #     )
    # )

    return LaunchDescription(declared_arguments + [OpaqueFunction(function=launch_setup)])