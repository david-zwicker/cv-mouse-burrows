#!/bin/bash

#SBATCH -n {PASS9/CORES}     # Number of cores
#SBATCH -N 1                 # Ensure that all cores are on one machine
#SBATCH -t {PASS9/TIME}      # Runtime in minutes
#SBATCH -p {SLURM_PARTITION} # Partition to submit to
#SBATCH --mem-per-cpu={PASS9/MEMORY}   # Memory per cpu in MB (see also --mem)
#SBATCH -o {JOB_DIRECTORY}/underground_video/log_%A_%02a.txt    # File to which stdout and stderr will be written
#SBATCH --job-name=U_{NAME}_%a
#SBATCH --mail-type=FAIL
#SBATCH --mail-user={NOTIFICATION_EMAIL}

# format task id
task_id=$(printf "%0*d" 2 $SLURM_ARRAY_TASK_ID)

echo "Start job number $task_id with id $SLURM_JOB_ID"

# load python environment
source ~/.profile
# change to job directory
cd {JOB_DIRECTORY}

# run script to create underground movie
~/Code/cv-mouse-burrows/mouse_burrows/scripts/get_underground_movie.py \
    --result_file {JOB_DIRECTORY}/{NAME}_results.yaml \
    --output_file /scratch/underground_video_$task_id \
    --scale_bar \
    --video_part $SLURM_ARRAY_TASK_ID

# copy video to final destination
mv -f /scratch/underground_video_$task_id* {JOB_DIRECTORY}/underground_video/

echo "Ended job number $task_id with id $SLURM_JOB_ID"
