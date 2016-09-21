#!/bin/bash

#SBATCH -n {PASS8/CORES}     # Number of cores
#SBATCH -N 1                 # Ensure that all cores are on one machine
#SBATCH -t {PASS8/TIME}      # Runtime in minutes
#SBATCH -p {SLURM_PARTITION} # Partition to submit to
#SBATCH --mem-per-cpu={PASS8/MEMORY}   # Memory per cpu in MB (see also --mem)
#SBATCH -o {JOB_DIRECTORY}/log_underground_video_%j.txt    # File to which stdout and stderr will be written
#SBATCH --job-name=U_{NAME}
#SBATCH --mail-type=FAIL
#SBATCH --mail-user={NOTIFICATION_EMAIL}

hostname

echo "Start job with id $SLURM_JOB_ID"

# load python environment
source ~/.profile
# change to job directory
cd {JOB_DIRECTORY}
# run script to create underground movie
~/Code/cv-mouse-burrows/mouse_burrows/scripts/get_cropped_movie.py \
    --result_file {JOB_DIRECTORY}/{NAME}_results.yaml \
    --display "{VIDEO_DISPLAY_ITEM}" \

echo "Ended job with id $SLURM_JOB_ID"
