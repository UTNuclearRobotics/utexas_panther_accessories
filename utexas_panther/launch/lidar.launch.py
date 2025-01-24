from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    OpaqueFunction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    PathJoinSubstitution,
)
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node


def launch_setup(context, *args, **kwargs):
    # ros2 launch ouster_ros sensor.launch.xml sensor_hostname:=192.168.1.100 viz:=false
    lidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [PathJoinSubstitution([FindPackageShare("ouster_ros"), "launch", "sensor.launch.xml"])]
        ),
        launch_arguments={
            "sensor_hostname": "192.168.1.100",
            "viz": "false",
        }.items(),
    )

    # ros2 run tf2_ros static_transform_publisher 0.0 0.0 0.589 0.0 0.0 0.0 /panther/base_link /os_sensor
    static_transform_publisher = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="static_transform_publisher",
        arguments=["0.0", "0.0", "0.589", "0.0", "0.0", "0.0", "/panther/base_link", "/os_sensor"],
    )

    return [
        lidar_launch,
        static_transform_publisher,
    ]


def generate_launch_description():
    declared_arguments = []
    return LaunchDescription(declared_arguments + [OpaqueFunction(function=launch_setup)])
