from rosbags.highlevel import AnyReader
from rosbags.rosbag2 import Writer
from rosbags.typesys import Stores, get_typestore
import sys
from pathlib import Path
import shutil, os

def merge_bags(immesh_bag_path, colmap_bag_path, output_bag_path, topic):
    typestore = get_typestore(Stores.ROS2_JAZZY)

    if os.path.exists(output_bag_path):
        shutil.rmtree(output_bag_path)
    with Writer(output_bag_path, version=Writer.VERSION_LATEST) as writer:
        conn_immesh=writer.add_connection("/immesh_path", "geometry_msgs/msg/PoseStamped", typestore=typestore)
        conn_colmap=writer.add_connection("/colmap_path", "geometry_msgs/msg/PoseStamped", typestore=typestore)
        with AnyReader([Path(immesh_bag_path)], default_typestore=typestore) as reader:
            for connection, timestamp, rawdata in reader.messages():
                if connection.topic==topic:
                    writer.write(conn_immesh, timestamp, rawdata)

        with AnyReader([Path(colmap_bag_path)], default_typestore=typestore) as reader:
            for connection, timestamp, rawdata in reader.messages():
                if connection.topic==topic:
                    writer.write(conn_colmap, timestamp, rawdata)


if __name__ == "__main__":
    if len(sys.argv) >= 4:
        immesh_bag_path = sys.argv[1]
        colmap_bag_path = sys.argv[2]
        topic = sys.argv[3]
    else:
        immesh_bag_path = './trajectory_sync/immesh_path'
        colmap_bag_path = './trajectory_sync/colmap_path'
        topic="/path"
    output_bag_path = './trajectory_sync/merged_path'
    merge_bags(immesh_bag_path, colmap_bag_path, output_bag_path, topic)