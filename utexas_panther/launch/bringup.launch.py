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

import tempfile

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
    OpaqueFunction,
    SetEnvironmentVariable,
    SetLaunchConfiguration,
)
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    EnvironmentVariable,
    LaunchConfiguration,
    PathJoinSubstitution,
    PythonExpression,
)
from launch_ros.actions import Node, PushRosNamespace
from launch_ros.descriptions import ParameterFile
from launch_ros.substitutions import FindPackageShare
from nav2_common.launch import RewrittenYaml


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
    robot_model = LaunchConfiguration("robot_model")
    slam = LaunchConfiguration("slam")
    use_composition = LaunchConfiguration("use_composition")
    use_respawn = LaunchConfiguration("use_respawn")
    use_sim_time = LaunchConfiguration("use_sim_time")
    use_rviz = LaunchConfiguration("use_rviz")

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
        "map",
        default_value="/maps/map.yaml",
        description="Path to map yaml file to load.",
    )
    declare_namespace_arg = DeclareLaunchArgument(
        "namespace",
        default_value=EnvironmentVariable("ROBOT_NAMESPACE", default_value=""),
        description="Add namespace to all launched nodes.",
    )
    declare_observation_topic_arg = DeclareLaunchArgument(
        "observation_topic",
        default_value="/ouster/points",
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
        default_value=PathJoinSubstitution(
            [utexas_panther, "config", "nav2_params.yaml"]
        ),
        description="Path to the parameters file to use for all nav2 related nodes",
    )
    declare_robot_model_arg = DeclareLaunchArgument(
        "robot_model",
        default_value=EnvironmentVariable(name="ROBOT_MODEL_NAME", default_value="panther"),
        description="Specify robot model",
        choices=["lynx", "panther"],
    )
    declare_slam_arg = DeclareLaunchArgument(
        "slam", default_value="False", description="Whether run a SLAM."
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
        default_value="true",
        description="Use simulation (Gazebo) clock if true.",
    )
    declare_use_rviz_arg = DeclareLaunchArgument(
        "use_rviz",
        default_value="true",
        description="Whether to launch RViz.",
    )

    robot_bounding_box = {
        "panther": {
            "min_x": -0.85,
            "min_y": -0.95,
            "min_z": 0.05,
            "max_x": 0.85,
            "max_y": 0.95,
            "max_z": 0.65,
        },
        "lynx": {
            "min_x": -0.38,
            "min_y": -0.33,
            "min_z": 0.05,
            "max_x": 0.38,
            "max_y": 0.33,
            "max_z": 0.5,
        },
    }

    # OpaqueFunction: resolves all <placeholder> substitutions at launch time
    # by reading the yaml, doing string replacements, and writing a temp file.
    # use_sim_time and yaml_filename are intentionally LEFT for RewrittenYaml
    # to handle, since it correctly coerces types via convert_types=True.
    def resolve_placeholders(context, *args, **kwargs):
        robot_model_name = LaunchConfiguration("robot_model").perform(context)
        namespace_val = LaunchConfiguration("namespace").perform(context)
        observation_topic_val = LaunchConfiguration("observation_topic").perform(context)
        observation_topic_type_val = LaunchConfiguration("observation_topic_type").perform(context)
        params_file_val = LaunchConfiguration("params_file").perform(context)

        bounding_box = robot_bounding_box[robot_model_name]
        namespace_ext_val = namespace_val + "/" if namespace_val else ""
        scan_topic_val = "scan" if observation_topic_type_val == "pointcloud" else observation_topic_val

        with open(params_file_val, "r") as f:
            content = f.read()

        # Only replace structural <placeholder> tokens here.
        # use_sim_time and yaml_filename are handled by RewrittenYaml below.
        replacements = {
            "<namespace>/": namespace_ext_val,
            "<min_x>": str(bounding_box["min_x"]),
            "<max_x>": str(bounding_box["max_x"]),
            "<min_y>": str(bounding_box["min_y"]),
            "<max_y>": str(bounding_box["max_y"]),
            "<min_z>": str(bounding_box["min_z"]),
            "<max_z>": str(bounding_box["max_z"]),
            "<observation_topic>": observation_topic_val,
            "<observation_topic_type>": observation_topic_type_val,
            "<scan_topic>": scan_topic_val,
        }

        for placeholder, value in replacements.items():
            content = content.replace(placeholder, str(value))

        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
        tmp.write(content)
        tmp.flush()
        tmp.close()

        return [SetLaunchConfiguration("resolved_params_file", tmp.name)]

    opaque_params = OpaqueFunction(function=resolve_placeholders)
    resolved_params_file = LaunchConfiguration("resolved_params_file")

    # RewrittenYaml handles use_sim_time and yaml_filename correctly
    # via LaunchConfiguration substitutions with convert_types=True.
    param_substitutions = {
        "use_sim_time": use_sim_time,
        "yaml_filename": map,
    }

    configured_params = ParameterFile(
        RewrittenYaml(
            source_file=resolved_params_file,
            param_rewrites=param_substitutions,
            convert_types=True,
        ),
        allow_substs=True,
    )

    observation_topic_filtered = PythonExpression(
        ["'", observation_topic, "_filtered'"],
    )

    rviz_config_file = PathJoinSubstitution([utexas_panther, "config", "rviz.rviz"])

    bringup_cmd_group = GroupAction(
        [
            PushRosNamespace(namespace),
            Node(
                condition=IfCondition(
                    PythonExpression(["'", observation_topic_type, "' == 'pointcloud'"])
                ),
                package="pointcloud_crop_box",
                executable="pointcloud_crop_box_node",
                name="pointcloud_crop_box",
                parameters=[configured_params],
                output="screen",
            ),
            Node(
                condition=IfCondition(
                    PythonExpression(["'", observation_topic_type, "' == 'pointcloud'"])
                ),
                package="pointcloud_to_laserscan",
                executable="pointcloud_to_laserscan_node",
                name="pointcloud_to_laserscan",
                parameters=[configured_params],
                remappings=[("cloud_in", observation_topic_filtered)],
                output="screen",
            ),
            Node(
                condition=IfCondition(use_composition),
                name="nav2_container",
                package="rclcpp_components",
                executable="component_container_isolated",
                parameters=[configured_params, {"autostart": autostart}],
                arguments=["--ros-args", "--log-level", log_level],
                output="screen",
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution([launch_dir, "slam_launch.py"])
                ),
                condition=IfCondition(slam),
                launch_arguments={
                    "autostart": autostart,
                    "namespace": namespace,
                    "params_file": resolved_params_file,
                    "use_respawn": use_respawn,
                    "use_sim_time": use_sim_time,
                }.items(),
            ),
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
                    "params_file": resolved_params_file,
                    "use_composition": use_composition,
                    "use_respawn": use_respawn,
                    "use_sim_time": use_sim_time,
                }.items(),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution([utexas_panther_launch_dir, "navigation_launch.py"])
                ),
                launch_arguments={
                    "namespace": namespace,
                    "use_sim_time": use_sim_time,
                    "autostart": autostart,
                    "params_file": resolved_params_file,
                    "use_composition": use_composition,
                    "use_respawn": use_respawn,
                    "container_name": "nav2_container",
                }.items(),
            ),
            Node(
                condition=IfCondition(slam),
                name="map_autosaver",
                package="husarion_ugv_navigation",
                executable="map_autosaver_node",
                parameters=[configured_params],
                arguments=["--ros-args", "--log-level", log_level],
                output="screen",
            ),
        ]
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
            declare_robot_model_arg,
            declare_slam_arg,
            declare_use_composition_arg,
            declare_use_respawn_arg,
            declare_use_sim_time_arg,
            declare_use_rviz_arg,
            opaque_params,          # step 1: replace <placeholders> → temp yaml
            bringup_cmd_group,      # step 2: RewrittenYaml rewrites use_sim_time + yaml_filename
            Node(
                condition=IfCondition(use_rviz),
                package="rviz2",
                executable="rviz2",
                name="rviz2",
                arguments=["-d", rviz_config_file],
                parameters=[{"use_sim_time": use_sim_time}],
                output="screen",
            ),
        ]
    )