# music-sheet-music-modeling
=======

## Quick Start

Follow these steps to connect to the MIT cluster and have access to the codebase. These instructions are for the terminal, but can be used as a reference to ssh into the cluster via VSCode, which is highly recommended. Additionally, it might be a good idea to research anaconda, how the login and compute nodes work, and the overall file system of the server.

### Step 1: Connect to the Remote Server

Use SSH to connect to the remote server where the project will run.

```sh
ssh spangher@eofe7.mit.edu
```

### Step 2: Navigate to the Project Directory

Change directory to the project's location on the remote server.

```sh
cd /pool001/spangher/music-sheet-music-modeling
```

### Step 3: Allocate Resources and Start an Interactive Session

Allocate the necessary resources (CPU, GPU) and start an interactive session. This command requests one node, 128 CPU cores, and 4 GPUs.

```sh
srun -N 1 --cpus-per-task=128 --gres=gpu:4 --partition=sched_mit_psfc_gpu_r8 --pty bash -i
```

### Step 4: Activate the Conda Environment

Activate the Conda environment that contains the dependencies required for the project.

```sh
conda activate sheet-music-main
```

### Step 5: Navigate to the SMT Directory

Change directory to SMT.

```sh
cd SMT
```

 ## Usage

If you need to clone a git repo into the main music-sheet-music-modeling repo, make sure you delete the inner .git folder to avoid nested repos. 

Be sure to keep this README up to date with any other additions or warnings.

 ## Acknowledgments

Use this space to list resources you find helpful and would like to give credit to.

- [SMT - Sheet Music Transformer]([https://github.com/ShaanCoding/ReadME-Generator](https://github.com/multiscore/SMT))
