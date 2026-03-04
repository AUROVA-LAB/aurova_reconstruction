import argparse
import os
import numpy as np
import rosbag
from cv_bridge import CvBridge
import cv2
import json


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Prepare data for NefStudio from rosbag and optimized poses')

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

    # Read rosbag
    bag = rosbag.Bag(args.rosbag_images)
    for topic, msg, t in bag.read_messages():
        first_time = t.to_sec()
        break
    bag.close()

    bag = rosbag.Bag(args.rosbag_path)
    output_file = open(args.output+"/pose_priors.txt", 'w')
    images_list = os.listdir(args.images_folder)
    images_list = sorted(images_list)
    time_diference = None
    idx=0
    sec, decimals = images_list[idx].split(".")[0].split("_")
    image_time = float(sec)+float(decimals)/(10**len(decimals))
    for topic,msg,t in bag.read_messages(topics=args.pose_topic):
        if time_diference is None:
            time_diference = t.to_sec()-first_time
        pose_time = msg.poses[-1].header.stamp.to_sec()
        if image_time<pose_time-time_diference:
            previous_pose_time = msg.poses[-2].header.stamp.to_sec()
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
    bag.close()
    print("Finished")
