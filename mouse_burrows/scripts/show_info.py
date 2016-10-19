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

from mouse_burrows.simple import load_result_file



def get_info(result_file, parameters=False):
    """ show information about an analyzed antfarm video
    
    `result_file` is the file where the results from the video analysis are
        stored. This is usually a *.yaml file
    `parameters` is a flag that indicates whether the parameters of the result
        file are shown
    """
    # load the respective result file 
    analyzer = load_result_file(result_file)

    info = {}

    if parameters:
        info['Parameters'] = analyzer.params.to_dict()
        
    return info
    


def main(): 
    """ main routine of the script """
    # setup the argument parsing
    parser = argparse.ArgumentParser(
         description='Program that outputs information about the analysis of '
                     'antfarm processing.',
         formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-r', '--result_file', metavar='FILE',
                        type=str, required=True,
                        help='filename of video analysis result')
    parser.add_argument('-p', '--parameters', action='store_true',
                        help='show all parameters')
    

    # fetch the arguments and build the parameter list
    args = parser.parse_args()
    
    # obtain information from data
    info = get_info(result_file=args.result_file, parameters=args.parameters)
    
    # TODO: add other output methods, like json, yaml, python dict
    from pprint import pprint
    pprint(info)
    


if __name__ == '__main__':
    main()
    
    
