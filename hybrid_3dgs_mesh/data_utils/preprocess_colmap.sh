#!/bin/bash

cd /workspace && \
mkdir -m 777 colmap && \
colmap feature_extractor --database_path colmap/database.db --image_path images/ --ImageReader.camera_model OPENCV --ImageReader.single_camera 1 --SiftExtraction.peak_threshold 0.000666667 --SiftExtraction.edge_threshold 5 && \
colmap exhaustive_matcher --database_path colmap/database.db --SiftMatching.guided_matching 1 && \
mkdir -m 777 sparse && \
python /hybrid_3dgs_mesh/submodules/colmap/scripts/python/write_pose_priors_to_database.py --database_path /workspace/colmap/database.db --pose_priors_path /workspace/pose_priors.txt --coordinate_system 1