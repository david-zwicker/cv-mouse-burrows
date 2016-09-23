#!/usr/bin/env python2
'''
Created on Oct 18, 2015

@author: David Zwicker <dzwicker@seas.harvard.edu>
'''

from __future__ import division

import datetime
import logging

import numpy as np

from ...simple import load_result_file
from video.filters import FilterCrop
from video.io import VideoComposer
from video.analysis.shapes import Rectangle



def make_cropped_video(result_file, output_video=None,
                           display='{time} [{frame}]', scale_bar=True):
    """ main routine of the program
    `result_file` is the file where the results from the video analysis are
        stored. This is usually a *.yaml file
    `output_video` denotes the filename where the result video should be
        written to.
    `display` determines what information is displayed. There are several
        variables that would be replaced by data:
            {time} the current time stamp
            {frame} the current frame number
    `scale_bar` determines whether a scale bar is shown
    """
    logging.info('Analyze video `%s`', result_file)
    
    # load the respective result file 
    analyzer = load_result_file(result_file)

    # load the full original video
    video_info = analyzer.load_video(frames=(0, None))
    
    # crop the video to the cage
    video_input = analyzer.video
    cropping_cage = analyzer.data['pass1/video/cropping_cage']
    if cropping_cage:
        video_input = FilterCrop(video_input, rect=cropping_cage)
    
    # determine the filename of the output video
    if output_video is None:
        # determine the complete filename automatically
        movie_ext = analyzer.params['output/video/extension']
        filename = 'cropped'
        output_video = analyzer.get_filename(filename + movie_ext, 'video')
        
    elif '.' not in output_video:
        # determine the extension automatically
        movie_ext = analyzer.params['output/video/extension']
        output_video = output_video + movie_ext
    
    logging.info('Write output to `%s`', output_video)
    
    # create the video writer
    video_codec = analyzer.params['output/video/codec']
    video_bitrate = analyzer.params['output/video/bitrate']
    fps = video_input.fps
    video_output = VideoComposer(
        output_video, size=video_input.size, fps=fps, is_color=False,
        codec=video_codec, bitrate=video_bitrate,
    )
    
    # time label position
    label_pos = video_input.width // 2, 30

    # calculate size of scale bar and the position of its label
    pixel_size_cm = analyzer.data['pass2/pixel_size_cm']
    scale_bar_size_cm = 10
    scale_bar_size_px = np.round(scale_bar_size_cm / pixel_size_cm)
    scale_bar_rect = Rectangle(30, 50, scale_bar_size_px, 5)
    scale_bar_pos = (30 + scale_bar_size_px//2, 30)
    
    for frame_id, frame in enumerate(video_input):
        video_output.set_frame(frame, copy=True)

        if scale_bar:
            # show a scale bar
            video_output.add_rectangle(scale_bar_rect, width=-1)
            video_output.add_text(str('%g cm' % scale_bar_size_cm),
                                  scale_bar_pos, color='w',
                                  anchor='upper center')

        # gather data about this frame
        frame_data = {'frame': frame_id}
        
        # calculate time stamp
        time_secs, time_frac = divmod(frame_id, fps)
        time_msecs = int(1000 * time_frac / fps)
        dt = datetime.timedelta(seconds=time_secs,
                                milliseconds=time_msecs)
        frame_data['time'] = str(dt)
            
        # output the display data
        if display:
            display_text = display.format(**frame_data)
            video_output.add_text(display_text, label_pos, color='w',
                                  anchor='upper center')

    # show summary
    frames_total = video_info['frames'][1] - video_info['frames'][0]
    frames_written = video_output.frames_written
    logging.info('%d (%d%%) of %d frames written', frames_written,
                 100 * frames_written // frames_total, frames_total)
    
    # close and finalize video
    try:
        video_output.close()
    except IOError:
        logging.exception('Error while writing out the debug video `%s`',
                          video_output)
        