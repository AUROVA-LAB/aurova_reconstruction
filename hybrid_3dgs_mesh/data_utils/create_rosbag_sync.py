import argparse
import os
import numpy as np
import rosbag
from geometry_msgs.msg import PoseStamped, Quaternion, Point
from tf.transformations import *
import rospy


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

    # Read rosbag
    bag = rosbag.Bag(args.rosbag_images)
    for topic, msg, t in bag.read_messages():
        first_time = t.to_sec()
        break
    bag.close()

    bag = rosbag.Bag(args.rosbag_path)

    time_diference = None
    for topic, msg, t in bag.read_messages(topics=[args.pose_topic]):
        last_msg=msg
    time_diference = last_msg.poses[0].header.stamp.to_sec()-first_time
    bag.close()

    output_bag = rosbag.Bag('./trajectory_sync/colmap_path.bag', 'w')
    correct_path_bag = rosbag.Bag('./trajectory_sync/immesh_path.bag', 'w')

    for pose in last_msg.poses:
        pose.header.stamp = rospy.Time(pose.header.stamp.to_sec()-time_diference)
        correct_path_bag.write(args.pose_topic,pose,pose.header.stamp)
    correct_path_bag.close() 

    with open(args.images_colmap) as f:
        for i, line in enumerate(f):
            if i%2!=0 or i<4: continue
            line = line.split(" ")
            pose = PoseStamped()
            try:
                sec, decimals = line[9].split(".")[0].split("_")
                image_time = float(sec)+float(decimals)/(10**len(decimals))
                pose.header.stamp = rospy.Time(image_time)
                # Inverse the transform of colmap
                quat = np.array([float(line[2]),float(line[3]),float(line[4]),float(line[1])])
                R = quaternion_matrix(quat)[:3,:3]
                t = np.array([float(line[5]),float(line[6]),float(line[7])])
                t = np.matmul(-R.transpose(),t)
                transform = np.eye((4))
                transform[:3,:3] = R.transpose()
                quat_inv = quaternion_from_matrix(transform)
                pose.pose.position = Point(t[0],t[1],t[2])
                pose.pose.orientation = Quaternion(quat_inv[0],quat_inv[1],quat_inv[2],quat_inv[3])
                output_bag.write(args.pose_topic,pose,pose.header.stamp)
            except ValueError:
                pass

    
    output_bag.close()
    print("Finished")
