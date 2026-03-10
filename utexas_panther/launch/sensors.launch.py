from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    OpaqueFunction,
    RegisterEventHandler
)
from launch.event_handlers import OnProcessStart
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    PathJoinSubstitution,
    Command,
    TextSubstitution,
)
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node


def launch_setup(context, *args, **kwargs):
    # ros2 launch depthai_ros_driver camera.launch.py
    depthai_camera = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [PathJoinSubstitution([FindPackageShare("utexas_panther"), "launch", "camera.launch.py"])]
        ),
        launch_arguments={"camera_i_restart_on_diagnostics_error": "true"}.items(),
    )
    # ros2 launch ouster_ros sensor.launch.xml sensor_hostname:=192.168.1.100 viz:=false
    ouster_lidar = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [PathJoinSubstitution([FindPackageShare("utexas_panther"), "launch", "lidar.launch.py"])]
        ),
        launch_arguments={
            "sensor_hostname": "192.168.1.100",
            "viz": "false",
        }.items(),
    )

    # Relay node: copies /panther/hardware/estop → /hardware/estop
    goal_relay = Node(
        package='topic_tools',
        executable='relay',
        name='goal_topic_relay',
        output='screen',
        arguments=[
            '/goal_pose',
            '/panther/goal_pose'
        ],
        parameters=[{'use_sim_time': False}],
    )

    domain_bridge = Node(
        package='domain_bridge',
        executable='domain_bridge',
        name='domain_bridge',
        output='screen',
        arguments=[
            PathJoinSubstitution([
                FindPackageShare("utexas_panther"), "config", "domain_bridge.yaml"
            ])
        ],
    )

    # cmd_relay = Node(
    #     package='topic_tools',
    #     executable='relay',
    #     name='cmd_vel_nav_topic_relay',
    #     output='screen',
    #     arguments=[
    #         '/cmd_vel_nav',
    #         '/panther/controller/cmd_vel'
    #     ],
    #     parameters=[{'use_sim_time': False}],
    # )

    return [
        depthai_camera,
        ouster_lidar,
        goal_relay,
        domain_bridge,
        # cmd_relay,
    ]


def generate_launch_description():
    declared_arguments = []
    return LaunchDescription(declared_arguments + [OpaqueFunction(function=launch_setup)])