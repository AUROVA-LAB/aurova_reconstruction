import rosbag
import sys

def merge_bags(immesh_bag_path, colmap_bag_path, output_bag_path, topic):
    immesh_bag = rosbag.Bag(immesh_bag_path)
    colmap_bag = rosbag.Bag(colmap_bag_path)
    output_bag = rosbag.Bag(output_bag_path, 'w')

    try:
        for topic, msg, t in immesh_bag.read_messages(topics=[topic]):
            output_bag.write('/immesh_path', msg, t)

        for topic, msg, t in colmap_bag.read_messages(topics=[topic]):
            output_bag.write('/colmap_path', msg, t)
    finally:
        immesh_bag.close()
        colmap_bag.close()
        output_bag.close()

if __name__ == "__main__":
    if len(sys.argv) >= 4:
        immesh_bag_path = sys.argv[1]
        colmap_bag_path = sys.argv[2]
        topic = sys.argv[3]
    else:
        immesh_bag_path = './trajectory_sync/immesh_path.bag'
        colmap_bag_path = './trajectory_sync/colmap_path.bag'
        topic="/path"
    output_bag_path = './trajectory_sync/merged_path.bag'
    merge_bags(immesh_bag_path, colmap_bag_path, output_bag_path, topic)