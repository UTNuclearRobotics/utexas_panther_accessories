from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def launch_setup(context, *args, **kwargs):
    # Camera
    depthai_camera = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [PathJoinSubstitution([FindPackageShare("utexas_panther"), "launch", "camera.launch.py"])]
        ),
        launch_arguments={
            "camera_i_restart_on_diagnostics_error": "true"
        }.items(),
    )

    # Ouster LiDAR
    ouster_lidar = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [PathJoinSubstitution([FindPackageShare("utexas_panther"), "launch", "lidar.launch.py"])]
        ),
        launch_arguments={
            "sensor_hostname": "192.168.1.100",
            "viz": "false",
        }.items(),
    )

    # SLAM Toolbox configuration
    slam_params_file = LaunchConfiguration('slam_params_file')
    slam_mode = LaunchConfiguration('slam_mode')

    slam_toolbox = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[
            slam_params_file,
            {
                'mode': slam_mode,           # controlled by launch argument
                # You can add more overrides here if desired
                # 'use_sim_time': False,
                # 'odom_frame': 'odom',
                # 'map_frame': 'map',
                # 'base_frame': 'base_link',
            }
        ],
    )

    return [
        depthai_camera,
        ouster_lidar,
        slam_toolbox,
    ]


def generate_launch_description():
    return LaunchDescription([
        # ── Launch arguments ───────────────────────────────────────────────
        DeclareLaunchArgument(
            'slam_params_file',
            default_value=PathJoinSubstitution([
                FindPackageShare('utexas_panther'),
                'config',
                'slam_params.yaml'
            ]),
            description='Full path to the SLAM Toolbox parameters file to use'
        ),

        DeclareLaunchArgument(
            'slam_mode',
            default_value='mapping',
            description="SLAM mode: 'mapping' or 'localization'"
        ),

        # ── The actual nodes ───────────────────────────────────────────────
        OpaqueFunction(function=launch_setup),
    ])