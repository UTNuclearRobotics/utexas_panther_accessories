source /opt/ros/humble/setup.bash
BAG_NAME="panther_recording_$(%Y%m%d_%H%M%S)"
echo "Recording bag file..."
echo "Outputting bag to $HOME/$BAG_NAME"
ros2 bag record -o $HOME/$BAG_NAME \
    /oak/rgb/image_raw/compressed \
    /oak/rgb/camera_info \
    /oak/imu/data \
    /ouster/imu \
    /panther/odometry/filtered \
    /panther/odometry/wheels \
    /panther/imu/data