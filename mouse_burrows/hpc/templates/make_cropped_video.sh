#!/bin/bash

#SBATCH -n {PASS7/CORES}     # Number of cores
#SBATCH -N 1                 # Ensure that all cores are on one machine
#SBATCH -t {PASS7/TIME}      # Runtime in minutes
#SBATCH -p {SLURM_PARTITION} # Partition to submit to
#SBATCH --mem-per-cpu={PASS7/MEMORY}   # Memory per cpu in MB (see also --mem)
#SBATCH -o {JOB_DIRECTORY}/log_cropped_video_%j.txt    # File to which stdout and stderr will be written
#SBATCH --job-name=V_{NAME}
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
    --display="{VIDEO_DISPLAY_ITEM}" \
    --border_buffer="{VIDEO_CROP_BORDER_BUFFER}" \ 
    --time_compression="{VIDEO_CROP_TIME_COMPRESSION}" \
    --time_duration="{VIDEO_CROP_TIME_DURATION}"

echo "Ended job with id $SLURM_JOB_ID"
