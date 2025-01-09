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


def launch_setup(context, *args, **kwargs):
    # ros2 launch ouster_ros sensor.launch.xml sensor_hostname:=192.168.1.100 viz:=false
    depthai_camera = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [PathJoinSubstitution([FindPackageShare("ouster_ros"), "launch", "sensor.launch.xml"])]
        ),
        launch_arguments={
            "sensor_hostname": "192.168.1.100",
            "viz": "false",
        }.items(),
    )

    return [
        depthai_camera,
    ]


def generate_launch_description():
    declared_arguments = []
    return LaunchDescription(declared_arguments + [OpaqueFunction(function=launch_setup)])
