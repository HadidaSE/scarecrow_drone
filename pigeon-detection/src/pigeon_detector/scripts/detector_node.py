#!/usr/bin/env python3
"""
ROS Node for Pigeon Detection
Designed for Intel Aero drone with RealSense camera
"""

import rospy
import cv2
import yaml
import numpy as np
from pathlib import Path
from sensor_msgs.msg import Image
from std_msgs.msg import String, Int32
from cv_bridge import CvBridge, CvBridgeError
from geometry_msgs.msg import Point

# Import local modules
from pigeon_detector import PigeonDetector, Detection


class PigeonDetectorNode:
    """ROS node for pigeon detection using YOLO"""

    def __init__(self):
        """Initialize the detector node"""
        rospy.init_node('pigeon_detector_node', anonymous=True)

        # Load configuration
        config_path = rospy.get_param(
            '~config_path',
            str(Path(__file__).parent.parent / 'config' / 'detector_config.yaml')
        )
        self.config = self._load_config(config_path)

        # Initialize CV bridge
        self.bridge = CvBridge()

        # Initialize detector
        model_config = self.config.get('model', {})
        self.detector = PigeonDetector(
            model_path=model_config.get('weights', 'yolov8n.pt'),
            confidence_threshold=model_config.get('confidence_threshold', 0.5),
            iou_threshold=model_config.get('iou_threshold', 0.45),
            device=model_config.get('device', 'cpu'),
            img_size=model_config.get('img_size', 640)
        )

        # Detection settings
        detection_config = self.config.get('detection', {})
        self.draw_boxes = detection_config.get('draw_boxes', True)
        self.box_color = tuple(detection_config.get('box_color', [0, 255, 0]))

        # Set up ROS topics
        ros_config = self.config.get('ros', {})
        input_topic = ros_config.get('input_topic', '/camera/rgb/image_raw')
        output_topic = ros_config.get('output_topic', '/pigeon_detector/detections')
        image_output_topic = ros_config.get('image_output_topic', '/pigeon_detector/image_annotated')

        # Publishers
        self.detection_pub = rospy.Publisher(output_topic, String, queue_size=10)
        self.count_pub = rospy.Publisher('/pigeon_detector/count', Int32, queue_size=10)
        self.image_pub = rospy.Publisher(image_output_topic, Image, queue_size=1)
        self.center_pub = rospy.Publisher('/pigeon_detector/centers', Point, queue_size=10)

        # Subscriber
        self.image_sub = rospy.Subscriber(input_topic, Image, self.image_callback)

        rospy.loginfo(f"Pigeon Detector Node initialized")
        rospy.loginfo(f"  Subscribed to: {input_topic}")
        rospy.loginfo(f"  Publishing detections to: {output_topic}")
        rospy.loginfo(f"  Publishing annotated images to: {image_output_topic}")

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                rospy.loginfo(f"Loaded config from {config_path}")
                return config
        except Exception as e:
            rospy.logwarn(f"Could not load config from {config_path}: {e}")
            rospy.logwarn("Using default configuration")
            return {}

    def image_callback(self, msg: Image):
        """Process incoming image messages"""
        try:
            # Convert ROS Image to OpenCV
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")

            # Run detection
            annotated, detections = self.detector.detect_and_annotate(
                cv_image,
                box_color=self.box_color
            )

            # Publish detection count
            self.count_pub.publish(Int32(len(detections)))

            # Publish detection details
            for det in detections:
                # Detection info as JSON string
                detection_msg = f'{{"class": "{det.class_name}", "confidence": {det.confidence:.3f}, "bbox": {list(det.bbox)}, "center": {list(det.center)}}}'
                self.detection_pub.publish(String(detection_msg))

                # Publish center point
                center_point = Point()
                center_point.x = float(det.center[0])
                center_point.y = float(det.center[1])
                center_point.z = 0.0
                self.center_pub.publish(center_point)

            # Publish annotated image
            if self.draw_boxes:
                annotated_msg = self.bridge.cv2_to_imgmsg(annotated, "bgr8")
                annotated_msg.header = msg.header
                self.image_pub.publish(annotated_msg)

            if len(detections) > 0:
                rospy.loginfo(f"Detected {len(detections)} pigeon(s)")

        except CvBridgeError as e:
            rospy.logerr(f"CV Bridge Error: {e}")
        except Exception as e:
            rospy.logerr(f"Detection error: {e}")

    def run(self):
        """Run the node"""
        rospy.loginfo("Pigeon Detector Node running...")
        rospy.spin()


def main():
    try:
        node = PigeonDetectorNode()
        node.run()
    except rospy.ROSInterruptException:
        pass


if __name__ == '__main__':
    main()
