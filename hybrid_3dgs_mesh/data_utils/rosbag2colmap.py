#!/usr/bin/env python
import rospy
from geometry_msgs.msg import PoseStamped
from rosbags.highlevel import AnyReader
from rosbags.typesys import Stores, get_typestore
import json
import numpy as np
from copy import copy
from tf.transformations import *
from pathlib import Path

def main():
    # Parameters
    bag_file = "./trajectory_sync/colmap_path"
    output_file = "./scientific_park_gof/sparse/reference_images.txt"
    transform_file = "./trajectory_sync/transform.json"
    images_file = "./scientific_park_gof/sparse_ImMesh/0/images.txt"
    path_topic = "/path"

    # Load transformation
    with open(transform_file) as f:
        transform = json.load(f)

    q = np.array([transform["qx"], transform["qy"], transform["qz"], transform["qw"]])
    t = np.array([transform["x"], transform["y"], transform["z"]])
    transform_matrix = quaternion_matrix(q)
    transform_matrix[:3,3]=t
    transform_matrix[3,3]=transform["scale"]

    # Read image data from images.txt
    image_data = {}
    with open(images_file) as f:
        lines = f.readlines()
        for i in range(4, len(lines), 2):
            line = lines[i].split(" ")
            image_id = int(line[0])
            image_name = line[9].rstrip()
            image_data[image_id] = image_name
    # Open bag file
    typestore = get_typestore(Stores.ROS2_JAZZY)
    id = 1
    with open(output_file, 'w') as f:
        with AnyReader([Path(bag_file)], default_typestore=typestore) as reader:
            for connection, timestamp, rawdata in reader.messages():
                if connection.topic==path_topic:
                    msg = typestore.deserialize_cdr(rawdata, connection.msgtype)
                    pose = msg.pose
                    position = np.array([pose.position.x, pose.position.y, pose.position.z])
                    orientation = np.array([pose.orientation.x, pose.orientation.y, pose.orientation.z, pose.orientation.w])

                    pose_matrix = quaternion_matrix(orientation)
                    pose_matrix[:3,3]=position
                    pose_matrix = transform_matrix@pose_matrix #Apply transformation
                    t = pose_matrix[:3,3]

                    # Write to file in colmap format
                    f.write("{}, {}, {}, {}\n".format(image_data[id], t[0], t[1], t[2]))
                    id+=1

if __name__ == '__main__':
    main()