#!/bin/sh
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --time=40:00:00
#SBATCH --gres=gpu:a40:1
#SBATCH --mem=200GB
#SBATCH --cpus-per-gpu=10
#SBATCH --partition=gpu

source /home1/spangher/.bashrc
data_dir=/project/jonmay_231/spangher/Projects/music-sheet-music-modeling/DATASET/
conda activate retriv-py39
python create_index.py --data_dir $data_dir