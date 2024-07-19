#!/bin/sh
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --time=40:00:00
#SBATCH --gres=gpu:a40:4
#SBATCH --mem=400GB
#SBATCH --cpus-per-gpu=10
#SBATCH --partition=isi

source /home1/spangher/.bashrc
conda activate vllm-py310
python match_songs_in_index.py \
  --input quantized-performance-embedding-matches.jsonl \
  --output_file vllm-performance-matches.jsonl \
  --matching_process llm