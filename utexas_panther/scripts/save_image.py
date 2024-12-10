import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2

class SaveImageNode(Node):
    def __init__(self):
        super().__init__('save_image_node')
        self.subscription = self.create_subscription(
            Image,
            '/oak/rgb/image_raw',  # Change to your topic
            self.callback,
            10)
        self.bridge = CvBridge()

    def callback(self, msg):
        self.get_logger().info("Image received!")
        image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        cv2.imwrite("saved_image.jpg", image)
        self.get_logger().info("Image saved as 'saved_image.jpg'")
        rclpy.shutdown()  # Shut down the node

def main(args=None):
    rclpy.init(args=args)
    node = SaveImageNode()
    rclpy.spin(node)

if __name__ == '__main__':
    main()
