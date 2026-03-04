import argparse
import os
import numpy as np
import rosbag
from cv_bridge import CvBridge
import cv2
import json


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Prepare data for NefStudio from rosbag and optimized poses')

    parser.add_argument('--start_frame', type=int, default=0, metavar='X',
                        help='Start saving data after start frame (Default 0)')
    parser.add_argument('--rosbag', type=str,required=True,
                        help='Rosbag file (with images and camera intrinsics)')
    parser.add_argument('--camera_topic', type=str, default="/camera/color",
                        help='Prefix of the camera topics "camera_topic"/camera_info and "camera_topic"/image_raw (Default /camera/color)')
    parser.add_argument('--output', type=str, required=True,
                        help='Output folder.')
    parser.add_argument('--width', type=int, default=1280, metavar='X',
                        help='Width of the images (Default: 1280)')
    parser.add_argument('--height', type=int, default=720, metavar='X',
                        help='Height of the images (Default: 720)')

    args = parser.parse_args()

    # Read rosbag
    bag = rosbag.Bag(args.rosbag)
    frame=-1
    frames_between_samples=15 #The topic is published at 15Hz, so a sample every second
    previous_frame=-frames_between_samples
    bridge = CvBridge()
 

    # Read images. The images has a higher frequency than the poses, which are related with other topic.
    # This topic is used to get the frame and the time to synchronize the pose with the closest image.
    if not os.path.exists(args.output):
        os.mkdir(args.output)
    if not os.path.exists(args.output+"/images"):
        os.mkdir(args.output+"/images")
    
    topics=(args.camera_topic+"/image_raw")

    for topic,msg,t in bag.read_messages(topics=topics):
        frame+=1
        if frame > args.start_frame and frame-previous_frame>=frames_between_samples:
            t = t.to_sec()
            cvimage=bridge.imgmsg_to_cv2(msg, "bgr8")
            cv2.imshow("Image",cvimage)
            key = cv2.waitKey(10000)
            if key == 13: 
                sec, nsec = str(t).split(".")   
                cv2.imwrite(args.output+"/images/{}_{}.png".format(sec,nsec[:2]),cvimage)
                previous_frame=frame
                print("Saving frame {}".format(frame))
            elif key == 27:
                break

    bag.close()
    cv2.destroyAllWindows()
    print("Finished")
