#!/bin/bash

#SBATCH -n {PASS3/CORES}     # Number of cores
#SBATCH -N 1                 # Ensure that all cores are on one machine
#SBATCH -t {PASS3/TIME}      # Runtime in minutes
#SBATCH -p {SLURM_PARTITION} # Partition to submit to
#SBATCH --mem-per-cpu={PASS3/MEMORY} # Memory per cpu in MB (see also --mem)
#SBATCH -o {JOB_DIRECTORY}/log_pass3_%j.txt    # File to which stdout and stderr will be written
#SBATCH --job-name=P3_{NAME}
#SBATCH --mail-type=FAIL
#SBATCH --mail-user={NOTIFICATION_EMAIL}

echo "Start job with id $SLURM_JOB_ID"
echo $SLURM_JOB_ID >> pass3_job_id.txt

# copy video to temporary location if necessary
mkdir -p {VIDEO_FOLDER_TEMPORARY}
rsync -avzh --progress {VIDEO_FILE_SOURCE} {VIDEO_FOLDER_TEMPORARY}

# increase process limit, because ffmpeg needs many threads
ulimit -u 2048

# load python environment
source ~/.profile
# change to job directory
cd {JOB_DIRECTORY}
# run python script
python {JOB_FILE_1} $SLURM_JOB_ID

echo "Ended job with id $SLURM_JOB_ID"
