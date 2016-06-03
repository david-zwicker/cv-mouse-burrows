#!/bin/bash

#SBATCH -n {PASS2/CORES}     # Number of cores
#SBATCH -N 1                 # Ensure that all cores are on one machine
#SBATCH -t {PASS2/TIME}      # Runtime in minutes
#SBATCH -p {SLURM_PARTITION} # Partition to submit to
#SBATCH --mem-per-cpu={PASS2/MEMORY} # Memory per cpu in MB (see also --mem)
#SBATCH -o {JOB_DIRECTORY}/log_pass2_%j.txt    # File to which stdout and stderr will be written
#SBATCH --job-name=P2_{NAME}
#SBATCH --mail-type=FAIL
#SBATCH --mail-user={NOTIFICATION_EMAIL}

hostname

echo "Start job with id $SLURM_JOB_ID"
echo $SLURM_JOB_ID >> pass2_job_id.txt

# increase process limit, because ffmpeg needs many threads
#ulimit -u 2048

# load python environment
source ~/.profile
# change to job directory
cd {JOB_DIRECTORY}
# run python script
python {JOB_FILE_1} $SLURM_JOB_ID

echo "Ended job with id $SLURM_JOB_ID"
