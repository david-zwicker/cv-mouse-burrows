#!/usr/bin/env python2
'''
Created on Sep 21, 2016

@author: David Zwicker <dzwicker@seas.harvard.edu>
'''

from __future__ import division

import argparse
import sys
import os

# add the root of the video-analysis project to the path
script_path = os.path.split(os.path.realpath(__file__))[0]
package_path = os.path.abspath(os.path.join(script_path, '..', '..'))
sys.path.append(package_path)

video_analysis_path_guess = os.path.join(package_path, '..', 'video-analysis')
sys.path.append(os.path.abspath(video_analysis_path_guess))

from mouse_burrows.scripts.functions.cropped_movie import make_cropped_video



def main(): 
    """ main routine of the script """
    # setup the argument parsing
    parser = argparse.ArgumentParser(
         description='Program that reads an antfarm video and the associated '
                     'data from the video analysis to crop the video to the '
                     'antfarm.',
         formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-r', '--result_file', metavar='FILE',
                        type=str, required=True,
                        help='filename of video analysis result')
    parser.add_argument('-o', '--output_file', metavar='FILE',
                        type=str, default=None,
                        help='filename of the output video [optional]')
    parser.add_argument('-d', '--display', type=str, default='{time}',
                        help='information that is displayed')
    parser.add_argument('-s', '--scale_bar', action='store_true', default=False,
                        help='displays a scale bar in the video')
    parser.add_argument('-b', '--border_buffer', metavar='CM',
                        type=float, default=0,
                        help='enlarge the cropping rectangle by the given '
                             'length (in cm) in all directions.')
    parser.add_argument('-c', '--frame_compression', metavar='FACTOR',
                        type=float, default=1,
                        help='factor that determines how many frames are '
                             'dropped to compress video')
    parser.add_argument('-t', '--time_duration', metavar='SECONDS',
                        type=float, default=-1,
                        help='maximal number of seconds the produced video is '
                             'going to cover. Negative inputs indicate that '
                             'the full video is used.')
    parser.add_argument('-p', '--progress', action='store_true',
                        help='Displays progress')
    
    # fetch the arguments and build the parameter list
    args = parser.parse_args()
    
    time_duration = args.time_duration
    if time_duration < 0:
        time_duration = None
    
    # create the video
    make_cropped_video(result_file=args.result_file,
                       output_video=args.output_file,
                       display=args.display, scale_bar=args.scale_bar,
                       border_buffer_cm=args.border_buffer,
                       frame_compression=args.frame_compression,
                       time_duration=time_duration,
                       progress=args.progress)
    


if __name__ == '__main__':
    main()
    
    
