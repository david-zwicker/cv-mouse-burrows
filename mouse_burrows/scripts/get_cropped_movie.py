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
    parser.add_argument('-b', '--border_buffer', type=float, default=0,
                        help='enlarge the cropping rectangle by the given '
                             'length (in cm) in all directions.')
    
    # fetch the arguments and build the parameter list
    args = parser.parse_args()
    
    # create the video
    make_cropped_video(result_file=args.result_file,
                       output_video=args.output_file,
                       display=args.display, scale_bar=args.scale_bar,
                       border_buffer_cm=args.border_buffer)
    


if __name__ == '__main__':
    main()
    
    
