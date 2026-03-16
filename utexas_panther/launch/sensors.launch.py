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
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node
from nav2_common.launch import ReplaceString, RewrittenYaml
from launch_ros.descriptions import ParameterFile


def launch_setup(context, *args, **kwargs):
    import os

    namespace         = LaunchConfiguration("namespace").perform(context)
    observation_topic = LaunchConfiguration("observation_topic").perform(context)

    observation_topic_filtered = observation_topic + "_filtered"
    scan_topic_abs             = "/" + namespace + "/scan" if namespace else "/scan"
    target_frame               = namespace + "/base_link" if namespace else "base_link"

    utexas_panther = FindPackageShare("utexas_panther").find("utexas_panther")
    pc2ls_params_raw = os.path.join(utexas_panther, "config", "pc2ls_params.yaml")

    # --------------------------------------------------------------------------
    # pc2ls_params.yaml — substitute <namespace> token at launch time.
    # --------------------------------------------------------------------------
    pc2ls_params_file = ReplaceString(
        source_file=pc2ls_params_raw,
        replacements={"<namespace>": namespace},
    )

    configured_pc2ls_params = ParameterFile(
        RewrittenYaml(
            source_file=pc2ls_params_file,
            root_key="",
            param_rewrites={"use_sim_time": "false"},
            convert_types=True,
        ),
        allow_substs=True,
    )

    # --------------------------------------------------------------------------
    # Sensors
    # --------------------------------------------------------------------------
    depthai_camera = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [PathJoinSubstitution([FindPackageShare("utexas_panther"), "launch", "camera.launch.py"])]
        ),
        launch_arguments={"camera_i_restart_on_diagnostics_error": "true"}.items(),
    )

    ouster_lidar = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [PathJoinSubstitution([FindPackageShare("utexas_panther"), "launch", "lidar.launch.py"])]
        ),
        launch_arguments={
            "sensor_hostname": "192.168.1.100",
            "viz": "false",
        }.items(),
    )

    # --------------------------------------------------------------------------
    # pointcloud_crop_box — global scope, no namespace.
    # Removes robot body returns from the raw Ouster cloud before any
    # downstream consumer (pc2ls, costmap) sees the data.
    # --------------------------------------------------------------------------
    pointcloud_crop_box = Node(
        package="pointcloud_crop_box",
        executable="pointcloud_crop_box_node",
        name="pointcloud_crop_box",
        parameters=[
            {
                "input_topic":  observation_topic,
                "output_topic": observation_topic_filtered,
                "target_frame": target_frame,
                "negative":     True,
                "min_x": -0.55,
                "max_x":  0.55,
                "min_y": -0.55,
                "max_y":  0.55,
                "min_z": -0.10,
                "max_z":  0.60,
                "visualize_bounding_box": False,
                "use_sim_time": False,
            }
        ],
        remappings=[
            ("/tf",        "/tf"),
            ("/tf_static", "/tf_static"),
        ],
        output="screen",
    )

    # --------------------------------------------------------------------------
    # pointcloud_to_laserscan — converts filtered cloud to LaserScan for
    # slam_toolbox and AMCL.
    # cloud_in → <observation_topic_filtered>  (e.g. /ouster/points_filtered)
    # scan     → /<namespace>/scan             (e.g. /panther/scan)
    # --------------------------------------------------------------------------
    pointcloud_to_laserscan = Node(
        package="pointcloud_to_laserscan",
        executable="pointcloud_to_laserscan_node",
        name="pointcloud_to_laserscan",
        parameters=[configured_pc2ls_params],
        remappings=[
            ("cloud_in", observation_topic_filtered),
            ("scan",     scan_topic_abs),
        ],
        output="screen",
    )

    # --------------------------------------------------------------------------
    # Relay / utility nodes
    # --------------------------------------------------------------------------
    goal_relay = Node(
        package="topic_tools",
        executable="relay",
        name="goal_topic_relay",
        output="screen",
        arguments=[
            "/goal_pose",
            "/" + namespace + "/goal_pose" if namespace else "/goal_pose",
        ],
        parameters=[{"use_sim_time": False}],
    )

    initial_pose_relay = Node(
        package="topic_tools",
        executable="relay",
        name="initial_pose_relay",
        output="screen",
        arguments=[
            "/initialpose",
            "/" + namespace + "/initialpose" if namespace else "/initialpose",
        ],
        parameters=[{"use_sim_time": False}],
    )

    twist_stamper = Node(
        package="twist_stamper",
        executable="twist_stamper",
        name="twist_stamper",
        output="screen",
        remappings=[
            ("cmd_vel_in",  "/" + namespace + "/controller/cmd_vel" if namespace else "/controller/cmd_vel"),
            ("cmd_vel_out", "/cmd_vel_out"),
        ],
        parameters=[{
            "frame_id":     target_frame,
            "use_sim_time": False,
        }],
    )

    return [
        depthai_camera,
        ouster_lidar,
        pointcloud_crop_box,
        pointcloud_to_laserscan,
        goal_relay,
        initial_pose_relay,
        twist_stamper,
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            "namespace",
            default_value="panther",
            description="Robot namespace — must match bringup.launch.py namespace arg.",
        ),
        DeclareLaunchArgument(
            "observation_topic",
            default_value="/ouster/points",
            description="Raw PointCloud2 topic from the lidar driver.",
        ),
        OpaqueFunction(function=launch_setup),
    ])