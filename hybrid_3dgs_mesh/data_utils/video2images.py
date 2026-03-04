import os
import cv2
import sys

if len(sys.argv) < 3 or not os.path.exists(sys.argv[1]):
    print("Usage: python video2images.py Video_path Frame_interval (Start_index)")
    sys.exit(1)

video_path = sys.argv[1]
frame_interval = int(sys.argv[2])
if len(sys.argv) > 3: start_index= int(sys.argv[3])
else: start_index=0
output_dir = os.path.join(os.path.dirname(video_path),os.path.basename(video_path).split(".")[0])
output_file = os.path.join(output_dir, "image_list.txt")

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

cap = cv2.VideoCapture(video_path)
frame_count = 0
saved_count = start_index
output_file = open(output_file, "w")
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    if frame_count % frame_interval == 0:
        output_path = os.path.join(output_dir, f"frame_{saved_count:04d}.jpg")
        cv2.imwrite(output_path, frame)
        output_file.write(f"frame_{saved_count:04d}.jpg\n")
        saved_count += 1

    frame_count += 1
output_file.close()
cap.release()
print(f"Extracted {saved_count-start_index} frames to {output_dir}")