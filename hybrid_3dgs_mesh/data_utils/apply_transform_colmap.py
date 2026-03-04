import os
import numpy as np
import json
import tf.transformations as tr
from copy import copy
import argparse

class Reconstruction:
    def __init__(self):
        self.cameras = {}
        self.images = {}
        self.points3D = {}

    def read_text(self, path):
        self.cameras.clear()
        self.images.clear()
        self.points3D.clear()
        self.read_cameras_text(os.path.join(path, "cameras.txt"))
        self.read_images_text(os.path.join(path, "images.txt"))
        self.read_points3D_text(os.path.join(path, "points3D.txt"))

    def read_cameras_text(self, filepath):
        with open(filepath, 'r') as file:
            for line in file:
                if line.startswith('#'):
                    continue
                parts = line.strip().split()
                camera_id = int(parts[0])
                model = parts[1]
                width = int(parts[2])
                height = int(parts[3])
                params = list(map(float, parts[4:]))
                self.cameras[camera_id] = {
                    'model': model,
                    'width': width,
                    'height': height,
                    'params': params
                }

    def read_images_text(self, filepath):
        with open(filepath, 'r') as file:
            for i,line in enumerate(file):
                if line.startswith('#'):
                    continue
                if i%2==0:
                    parts = line.strip().split()
                    image_id = int(parts[0])
                    qvec = list(map(float, parts[1:5]))
                    qvec = [qvec[1], qvec[2], qvec[3], qvec[0]]
                    tvec = list(map(float, parts[5:8]))
                    camera_id = int(parts[8])
                    name = parts[9]
                else:
                    parts = line.strip().split()
                    xys = []
                    point3D_ids = []
                    for i in range(0,len(parts), 3):
                        xys.append((float(parts[i]), float(parts[i+1])))
                        point3D_ids.append(int(parts[i+2]))

                    self.images[image_id] = {
                        'qvec': qvec,
                        'tvec': tvec,
                        'camera_id': camera_id,
                        'name': name,
                        'xys': xys,
                        'point3D_ids': point3D_ids,
                        'save': True
                    }

    def read_points3D_text(self, filepath):
        with open(filepath, 'r') as file:
            for line in file:
                if line.startswith('#'):
                    continue
                parts = line.strip().split()
                point3D_id = int(parts[0])
                xyz = list(map(float, parts[1:4]))
                rgb = list(map(int, parts[4:7]))
                error = float(parts[7])
                track = []
                for i in range(8, len(parts), 2):
                    track.append((int(parts[i]), int(parts[i+1])))
                self.points3D[point3D_id] = {
                    'xyz': xyz,
                    'rgb': rgb,
                    'error': error,
                    'track': track
                }
    def transform(self, new_from_old_world):
        for image_id, image in self.images.items():
            if self.has_pose(image):
                self.set_cam_from_world(image, self.transform_camera_world(new_from_old_world, self.get_cam_from_world(image)))
        for point3D_id, point3D in self.points3D.items():
            point3D['xyz'] = new_from_old_world["scale"]*(new_from_old_world["rotation"] @ np.array(point3D['xyz'])) + new_from_old_world["translation"]

    def has_pose(self, image):
        return 'qvec' in image and 'tvec' in image

    def get_cam_from_world(self, image):
        transform={}
        transform["rotation"] = tr.quaternion_matrix(np.array(image['qvec']))[:3,:3]
        transform["translation"] = np.array(image['tvec'])
        transform["translation"] = np.matmul(-transform["rotation"].transpose(),transform["translation"])
        transform["rotation"]=transform["rotation"].transpose()
        return transform

    def set_cam_from_world(self, image, cam_from_world):
        image['qvec'] = tr.quaternion_from_matrix(cam_from_world["rotation"])
        image['tvec'] = cam_from_world["translation"]

    def transform_camera_world(self, new_from_old_world, cam_from_world):
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
    
    def write_text(self, path):
        self.write_cameras_text(os.path.join(path, "cameras.txt"))
        self.write_images_text(os.path.join(path, "images.txt"))
        self.write_points3D_text(os.path.join(path, "points3D.txt"))

    def write_cameras_text(self, filepath):
        with open(filepath, 'w') as file:
            file.write("# Camera list with one line of data per camera:\n")
            file.write("#   CAMERA_ID, MODEL, WIDTH, HEIGHT, PARAMS[]\n")
            file.write(f"# Number of cameras: {len(self.cameras)}\n")
            for camera_id, camera in self.cameras.items():
                params = ' '.join(map(str, camera['params']))
                file.write(f"{camera_id} {camera['model']} {camera['width']} {camera['height']} {params}\n")

    def write_images_text(self, filepath):
        with open(filepath, 'w') as file:
            file.write("# Image list with two lines of data per image:\n")
            file.write("#   IMAGE_ID, QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID, NAME\n")
            file.write("#   POINTS2D[] as (X, Y, POINT3D_ID)\n#\n")
            for image_id, image in self.images.items():
                if not image["save"]: continue
                image["qvec"] = [image["qvec"][3],image["qvec"][0],image["qvec"][1],image["qvec"][2]]
                qvec = ' '.join(map(str, image['qvec']))
                tvec = ' '.join(map(str, image['tvec']))
                xys = ' '.join(f"{xy[0]} {xy[1]} {point3D_id}" for xy, point3D_id in zip(image['xys'], image['point3D_ids']))
                file.write(f"{image_id} {qvec} {tvec} {image['camera_id']} {image['name']}\n{xys}\n")

    def write_points3D_text(self, filepath):
        with open(filepath, 'w') as file:
            file.write("# 3D point list with one line of data per point:\n")
            file.write("#   POINT3D_ID, X, Y, Z, R, G, B, ERROR, TRACK[] as (IMAGE_ID, POINT2D_IDX)\n")
            for point3D_id, point3D in self.points3D.items():
                xyz = ' '.join(map(str, point3D['xyz']))
                rgb = ' '.join(map(str, point3D['rgb']))
                track = ' '.join(f"{track_el[0]} {track_el[1]}" for track_el in point3D['track'])
                file.write(f"{point3D_id} {xyz} {rgb} {point3D['error']} {track}\n")

    
def readTransform(path):
    transform={}
    with open(path, 'r') as file:
        data = json.load(file)
        transform["translation"]=np.array([data["x"],data["y"],data["z"]])
        quat = np.array([data["qx"],data["qy"],data["qz"],data["qw"]])
        transform["rotation"]=tr.quaternion_matrix(quat)[:3,:3]
        transform["scale"]=data["scale"]
        return transform
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Prepare data for NefStudio from rosbag and optimized poses')

    parser.add_argument('--input', type=str,required=True,
                        help='Input sparse model folder')
    parser.add_argument('--output', type=str,required=True,
                        help='Output sparse model folder')
    parser.add_argument('--pose_prior', type=str,default=None,
                        help='Path to pose prior file. If set, discard incorrect poses.')
    parser.add_argument('--max_distance', type=float,default=1.5,
                        help='Max distance between the pose and the pose prior to consider it correct.')

    args = parser.parse_args()

    reconstruction = Reconstruction()
    reconstruction.read_text(args.input)
    transform = readTransform('trajectory_sync/transform.json')
    reconstruction.transform(transform)

    #Pose refinement
    image_id = 1
    if args.pose_prior is not None:
        with open(args.pose_prior, 'r') as file:
            data = file.readlines()
            for line in data:
                line = line.strip().split()
                image_name = line[0]
                pose = np.array(list(map(float, line[1:])))              
                while image_id not in reconstruction.images and reconstruction.images[image_id]["name"]!=image_name:
                    image_id+=1
                    if image_id>=len(reconstruction.images):
                        print("Image not found")
                        exit(0)
               
                transform = reconstruction.get_cam_from_world(reconstruction.images[image_id])
                if np.linalg.norm(transform["translation"]-pose)>args.max_distance:
                    print(f"Pose {image_id} is incorrect")
                    reconstruction.images[image_id]["save"] = False
                image_id+=1
    reconstruction.write_text(args.output)