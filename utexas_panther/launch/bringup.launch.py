# Copyright 2024 Husarion sp. z o.o.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    EmitEvent,
    ExecuteProcess,
    GroupAction,
    IncludeLaunchDescription,
    LogInfo,
    RegisterEventHandler,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.conditions import IfCondition, UnlessCondition
from launch.event_handlers import OnProcessExit, OnExecutionComplete
from launch.events import Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    EnvironmentVariable,
    LaunchConfiguration,
    PathJoinSubstitution,
    PythonExpression,
    TextSubstitution,
)
from launch_ros.actions import Node, PushRosNamespace
from launch_ros.descriptions import ParameterFile
from launch_ros.substitutions import FindPackageShare
from nav2_common.launch import ReplaceString, RewrittenYaml


def generate_launch_description():
    husarion_ugv_navigation = FindPackageShare("husarion_ugv_navigation")
    launch_dir = PathJoinSubstitution([husarion_ugv_navigation, "launch"])
    utexas_panther = FindPackageShare("utexas_panther")
    utexas_panther_launch_dir = PathJoinSubstitution([utexas_panther, "launch"])

    autostart = LaunchConfiguration("autostart")
    log_level = LaunchConfiguration("log_level")
    map = LaunchConfiguration("map")
    namespace = LaunchConfiguration("namespace")
    observation_topic = LaunchConfiguration("observation_topic")
    observation_topic_type = LaunchConfiguration("observation_topic_type")
    params_file = LaunchConfiguration("params_file")
    pc2ls_params_file = LaunchConfiguration("pc2ls_params_file")
    slam = LaunchConfiguration("slam")
    slam_delay = LaunchConfiguration("slam_delay")
    nav_delay = LaunchConfiguration("nav_delay")
    use_composition = LaunchConfiguration("use_composition")
    use_respawn = LaunchConfiguration("use_respawn")
    use_sim_time = LaunchConfiguration("use_sim_time")
    use_rviz = LaunchConfiguration("use_rviz")
    rviz_config_file = LaunchConfiguration("rviz_config_file")

    declare_autostart_arg = DeclareLaunchArgument(
        "autostart",
        default_value="true",
        description="Automatically startup the nav2 stack.",
    )
    declare_log_level_arg = DeclareLaunchArgument(
        "log_level",
        default_value="info",
        description="Logging level.",
        choices=["debug", "info", "warning", "error"],
    )
    declare_map_arg = DeclareLaunchArgument(
        "map", default_value="/map/map.yaml", description="Path to map yaml file to load."
    )
    declare_namespace_arg = DeclareLaunchArgument(
        "namespace",
        default_value=EnvironmentVariable("ROBOT_NAMESPACE", default_value=""),
        description="Add namespace to all launched nodes.",
    )
    declare_observation_topic_arg = DeclareLaunchArgument(
        "observation_topic",
        default_value="",
        description="Topic name for LaserScan or PointCloud2 observation messages type.",
    )
    declare_observation_topic_type_arg = DeclareLaunchArgument(
        "observation_topic_type",
        default_value="pointcloud",
        description="Observation topic type.",
        choices=["laserscan", "pointcloud"],
    )
    declare_params_file_arg = DeclareLaunchArgument(
        "params_file",
        default_value=PathJoinSubstitution([utexas_panther, "config", "nav2_params.yaml"]),
        description="Path to the parameters file to use for all nav2 related nodes",
    )
    declare_pc2ls_params_file_arg = DeclareLaunchArgument(
        "pc2ls_params_file",
        default_value=PathJoinSubstitution([utexas_panther, "config", "pc2ls_params.yaml"]),
        description="Path to the parameters file to use for pointcloud_to_laserscan node.",
    )
    declare_slam_arg = DeclareLaunchArgument(
        "slam", default_value="False", description="Whether run a SLAM."
    )
    # ---------------------------------------------------------------------------
    # NEW: Timing knobs exposed as launch args so you can tune from CLI without
    # editing this file.  Typical working values on real hardware:
    #   slam_delay  = 1.0 s  (after the outer 3 s gate — slam starts at t=4 s)
    #   nav_delay   = 12.0 s (after slam starts — navigation starts at t=16 s)
    #
    # Increase nav_delay if slam_toolbox is slow to publish /panther/map on your
    # machine; decrease it once you know your hardware is fast enough.
    # ---------------------------------------------------------------------------
    declare_slam_delay_arg = DeclareLaunchArgument(
        "slam_delay",
        default_value="1.0",
        description=(
            "Seconds to wait (after the outer 3 s gate) before starting slam_toolbox. "
            "Total slam start time = 3.0 + slam_delay."
        ),
    )
    declare_nav_delay_arg = DeclareLaunchArgument(
        "nav_delay",
        default_value="5.0",
        description=(
            "Seconds to wait after slam_toolbox starts before launching the Nav2 "
            "navigation stack (nav2_container + navigation_launch). "
            "Increase this if /panther/map is not yet published when costmap initialises."
        ),
    )
    declare_use_composition_arg = DeclareLaunchArgument(
        "use_composition",
        default_value="True",
        description="Whether to use composed bringup.",
    )
    declare_use_respawn_arg = DeclareLaunchArgument(
        "use_respawn",
        default_value="False",
        description="Whether to respawn if a node crashes. Applied when composition is disabled.",
    )
    declare_use_sim_time_arg = DeclareLaunchArgument(
        "use_sim_time",
        default_value="false",
        description="Use simulation (Gazebo) clock if true.",
    )
    declare_use_rviz_arg = DeclareLaunchArgument(
        "use_rviz",
        default_value="true",
        description="Whether to start RViz2.",
        choices=["true", "false"],
    )
    declare_rviz_config_file_cmd = DeclareLaunchArgument(
        "rviz_config_file",
        default_value=PathJoinSubstitution([utexas_panther, "config", "panther_sim.rviz"]),
        description="Full path to the RVIZ config file to use",
    )

    # --------------------------------------------------------------------------
    # Substitution helpers
    # --------------------------------------------------------------------------
    param_substitutions = {"use_sim_time": use_sim_time, "yaml_filename": map}

    namespace_or_default = PythonExpression(["'", namespace, "' if '", namespace, "' else 'robot'"])
    namespace_ext = PythonExpression(["'", namespace, "' + '/' if '", namespace, "' else ''"])

    scan_topic = PythonExpression(
        ["'scan' if '", observation_topic_type, "' == 'pointcloud' else '", observation_topic, "'"]
    )
    add_obstacle_layer = PythonExpression(
        ["'obstacle_layer,' if '", observation_topic_type, "' == 'laserscan' else ''"]
    )
    add_voxel_layer = PythonExpression(
        ["'voxel_layer,' if '", observation_topic_type, "' == 'pointcloud' else ''"]
    )

    namespace_scan_topic = PythonExpression(
        ["'/' + '", namespace, "' + '/scan' if '", namespace, "' else '/scan'"]
    )

    crop_box_target_frame = PythonExpression(
        ["'", namespace, "' + '/base_link' if '", namespace, "' else 'base_link'"]
    )

    observation_topic_filtered = PythonExpression(["'", observation_topic, "' + '_filtered'"])

    # --------------------------------------------------------------------------
    # nav2_params.yaml substitutions
    # --------------------------------------------------------------------------
    params_file = ReplaceString(
        source_file=params_file,
        replacements={
            "<namespace_key>": namespace_or_default,
            "<namespace>/": namespace_ext,
            "<observation_topic>": observation_topic_filtered,
            "<scan_topic>": scan_topic,
            "<obstacle_layer>,": add_obstacle_layer,
            "<voxel_layer>,": add_voxel_layer,
        },
    )

    configured_params = ParameterFile(
        RewrittenYaml(
            source_file=params_file,
            root_key="",
            param_rewrites=param_substitutions,
            convert_types=True,
        ),
        allow_substs=True,
    )

    # --------------------------------------------------------------------------
    # pc2ls_params.yaml substitutions
    # --------------------------------------------------------------------------
    pc2ls_params_file = ReplaceString(
        source_file=pc2ls_params_file,
        replacements={
            "<namespace>": namespace,
        },
    )

    configured_pc2ls_params = ParameterFile(
        RewrittenYaml(
            source_file=pc2ls_params_file,
            root_key="",
            param_rewrites={"use_sim_time": use_sim_time},
            convert_types=True,
        ),
        allow_substs=True,
    )

    # --------------------------------------------------------------------------
    # pointcloud_crop_box — global scope (no namespace), same as before.
    # --------------------------------------------------------------------------
    pointcloud_crop_box_node = Node(
        condition=IfCondition(
            PythonExpression(["'", observation_topic_type, "' == 'pointcloud'"])
        ),
        package="pointcloud_crop_box",
        executable="pointcloud_crop_box_node",
        name="pointcloud_crop_box",
        parameters=[
            {
                "input_topic": observation_topic,
                "output_topic": observation_topic_filtered,
                "target_frame": crop_box_target_frame,
                "negative": True,
                "min_x": -0.55,
                "max_x":  0.55,
                "min_y": -0.55,
                "max_y":  0.55,
                "min_z": -0.10,
                "max_z":  0.60,
                "visualize_bounding_box": False,
                "use_sim_time": use_sim_time,
            }
        ],
        remappings=[
            ("/tf", "/tf"),
            ("/tf_static", "/tf_static"),
        ],
        output="screen",
    )

    # --------------------------------------------------------------------------
    # SLAM group — starts at t = 3.0 + slam_delay.
    #
    # slam_toolbox (via slam_launch.py) and pc2ls start here.  The lifecycle
    # manager inside slam_launch.py will bring up slam_toolbox and it will begin
    # publishing /panther/map only after it has processed enough scans.
    # --------------------------------------------------------------------------
    slam_bringup_group = GroupAction(
        condition=IfCondition(slam),
        actions=[
            PushRosNamespace(namespace),

            # pointcloud_to_laserscan feeds slam_toolbox.
            Node(
                condition=IfCondition(
                    PythonExpression(["'", observation_topic_type, "' == 'pointcloud'"])
                ),
                package="pointcloud_to_laserscan",
                executable="pointcloud_to_laserscan_node",
                name="pointcloud_to_laserscan",
                parameters=[configured_pc2ls_params],
                remappings=[
                    ("cloud_in", observation_topic_filtered),
                    ("scan", namespace_scan_topic),
                ],
                output="screen",
            ),

            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution([launch_dir, "slam_launch.py"])
                ),
                launch_arguments={
                    "autostart": autostart,
                    "namespace": namespace,
                    "params_file": params_file,
                    "use_respawn": use_respawn,
                    "use_sim_time": use_sim_time,
                }.items(),
            ),

            Node(
                name="map_autosaver",
                package="husarion_ugv_navigation",
                executable="map_autosaver_node",
                parameters=[configured_params],
                arguments=["--ros-args", "--log-level", log_level],
                output="screen",
            ),
        ],
    )

    # --------------------------------------------------------------------------
    # Navigation group — starts at t = 3.0 + slam_delay + nav_delay.
    #
    # By this time slam_toolbox should have published at least one /panther/map
    # message, so the costmap's static layer won't stall waiting for the map.
    #
    # Also handles the localization path (AMCL) when slam=False: in that case
    # there is no race because /panther/map comes from map_server which loads
    # instantly, so nav_delay = 0 is fine and the delay is harmless.
    # --------------------------------------------------------------------------
    nav_bringup_group = GroupAction(
        actions=[
            PushRosNamespace(namespace),

            # pc2ls for the localization (non-SLAM) path.  When slam=True this
            # node is already running in slam_bringup_group above; launching it
            # a second time would cause a duplicate-node conflict.  The
            # UnlessCondition(slam) guard prevents that.
            Node(
                condition=IfCondition(
                    PythonExpression(
                        [
                            "'",
                            observation_topic_type,
                            "' == 'pointcloud' and not ",
                            slam,
                        ]
                    )
                ),
                package="pointcloud_to_laserscan",
                executable="pointcloud_to_laserscan_node",
                name="pointcloud_to_laserscan",
                parameters=[configured_pc2ls_params],
                remappings=[
                    ("cloud_in", observation_topic_filtered),
                    ("scan", namespace_scan_topic),
                ],
                output="screen",
            ),

            # Nav2 component container — must exist before localization/navigation
            # launch files try to load components into it.
            Node(
                condition=IfCondition(use_composition),
                name="nav2_container",
                package="rclcpp_components",
                executable="component_container_isolated",
                parameters=[configured_params, {"autostart": autostart}],
                arguments=["--ros-args", "--log-level", log_level],
                output="screen",
            ),

            # Localization (AMCL) — only when slam=False.
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution([launch_dir, "localization_launch.py"])
                ),
                condition=UnlessCondition(slam),
                launch_arguments={
                    "autostart": autostart,
                    "container_name": "nav2_container",
                    "map": map,
                    "namespace": namespace,
                    "params_file": params_file,
                    "use_composition": use_composition,
                    "use_respawn": use_respawn,
                    "use_sim_time": use_sim_time,
                }.items(),
            ),

            # Navigation stack (controller, planner, costmaps, BT navigator …).
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution([launch_dir, "navigation_launch.py"])
                ),
                launch_arguments={
                    "namespace": namespace,
                    "use_sim_time": use_sim_time,
                    "autostart": autostart,
                    "params_file": params_file,
                    "use_composition": use_composition,
                    "use_respawn": use_respawn,
                    "container_name": "nav2_container",
                }.items(),
            ),

            Node(
                condition=IfCondition(use_rviz),
                package="rviz2",
                executable="rviz2",
                name="rviz_mapping",
                arguments=["-d", PathJoinSubstitution([rviz_config_file])],
                parameters=[{"use_sim_time": use_sim_time}],
                output="screen",
            ),
        ]
    )

    # --------------------------------------------------------------------------
    # Outer gate: wait 3 s for hardware drivers / DDS to settle, then:
    #   t = 3.0              → crop_box starts
    #   t = 3.0 + slam_delay → slam_bringup_group starts (slam_toolbox + pc2ls)
    #   t = 3.0 + slam_delay + nav_delay → nav_bringup_group starts
    #
    # The inner TimerAction for nav is nested inside the slam TimerAction so
    # that nav_delay is measured from when slam actually fired, not from t=0.
    # --------------------------------------------------------------------------
    nav_timer = TimerAction(
        period=nav_delay,
        actions=[
            LogInfo(msg=["[bringup] nav_delay elapsed — starting Nav2 navigation stack."]),
            nav_bringup_group,
        ],
    )

    slam_and_nav_timer = TimerAction(
        period=slam_delay,
        actions=[
            LogInfo(msg=["[bringup] slam_delay elapsed — starting slam_toolbox."]),
            slam_bringup_group,
            # Nav timer starts counting from the moment slam fires.
            nav_timer,
        ],
    )

    return LaunchDescription(
        [
            SetEnvironmentVariable("RCUTILS_LOGGING_BUFFERED_STREAM", "1"),
            declare_autostart_arg,
            declare_log_level_arg,
            declare_map_arg,
            declare_namespace_arg,
            declare_observation_topic_arg,
            declare_observation_topic_type_arg,
            declare_params_file_arg,
            declare_pc2ls_params_file_arg,
            declare_slam_arg,
            declare_slam_delay_arg,
            declare_nav_delay_arg,
            declare_use_composition_arg,
            declare_use_respawn_arg,
            declare_use_sim_time_arg,
            declare_use_rviz_arg,
            declare_rviz_config_file_cmd,
            TimerAction(
                period=1.0,
                actions=[
                    LogInfo(msg=["[bringup] Hardware gate elapsed — starting crop_box and SLAM timer."]),
                    pointcloud_crop_box_node,
                    slam_and_nav_timer,
                ],
            ),
        ]
    )