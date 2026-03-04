#!/bin/bash

cd /workspace && \
mkdir distorted && \
mv images distorted/images && \
mv sparse distorted/sparse && \
colmap image_undistorter --image_path distorted/images --input_path distorted/sparse/0 --output_path . --output_type COLMAP && \
mv sparse sparse_no_referenced && \
mkdir -p sparse/0 && \
chmod 777 -R sparse && \
colmap model_converter --output_path sparse_no_referenced --output_type TXT --input_path sparse_no_referenced