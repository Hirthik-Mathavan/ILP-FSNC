#!/bin/bash
 
#SBATCH -n 24                        # number of cores
#SBATCH -t 99:00:00                  # wall time (D-HH:MM)
##SBATCH -A hmathava             # Account hours will be pulled from (commented out with double # in front)
#SBATCH -o slurm.%j.out             # STDOUT (%j = JobId)
#SBATCH -e slurm.%j.err             # STDERR (%j = JobId)
#SBATCH --mail-type=ALL             # Send a notification when the job starts, stops, or fails
#SBATCH --mail-user=hmathava@asu.edu # send-to address 
#SBATCH --mem=16G                    # amount of RAM requested in GiB (2^40)
#SBATCH -p publicgpu                      # Use gpu partition
#SBATCH -q wildfire                 # Run job under wildfire QOS queue
#SBATCH --gres=gpu:1                # Request two GPUs
module purge    # Always purge modules to ensure a consistent environment

module load anaconda/py3
module load cuda/10.2.89
source activate amm_gnn_py38

python train_AMM_ILP.py
