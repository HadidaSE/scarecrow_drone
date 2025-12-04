#!/usr/bin/env python3
"""
ROS Camera Node for development/testing
Publishes camera frames from webcam or other sources
"""

import rospy
import cv2
import yaml
from pathlib import Path
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

from camera_handler import create_camera


class CameraNode:
    """ROS node for camera input"""

    def __init__(self):
        """Initialize the camera node"""
        rospy.init_node('camera_node', anonymous=True)

        # Load configuration
        config_path = rospy.get_param(
            '~config_path',
            str(Path(__file__).parent.parent / 'config' / 'detector_config.yaml')
        )
        self.config = self._load_config(config_path)

        # Camera settings
        camera_config = self.config.get('camera', {})
        self.source_type = camera_config.get('source', 'webcam')
        self.device_id = camera_config.get('device_id', 0)
        self.width = camera_config.get('width', 640)
        self.height = camera_config.get('height', 480)
        self.fps = camera_config.get('fps', 30)

        # ROS settings
        ros_config = self.config.get('ros', {})
        self.output_topic = ros_config.get('input_topic', '/camera/rgb/image_raw')
        self.publish_rate = ros_config.get('publish_rate', 10)

        # Initialize CV bridge
        self.bridge = CvBridge()

        # Publisher
        self.image_pub = rospy.Publisher(self.output_topic, Image, queue_size=1)

        # Initialize camera
        self._init_camera()

        rospy.loginfo(f"Camera Node initialized")
        rospy.loginfo(f"  Source: {self.source_type}")
        rospy.loginfo(f"  Publishing to: {self.output_topic}")

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                rospy.loginfo(f"Loaded config from {config_path}")
                return config
        except Exception as e:
            rospy.logwarn(f"Could not load config from {config_path}: {e}")
            return {}

    def _init_camera(self):
        """Initialize camera based on configuration"""
        if self.source_type == 'webcam':
            self.camera = create_camera(
                'webcam',
                device_id=self.device_id,
                width=self.width,
                height=self.height,
                fps=self.fps
            )
        elif self.source_type == 'realsense':
            self.camera = create_camera(
                'realsense',
                width=self.width,
                height=self.height,
                fps=self.fps
            )
        else:
            rospy.logwarn(f"Unknown source type: {self.source_type}, defaulting to webcam")
            self.camera = create_camera('webcam', device_id=0)

        if not self.camera.is_opened():
            rospy.logerr("Failed to open camera!")

    def run(self):
        """Run the camera node"""
        rate = rospy.Rate(self.publish_rate)

        while not rospy.is_shutdown():
            ret, frame = self.camera.read()

            if ret and frame is not None:
                try:
                    # Convert to ROS message
                    img_msg = self.bridge.cv2_to_imgmsg(frame, "bgr8")
                    img_msg.header.stamp = rospy.Time.now()
                    img_msg.header.frame_id = "camera_frame"

                    # Publish
                    self.image_pub.publish(img_msg)

                except Exception as e:
                    rospy.logerr(f"Error publishing image: {e}")
            else:
                rospy.logwarn_throttle(5.0, "Failed to read camera frame")

            rate.sleep()

        self.camera.release()


def main():
    try:
        node = CameraNode()
        node.run()
    except rospy.ROSInterruptException:
        pass


if __name__ == '__main__':
    main()
