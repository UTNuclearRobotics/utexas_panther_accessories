# UTexas Husarion Panther Accessories

## Prerequisites

Make sure you have ROS 2 installed. You can follow the instructions [here](https://docs.ros.org/en/humble/Installation.html) to install ROS 2 Humble.

## Manual Setup

1. Create a ROS workspace with a `src` folder.

```sh
mkdir -p ~/utexas_panther_ws/src
```

2. Clone this repository along with its submodules. Make sure you're in the `src` directory.

```sh
git clone --recurse-submodules git@github.com:UTNuclearRobotics/utexas_panther_accessories.git
```

3. Install dependencies of packages. Make sure you're at the workspace root directory.

```sh
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y
```

4. Build the workspace.

```sh
colcon build
```

## Automatic Setup

You can also set up everything automatically with the following commands:

```sh
mkdir -p ~/utexas_panther_ws/src
cd ~/utexas_panther_ws/src
git clone --recurse-submodules git@github.com:UTNuclearRobotics/utexas_panther_accessories.git

cd ~/utexas_panther_ws
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build
```

## Launching Sensors

The following unified launch file initializes both the OAK-D depth camera and the Ouster LiDAR nodes, establishing the core data streams for perception (image and pointcloud):

```ros2 launch utexas_panther sensors.launch.py```

## Launching Slam

If you are operating in a new environment and need to generate a map, you will want to spin up the SLAM pipeline. The command below launches the main bringup routine with SLAM enabled, configured to consume point cloud data from the Ouster LiDAR.

```ros2 launch utexas_panther bringup.launch.py namespace:=panther observation_topic:=/ouster/points observation_topic_type:=pointcloud slam:=True```

## Launch AMLC

Once you have a saved map of your environment, you can switch from mapping mode to localization mode. Use the AMCL routine to pinpoint the robot's position within a static map. Remember to set a initial pose and drive around a lil bit to snap the robot into a more accurate position.

```ros2 launch utexas_panther bringup.launch.py namespace:=panther observation_topic:=/ouster/points observation_topic_type:=pointcloud slam:=False map:=/phantom_map.yaml```