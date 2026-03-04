import os
import shutil
import sys

if len(sys.argv) < 3 or not os.path.exists(sys.argv[1]) or not os.path.exists(sys.argv[2]):
    print("Usage: python copy_images.py input_image_folder output_image_folder")
    sys.exit(1)

image_folder = sys.argv[1]
output_dir = sys.argv[2]
output_file = os.path.join(output_dir, "image_list.txt")


with open(output_file, 'w') as file:
    for image_name in os.listdir(image_folder):
        image_path = os.path.join(image_folder, image_name)
        if os.path.isfile(image_path):
            output_path = os.path.join(output_dir, image_name)
            shutil.copy(image_path, output_path)
            file.write(image_name + '\n')