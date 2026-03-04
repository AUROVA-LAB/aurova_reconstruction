import argparse
import os
import numpy as np
import rosbag
from cv_bridge import CvBridge
import cv2
import json
import tf


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
    images_list = os.listdir(args.images_folder)
    images_list = sorted(images_list)
    time_diference = None
    idx=0
    sec, decimals = images_list[idx].split(".")[0].split("_")
    image_time = float(sec)+float(decimals)/(10**len(decimals))
    output_data ={"w": 1280,
	"h": 720,
	"fl_x": 957.3995391985428,
	"fl_y": 873.0152541859704,
	"cx": 650.0357251952752,
	"cy": 367.36092700626375,
	"k1": 0.1275312544766248,
	"k2": -0.18984746964537919,
	"p1": 0.0028447527959978413,
	"p2": -0.0011637406039605217,
	"camera_model": "OPENCV",
    "frames": []}
    for topic,msg,t in bag.read_messages(topics=args.pose_topic):
        if time_diference is None:
            time_diference = t.to_sec()-first_time
        pose_time = msg.poses[-1].header.stamp.to_sec()
        if image_time<pose_time-time_diference:
            previous_pose_time = msg.poses[-2].header.stamp.to_sec()
            if abs(image_time-previous_pose_time-time_diference) < abs(image_time-pose_time-time_diference):
                transform=tf.transformations.quaternion_matrix([msg.poses[-2].pose.orientation.x, msg.poses[-2].pose.orientation.y, 
                                                                msg.poses[-2].pose.orientation.z, msg.poses[-2].pose.orientation.w])
                transform[:3,3]=[msg.poses[-2].pose.position.x, msg.poses[-2].pose.position.y, msg.poses[-2].pose.position.z]
                output_data["frames"].append({"file_path": "./"+args.images_folder+images_list[idx],
                            "transform_matrix": transform.tolist()})
            else:
                transform=tf.transformations.quaternion_matrix([msg.poses[-1].pose.orientation.x, msg.poses[-1].pose.orientation.y, 
                                                                msg.poses[-1].pose.orientation.z, msg.poses[-1].pose.orientation.w])
                transform[:3,3]=[msg.poses[-1].pose.position.x, msg.poses[-1].pose.position.y, msg.poses[-1].pose.position.z]
                output_data["frames"].append({"file_path": images_list[idx],
                            "transform": transform.tolist()})
            print("Writing pose for image {}".format(images_list[idx]))
            idx+=1
            if idx>=len(images_list):
                break
            sec, decimals = images_list[idx].split(".")[0].split("_")
            image_time = float(sec)+float(decimals)/(10**len(decimals))
    bag.close()
    with open(args.output+"/transforms.json", 'w') as file:
        json.dump(output_data, file,indent="\t")
    print("Finished")
