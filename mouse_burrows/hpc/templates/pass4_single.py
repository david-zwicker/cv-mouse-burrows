#!/usr/bin/env python2

from __future__ import division

import sys
import logging
{ADD_PYTHON_PATHS}  # @UndefinedVariable
    
from numpy import array  # @UnusedImport

from mouse_burrows.algorithm.pass4 import FourthPass
from mouse_burrows.hpc.project import process_trials
from video.io.backend_ffmpeg import FFmpegError 

# configure basic logging, which will be overwritten later
logging.basicConfig()

# set specific parameters for this job
parameters = {SPECIFIC_PARAMETERS}  # @UndefinedVariable

# set job parameters
job_id = sys.argv[1]
parameters.update({{
    'base_folder': "{JOB_DIRECTORY}",
    'logging/folder': ".",
    'output/folder': ".",
    'resources/pass3/job_id': job_id,
}})

# do the second pass scan
for trial in process_trials("{LOG_FILE}" % job_id, 10):
    try:
        pass4 = FourthPass("{NAME}", parameters=parameters, read_data=True)
        pass4.process()
    except FFmpegError:
        print('FFmpeg error occurred. Continue.')
