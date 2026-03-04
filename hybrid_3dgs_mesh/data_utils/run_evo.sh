scenes=("/home/alolivas/aurova-lab/labrobotica/dataset/3DGaussianSplatting/scientific_park_scene1" "/home/alolivas/aurova-lab/labrobotica/dataset/3DGaussianSplatting/scientific_park_scene2" "/home/alolivas/aurova-lab/labrobotica/dataset/3DGaussianSplatting/scientific_park_scene3" "/home/alolivas/aurova-lab/labrobotica/dataset/3DGaussianSplatting/scientific_park_scene4")
for scene in "${scenes[@]}"; do
    DATASET_DIR=$scene
    python create_rosbag_sync.py --rosbag_path ${DATASET_DIR}/immesh.bag --rosbag_images ${DATASET_DIR}/scene.bag --images_colmap ${DATASET_DIR}/sparse_no_referenced/images.txt
    python merge_rosbags.py
    evo_ape bag trajectory_sync/merged_path.bag /colmap_path /immesh_path --t_max_diff 0.05 -as -v
done
