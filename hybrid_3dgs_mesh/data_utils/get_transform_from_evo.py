import json
import numpy as np
from scipy.spatial.transform import Rotation as R

# Function to read the transformation alignment from the log file
def read_transformation_from_log(log_file_path):
    with open(log_file_path, 'r') as log_file:
        lines = log_file.readlines()
    
    # Extract the rotation matrix and translation vector from the log
    rotation_matrix = []
    translation_vector = []
    scale_correction = None
    
    for i, line in enumerate(lines):
        if "Rotation of alignment:" in line:
            rotation_matrix = [
                list(map(float, lines[i+1].strip().strip('[]').split())),
                list(map(float, lines[i+2].strip().strip('[]').split())),
                list(map(float, lines[i+3].strip().strip('[]').split()))
            ]
        if "Translation of alignment:" in line:
            translation_vector = list(map(float, lines[i+1].strip().strip('[]').split()))
        if "Scale correction:" in line:
            scale_correction = float(line.split(':')[1].strip())
    
    return np.array(rotation_matrix), np.array(translation_vector), scale_correction

# Read the transformation alignment from the log file
log_file_path = 'trajectory_sync/evo.log'
rotation_matrix, translation_vector, scale_correction = read_transformation_from_log(log_file_path)

# Convert rotation matrix to quaternion
rotation = R.from_matrix(rotation_matrix)
quaternion = rotation.as_quat()  # Returns in the order (x, y, z, w)

# Create the transformation dictionary
transformation = {
    "x": translation_vector[0],
    "y": translation_vector[1],
    "z": translation_vector[2],
    "qx": quaternion[0],
    "qy": quaternion[1],
    "qz": quaternion[2],
    "qw": quaternion[3],
    "scale": scale_correction
}

# Save the transformation to transform.json
with open('trajectory_sync/transform.json', 'w') as json_file:
    json.dump(transformation, json_file, indent=4)

print("Transformation saved to transform.json")