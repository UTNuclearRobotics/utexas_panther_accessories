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
    PythonExpression,
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

    initial_pose_relay = Node(
        package='topic_tools',
        executable='relay',
        name='initial_pose_relay',
        output='screen',
        arguments=[
            '/initialpose',
            '/panther/initialpose'
        ],
        parameters=[{'use_sim_time': False}],
    )

    twist_stamper = Node(
        package='twist_stamper',
        executable='twist_stamper',
        name='twist_stamper',
        output='screen',
        remappings=[
            ('cmd_vel_in', '/panther/cmd_vel'),
            ('cmd_vel_out', '/cmd_vel_out'),
        ],
        parameters=[{
            'frame_id': 'panther/base_link',
            'use_sim_time': False,
        }],
    )

    estop_relay = Node(
        package='topic_tools',
        executable='relay',
        name='estop_relay',
        output='screen',
        arguments=[
            '/panther/hardware/e_stop',
            '/hardware/e_stop'
        ],
        parameters=[{'use_sim_time': False}],
    )

    # pointcloud_crop_box_node = Node(
    #     package="pointcloud_crop_box",
    #     executable="pointcloud_crop_box_node",
    #     name="pointcloud_crop_box",
    #     # No namespace — intentionally global scope.
    #     parameters=[
    #         {
    #             "input_topic": "/ouster/points",
    #             "output_topic": "/ouster/points_filtered",
    #             "target_frame": "panther/base_link",
    #             "negative": True,
    #             "min_x": -0.55,
    #             "max_x":  0.55,
    #             "min_y": -0.55,
    #             "max_y":  0.55,
    #             "min_z": -0.10,
    #             "max_z":  0.60,
    #             "visualize_bounding_box": False,
    #             "use_sim_time": False,
    #         }
    #     ],
    #     remappings=[
    #         ("/tf", "/tf"),
    #         ("/tf_static", "/tf_static"),
    #     ],
    #     output="screen",
    # )

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
        twist_stamper,
        initial_pose_relay,
        estop_relay,
        # pointcloud_crop_box_node,
        # cmd_relay,
    ]


def generate_launch_description():
    declared_arguments = []
    return LaunchDescription(declared_arguments + [OpaqueFunction(function=launch_setup)])