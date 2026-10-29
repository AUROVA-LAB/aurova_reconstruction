#!/bin/bash

cd /workspace/data && \
mkdir -p camera_calibration/rectified && \
cp -r images/ camera_calibration/rectified/ && \
cp -r sparse/ camera_calibration/rectified/ && \
cd /workspace/submodules/hierarchical-3d-gaussians/ && \
python preprocess/auto_reorient.py --input_path /workspace/data/camera_calibration/rectified/sparse/0 --output_path /workspace/data/${NAME}/camera_calibration/aligned/sparse/0 && \
python3.12 preprocess/generate_chunks.py --project_dir /workspace/data && \
python3.12 preprocess/generate_depth.py --project_dir /workspace/data && \
DATE=$(date "+%y_%m_%d_%H_%M") && \
python3.12 scripts/full_train.py --project_dir /workspace/data --output_dir /workspace/outputs/${NAME}/hierarchical/${DATE}