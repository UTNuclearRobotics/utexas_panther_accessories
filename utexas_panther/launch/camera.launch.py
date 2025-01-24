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
        PythonLaunchDescriptionSource(
            [PathJoinSubstitution([FindPackageShare("depthai_ros_driver"), "launch", "camera.launch.py"])]
        ),
        launch_arguments={"camera_i_restart_on_diagnostics_error": "true"}.items(),
    )

    # ros2 run tf2_ros static_transform_publisher 0.2286 0.0 0.5715 0.0 0.0 0.0 /panther/base_link /oak-d-base-frame
    static_transform_publisher = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="static_transform_publisher",
        arguments=[
            "0.2886",
            "0.0",
            "0.5715",
            "0.0",
            "0.0",
            "0.0",
            "/panther/base_link",
            "/oak-d-base-frame",
        ],
    )

    return [
        depthai_camera,
    ]


def generate_launch_description():
    declared_arguments = []
    return LaunchDescription(declared_arguments + [OpaqueFunction(function=launch_setup)])
