#!/usr/bin/env python
import rospy
from sensor_msgs.msg import Image
from nav_msgs.msg import Path
from rosgraph_msgs.msg import Clock
import cv2
from cv_bridge import CvBridge
import os
import csv
import rosbag  

class RosbagSynchronizer:
    def __init__(self):
        # Initialize node
        rospy.init_node('rosbag_synchronizer', anonymous=True)

        # Parameters
        self.output_folder = "./trajectory_sync/images"
        self.csv_file = "./trajectory_sync/timestamps.csv"
        self.image_topic = "/camera/color/image_raw"
        self.path_topic = "/path"
        self.clock_topic =  "/clock"
        self.seq=1

        # Create output directories if they don't exist
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

        # Bridge to convert ROS Image to OpenCV Image
        self.bridge = CvBridge()

        # Initialize CSV file for saving timestamps
        self.csv_file_handle = open(self.csv_file, mode='w')
        self.csv_writer = csv.writer(self.csv_file_handle)
        self.csv_writer.writerow(["image_filename", "timestamp"])
        # self.corrected_path_bag = rosbag.Bag('./trajectory_sync/path.bag', 'w')

        # Variables
        self.current_time = None

        # Subscribers
        rospy.Subscriber(self.clock_topic, Clock, self.clock_callback)
        rospy.Subscriber(self.image_topic, Image, self.image_callback)
        rospy.Subscriber(self.path_topic, Path, self.path_callback)

        rospy.loginfo("Synchronizer initialized. Saving images to: {}".format(self.output_folder))

    def clock_callback(self, msg):
        """
        Update the current time from the /clock topic.
        """
        self.current_time = msg.clock

    def image_callback(self, msg):
        """
        Process incoming images, save them, and record their timestamps.
        """
        if self.current_time is None:
            rospy.logwarn("Clock not yet initialized, skipping image.")
            return

        try:
            # Convert ROS Image message to OpenCV image
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            timestamp = self.current_time.to_sec()

            # Save image with timestamp as filename
            image_filename = os.path.join(self.output_folder, f"image_{str(self.seq).zfill(5)}.png")
            self.seq+=1
            cv2.imwrite(image_filename, cv_image)

            # Log to CSV
            self.csv_writer.writerow([os.path.basename(image_filename), timestamp])

        except Exception as e:
            rospy.logerr(f"Failed to process image: {e}")

    def path_callback(self, msg):
        """
        Process incoming /path messages (optional: use this for verification/logging).
        """
        if self.current_time is None:
            rospy.logwarn("Clock not yet initialized, skipping path message.")
            return

        try:
            # Correct the header timestamp using the current clock time
            corrected_msg = msg
            corrected_msg.header.stamp = self.current_time  # Set header timestamp

            # Write the corrected message to the rosbag
            # self.corrected_path_bag.write(self.path_topic, corrected_msg, self.current_time)

        except Exception as e:
            rospy.logerr(f"Failed to write corrected path to bag: {e}")

    def cleanup(self):
        """
        Clean up CSV file resources.
        """
        self.csv_file_handle.close()
        # self.corrected_path_bag.close()
        rospy.loginfo("CSV file closed. Exiting.")

if __name__ == '__main__':
    try:
        synchronizer = RosbagSynchronizer()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
    finally:
        synchronizer.cleanup()