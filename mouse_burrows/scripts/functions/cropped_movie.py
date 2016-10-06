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
from video.filters import FilterCrop, FilterDropFrames
from video.io import VideoComposer
from video.analysis.shapes import Rectangle



def make_cropped_video(result_file, output_video=None,
                       display='{time} [{frame}]', scale_bar=True,
                       border_buffer_cm=0, frame_compression=1,
                       time_duration=None):
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
    `border_buffer_cm` sets the extra space (in units of cm) around the cropping
        rectangle that is included in the analysis
    `frame_compression` sets the compression factor that determines how many
        frames are dropped compared to the original video
    `time_duration` sets the maximal number of seconds the video is supposed to
        last. Additional frames will not be written.
    """
    logging.info('Analyze video `%s`', result_file)
    
    # load the respective result file 
    analyzer = load_result_file(result_file)

    # load the full original video
    video_info = analyzer.load_video(frames=(0, None))
    
    # crop the video to the cage
    video_input = analyzer.video
    cropping_cage = analyzer.data['pass1/video/cropping_cage']
    
    border_buffer_px = int(border_buffer_cm / analyzer.length_scale_mag)
    
    # change rectangle size if necessary
    if border_buffer_px != 0:
        cropping_rect = Rectangle.from_list(cropping_cage)
        video_rect = Rectangle(0, 0, video_input.width, video_input.height)
        
        cropping_rect.buffer(border_buffer_px)
        cropping_rect.intersect(video_rect)
        cropping_cage = cropping_rect.to_list()
    
    if cropping_cage:
        # size_alignment=2 makes sure that the width and height are even numbers 
        video_input = FilterCrop(video_input, rect=cropping_cage,
                                 size_alignment=2)
        
    if frame_compression is not None and frame_compression != 1:
        video_input = FilterDropFrames(video_input,
                                       compression=frame_compression)
        
    if time_duration is not None:
        index_max = int(time_duration * video_input.fps)
        video_input = video_input[:index_max]
    
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
        