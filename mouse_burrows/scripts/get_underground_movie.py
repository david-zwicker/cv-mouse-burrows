#!/usr/bin/env python2
'''
Created on Oct 18, 2015

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

from mouse_burrows.scripts.functions.underground_movie import \
                                                        make_underground_video



def main(): 
    """ main routine of the script """
    # setup the argument parsing
    parser = argparse.ArgumentParser(
         description='Program that reads an antfarm video and the associated '
                     'data from the video analysis to cut out frames where the '
                     'mouse is above ground.',
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
    parser.add_argument('-m', '--min_duration', type=float, default=60,
                        metavar='FRAMES',
                        help='minimal number of frames the mouse has to be '
                             'below ground to include the bout into the video')
    parser.add_argument('-b', '--blank_duration', type=float, default=15,
                        metavar='FRAMES',
                        help='number of blank frames inserted between bouts')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--bout-slice', type=int, nargs=2, metavar='IDX',
                       help='the range of bouts to include in the analysis')
    group.add_argument('--video_part', type=int, metavar='NR',
                       help='part of the full video that is created')
    
    # fetch the arguments and build the parameter list
    args = parser.parse_args()
    
    # prepare the bout slice argument
    if args.bout_slice:
        bout_slice = slice(*args.bout_slice)
    else:
        bout_slice = slice(None, None)
    
    # create the video
    make_underground_video(result_file=args.result_file,
                           output_video=args.output_file,
                           display=args.display, scale_bar=args.scale_bar,
                           min_duration=args.min_duration,
                           blank_duration=args.blank_duration,
                           bouts_slice=bout_slice,
                           video_part=args.video_part)
    


if __name__ == '__main__':
    main()
    
    
