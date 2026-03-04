#!/bin/bash

python create_rosbag_sync.py --rosbag_path ${DATASET_DIR}/immesh.bag --rosbag_images ${DATASET_DIR}/scene.bag --images_colmap ${DATASET_DIR}/sparse_no_referenced/images.txt && \
python merge_rosbags.py && \
evo_traj bag trajectory_sync/merged_path.bag /colmap_path --ref /immesh_path --t_max_diff 0.05 -as -v --plot > trajectory_sync/evo.log && \
python get_transform_from_evo.py && \
python apply_transform_colmap.py --input ${DATASET_DIR}/sparse_no_referenced --output ${DATASET_DIR}/sparse