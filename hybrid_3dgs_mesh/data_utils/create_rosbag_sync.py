import argparse
import os
import numpy as np
from rosbags.highlevel import AnyReader
from rosbags.rosbag2 import Writer
from rosbags.typesys import Stores, get_typestore
from geometry_msgs.msg import PoseStamped
from tf_transformations import *
from pathlib import Path
import shutil


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Prepare data for NefStudio from rosbag and optimized poses')

    parser.add_argument('--rosbag_path', type=str,required=True,
                        help='Rosbag file from ImMesh(with pose priors)')
    parser.add_argument('--rosbag_images', type=str,required=True,
                        help='Rosbag file with images, to get the time difference between rosbags.')
    parser.add_argument('--pose_topic', type=str, default="/path",
                        help='Prefix of the pose topic. It is a trajectory msg as it cames from ImMesh (Default /path)')
    parser.add_argument('--images_colmap', type=str, required=True,
                        help='images.txt output from colmap')

    args = parser.parse_args()
    typestore = get_typestore(Stores.ROS2_JAZZY)
    # Read rosbag
    with AnyReader([Path(args.rosbag_images)], default_typestore=typestore) as reader:
        for connection, timestamp, rawdata in reader.messages():
            first_time = timestamp
            break


    with AnyReader([Path(args.rosbag_path)], default_typestore=typestore) as reader:
        for connection, timestamp, rawdata in reader.messages():
            last_msg = rawdata
    last_msg = typestore.deserialize_cdr(last_msg, connection.msgtype)
    timestamp=last_msg.poses[0].header.stamp
    time_diference = timestamp.sec*10**9+timestamp.nanosec-first_time

    if os.path.exists('./trajectory_sync/immesh_path'):
        shutil.rmtree('./trajectory_sync/immesh_path')
    with Writer('./trajectory_sync/immesh_path', version=Writer.VERSION_LATEST) as correct_path_bag:
        conn=correct_path_bag.add_connection(args.pose_topic, "geometry_msgs/msg/PoseStamped", typestore=typestore)
        for pose in last_msg.poses:
            headstamp = pose.header.stamp.sec * 10**9 + pose.header.stamp.nanosec -time_diference
            pose.header.stamp.sec = headstamp // 10**9
            pose.header.stamp.nanosec = headstamp % 10**9
            outdata = typestore.serialize_cdr(pose, conn.msgtype)
            correct_path_bag.write(conn,headstamp,outdata)


    if os.path.exists('./trajectory_sync/colmap_path'):
        shutil.rmtree('./trajectory_sync/colmap_path')
    with open(args.images_colmap) as f, Writer('./trajectory_sync/colmap_path', version=Writer.VERSION_LATEST) as output_bag:
        conn=output_bag.add_connection(args.pose_topic, "geometry_msgs/msg/PoseStamped", typestore=typestore)
        for i, line in enumerate(f):
            if i%2!=0 or i<4: continue
            line = line.split(" ")
            pose = PoseStamped()
            try:
                sec, decimals = line[9].split(".")[0].split("_")
                nanosec = float(decimals)/(10**len(decimals))*10**9
                sec, nanosec = int(sec), int(nanosec)
                pose.header.stamp.sec = sec
                pose.header.stamp.nanosec = nanosec
                # Inverse the transform of colmap
                quat = np.array([float(line[2]),float(line[3]),float(line[4]),float(line[1])])
                R = quaternion_matrix(quat)[:3,:3]
                t = np.array([float(line[5]),float(line[6]),float(line[7])])
                t = np.matmul(-R.transpose(),t)
                transform = np.eye((4))
                transform[:3,:3] = R.transpose()
                quat_inv = quaternion_from_matrix(transform)
                pose.pose.position.x, pose.pose.position.y, pose.pose.position.z  = t[0],t[1],t[2]
                pose.pose.orientation.x,pose.pose.orientation.y,pose.pose.orientation.z,pose.pose.orientation.w = \
                    quat_inv[0],quat_inv[1],quat_inv[2],quat_inv[3]
                outdata = typestore.serialize_cdr(pose, conn.msgtype)
                output_bag.write(conn,sec*10**9+nanosec,outdata)
            except ValueError:
                pass

    
    print("Finished")
