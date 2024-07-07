#!/bin/sh
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --time=40:00:00
#SBATCH --mem=100GB
#SBATCH --cpus-per-task=10
#SBATCH --partition=main

# module purge
# eval "$(conda shell.bash hook)"
# mamba activate music-research
python yt-aria.py \
    --input_json youtube-links__10-6.jsonl \
    --sleep-time 10 \
    --proxy-file proxies.txt \
    --proxy-type socks5 \
    --download
#    --end-idx 40_000 \
#    --score-threshold 0