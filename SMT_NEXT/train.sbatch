#!/bin/bash
#SBATCH -N 1
#SBATCH --cpus-per-task=128
#SBATCH --gres=gpu:4
#SBATCH --partition=sched_mit_psfc_gpu_r8
#SBATCH --job-name=train_job
#SBATCH --output=output_%j.txt
#SBATCH --error=error_%j.txt


conda activate sheet-music-main
srun python train.py