source /opt/ros/humble/setup.bash
BAG_NAME="panther_recording_$(date +%Y%m%d_%H%M%S)"
echo "Recording bag file..."
echo "Outputting bag to ${HOME}/ros2_ws/src/data/$BAG_NAME"
ros2 bag record -o ${HOME}/ros2_ws/src/data/$BAG_NAME \
    /oakd1/oak_d_node/rgb/image_rect_color \
    /oakd2/oak_d_node/rgb/image_rect_color \
    /oakd3/oak_d_node/rgb/image_rect_color \
    /imu/data \
    /odometry/filtered
    #/camera/color/image_raw \
    #/camera/color/camera_info \