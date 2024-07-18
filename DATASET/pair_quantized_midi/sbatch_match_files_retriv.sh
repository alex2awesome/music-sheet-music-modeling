#!/bin/sh
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --time=40:00:00
#SBATCH --gres=gpu:a40:1
#SBATCH --mem=200GB
#SBATCH --cpus-per-gpu=10
#SBATCH --partition=gpu

source /home1/spangher/.bashrc
conda activate retriv-py39
python match_songs_in_index.py \
  --quantized_input quantized-piano-to-fetch.csv \
  --output_file quantized-performance-embedding-matches.csv