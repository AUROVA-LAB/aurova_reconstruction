import argparse
import os
import numpy as np
from rosbags.highlevel import AnyReader
from rosbags.typesys import Stores, get_typestore
from cv_bridge import CvBridge
import cv2
import json
from pathlib import Path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Prepare data for NerfStudio from rosbag and optimized poses')

    parser.add_argument('--rosbag_path', type=str,required=True,
                        help='Rosbag file from ImMesh(with pose priors)')
    parser.add_argument('--rosbag_images', type=str,required=True,
                        help='Rosbag file with images, to get the time difference between rosbags.')
    parser.add_argument('--pose_topic', type=str, default="/path",
                        help='Prefix of the pose topic. It is a trajectory msg as it cames from ImMesh (Default /path)')
    parser.add_argument('--images_folder', type=str, required=True,
                        help='Folder with the images, that are named as the timestamps.')
    parser.add_argument('--output', type=str, required=True,
                        help='Output folder (filename is pose_priors.txt).')

    args = parser.parse_args()
    typestore = get_typestore(Stores.ROS2_JAZZY)
    # Read rosbag

    with AnyReader([Path(args.rosbag_images)], default_typestore=typestore) as reader:
        for connection, timestamp, rawdata in reader.messages():
            first_time = timestamp
            break

    output_file = open(args.output+"/pose_priors.txt", 'w')
    images_list = os.listdir(args.images_folder)
    images_list = sorted(images_list)
    time_diference = None
    idx=0
    sec, decimals = images_list[idx].split(".")[0].split("_")
    image_time = float(sec)+float(decimals)/(10**len(decimals))
    with AnyReader([Path(args.rosbag_path)], default_typestore=typestore) as reader:
        for connection, timestamp, rawdata in reader.messages():
            if connection.topic==args.pose_topic:
                if time_diference is None:
                    time_diference = (timestamp -first_time)/10**9
                msg = typestore.deserialize_cdr(rawdata, connection.msgtype)
                head = msg.poses[-1].header
                pose_time = head.stamp.sec  + head.stamp.nanosec/10**9
                if image_time<pose_time-time_diference:
                    head = msg.poses[-2].header
                    previous_pose_time = head.stamp.sec + head.stamp.nanosec/10**9
                    if abs(image_time-previous_pose_time-time_diference) < abs(image_time-pose_time-time_diference):
                        output_file.write("{} {} {} {}\n".format(images_list[idx], 
                                        msg.poses[-2].pose.position.x, msg.poses[-2].pose.position.y, msg.poses[-2].pose.position.z))
                    else:
                        output_file.write("{} {} {} {}\n".format(images_list[idx], 
                                        msg.poses[-1].pose.position.x, msg.poses[-1].pose.position.y, msg.poses[-1].pose.position.z))
                    print("Writing pose for image {}".format(images_list[idx]))
                    idx+=1
                    if idx>=len(images_list):
                        break
                    sec, decimals = images_list[idx].split(".")[0].split("_")
                    image_time = float(sec)+float(decimals)/(10**len(decimals))
    output_file.close()
    print("Finished")
