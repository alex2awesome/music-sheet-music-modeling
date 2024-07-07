#!/bin/sh
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --time=160:00:00
#SBATCH --gres=gpu:1
#SBATCH --mem-per-gpu=100GB
#SBATCH --cpus-per-gpu=10
#SBATCH --partition=isi

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