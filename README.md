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

Before Running the Stack

```
source /opt/ros/jazzy/setup.bash
export ROBOT_NAMESPACE=panther
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

If using Slam

```
ros2 launch utexas_panther bringup.launch.py slam:=True
```

Ouster

Make sure you run the following line to run the ouster

```
ros2 launch ouster_ros sensor.launch.xml     sensor_hostname:=169.254.175.115     timestamp_mode:=TIME_FROM_ROS_TIME     viz:=false
```

And also create a tf transform between the base and lidar

```
ros2 run tf2_ros static_transform_publisher 0 0 0.5 0 0 0 panther/base_link os_sensor
```
