import os
import numpy as np
import json
import tf.transformations as tr
import random
from copy import copy

def read_images_text(filepath):
    with open(filepath, 'r') as file:
        images={}
        for i,line in enumerate(file):
            if line.startswith('#'):
                continue
            if i%2==0:
                parts = line.strip().split()
                image_id = int(parts[0])
                qvec = list(map(float, parts[1:5]))
                qvec = np.array([qvec[1], qvec[2], qvec[3], qvec[0]])
                tvec = np.array(list(map(float, parts[5:8])))
                camera_id = int(parts[8])
                name = parts[9]
                images[image_id] = {
                    'qvec': qvec,
                    'tvec': tvec,
                    'camera_id': camera_id,
                    'name': name,
                }
    return images

def transform_image(image, new_from_old_world):
    new_image=set_cam_from_world(image, transform_camera_world(new_from_old_world, get_cam_from_world(image)))
    return new_image


def get_cam_from_world(image):
    transform={}
    transform["rotation"] = tr.quaternion_matrix(np.array(image['qvec']))[:3,:3]
    transform["translation"] = np.array(image['tvec'])
    transform["translation"] = np.matmul(-transform["rotation"].transpose(),transform["translation"])
    transform["rotation"]=transform["rotation"].transpose()
    return transform

def set_cam_from_world(image, cam_from_world):
    new_image = copy(image)
    new_image['qvec'] = tr.quaternion_from_matrix(cam_from_world["rotation"])
    new_image['tvec'] = cam_from_world["translation"]
    return new_image

def transform_camera_world(new_from_old_world, cam_from_world):
    cam_from_new_world = np.zeros((4,4))
    cam_from_new_world[:3,:3] = cam_from_world["rotation"]
    cam_from_new_world[:3,3] = cam_from_world["translation"]
    cam_from_new_world[3,3] = 1
    
    cam_from_new_world[:3,:3] = new_from_old_world["rotation"]@cam_from_new_world[:3,:3]
    cam_from_new_world[:3,3] = new_from_old_world["scale"]*(new_from_old_world["rotation"]@cam_from_world["translation"])+new_from_old_world["translation"]

    # Get the camera transform (inverse)
    cam_from_new_world[:3,:3] = cam_from_new_world[:3,:3].transpose()
    cam_from_new_world[:3,3] = -cam_from_new_world[:3,:3]@cam_from_new_world[:3,3]
    return {"rotation":cam_from_new_world,"translation":cam_from_new_world[:3,3]}

def readTransform(path):
    transform={}
    with open(path, 'r') as file:
        data = json.load(file)
        transform["translation"]=np.array([data["x"],data["y"],data["z"]])
        quat = np.array([data["qx"],data["qy"],data["qz"],data["qw"]])
        transform["rotation"]=tr.quaternion_matrix(quat)[:3,:3]
        transform["scale"]=data["scale"]
        return transform   

def main():
    # Read transform.json
    transform = readTransform('trajectory_sync/transform.json')
    
    # Read poses from both COLMAP outputs
    scene = "scientific_park_scene1/"
    poses1 = read_images_text(scene+'camera_calibration/aligned/sparse/images.txt')
    poses2 = read_images_text(scene+'sparse/images.txt')
    
    
    # Select 5 random images that exist in both outputs
    common_images = list(set(poses1.keys()) & set(poses2.keys()))
    selected_images = random.sample(common_images, min(5, len(common_images)))
    
    print("\nComparing poses for 5 random images:")
    print("-" * 80)
    
    for img_name in selected_images:
        pose1 = poses1[img_name]
        pose2 = poses2[img_name]
        pose1_transformed = transform_image(pose1, transform)
        
        print(f"\nImage: {img_name}")
        print("Position comparison (x, y, z):")
        print(f"Original 1:     {pose1['tvec']}")
        print(f"Original 2:     {pose2['tvec']}")
        print(f"Transformed 1:  {pose1_transformed['tvec']}")
        print("\nQuaternion comparison (w, x, y, z):")
        print(f"Original 1:     {pose1['qvec']}")
        print(f"Original 2:     {pose2['qvec']}")
        print(f"Transformed 1:  {pose1_transformed['qvec']}")
        
        # Calculate errors
        pos_error_orig = np.linalg.norm(pose1['tvec'] - pose2['tvec'])
        pos_error_trans = np.linalg.norm(pose1_transformed['tvec'] - pose2['tvec'])
        
        print("\nErrors:")
        print(f"Position error before transform: {pos_error_orig:.6f}")
        print(f"Position error after transform:  {pos_error_trans:.6f}")
        print("-" * 80)

if __name__ == "__main__":
    main()