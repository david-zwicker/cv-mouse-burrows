'''
Created on Oct 2, 2014

@author: David Zwicker <dzwicker@seas.harvard.edu>

Module that contains the class responsible for the third pass of the algorithm
'''

from __future__ import division

import csv
# import math
import time

import cv2
import numpy as np
from scipy import cluster 
from shapely import geometry, geos

from .pass_base import PassBase
from .objects import mouse
from .objects.burrow import Burrow, BurrowTrack, BurrowTrackList
from utils.math import contiguous_int_regions_iter
from utils.misc import display_progress
from video.analysis import curves, regions
from video.filters import FilterCrop
from video.io import ImageWindow, VideoComposer

from video import debug  # @UnusedImport



class ThirdPass(PassBase):
    """ class containing methods for the third pass, which locates burrows
    based on the mouse movement """
    pass_name = 'pass3'
    
    
    def __init__(self, name='', parameters=None, **kwargs):
        super(ThirdPass, self).__init__(name, parameters, **kwargs)
        if kwargs.get('initialize_parameters', True):
            self.log_event('Pass 3 - Initialized the third pass analysis.')
        

    @classmethod
    def from_second_pass(cls, second_pass):
        """ create the object directly from the second pass """
        # create the data and copy the data from first_pass
        obj = cls(second_pass.name, initialize_parameters=False)
        obj.data = second_pass.data
        obj.params = obj.data['parameters']
        obj.result = obj.data.create_child('pass3')

        # close logging handlers and other files        
        second_pass.close()
        
        # initialize parameters
        obj.initialize_parameters()
        obj.initialize_pass()
        obj.log_event('Pass 3 - Initialized the third pass analysis.')
        return obj
    
    
    def process(self):
        """ processes the entire video """
        self.log_event('Pass 3 - Started initializing the video analysis.')
        self.set_pass_status(state='started')
        
        self.setup_processing()
        self.debug_setup()
        
        self.log_event('Pass 3 - Started iterating through the video with '
                       '%d frames.' % self.video.frame_count)
        self.set_status('Initialized video analysis')
        start_time = time.time()            
        
        try:
            # skip the first _frame, since it has already been analyzed
            self._iterate_over_video(self.video)
                
        except (KeyboardInterrupt, SystemExit):
            # abort the video analysis
            self.video.abort_iteration()
            self.log_event('Pass 3 - Analysis run has been interrupted.')
            self.set_status('Partly finished third pass')
            
        else:
            # finished analysis successfully
            self.log_event('Pass 3 - Finished iterating through the frames.')
            self.set_status('Finished third pass')
            
        finally:
            # cleanup in all cases 
            self.add_processing_statistics(time.time() - start_time)        

            # check how successful we finished
            self.set_pass_status(**self.get_pass_state(self.data))
                        
            # cleanup and write out of data
            self.video.close()
            self.debug_finalize()
            self.write_data()

            
    def add_processing_statistics(self, time):
        """ add some extra statistics to the results """
        frames_analyzed = self.frame_id + 1
        self.data['pass3/video/frames_analyzed'] = frames_analyzed
        self.result['statistics/processing_time'] = time
        self.result['statistics/processing_fps'] = frames_analyzed/time


    def setup_processing(self):
        """ sets up the processing of the video by initializing caches etc """
        # load the video
        cropping_rect = self.data['pass1/video/cropping_rect'] 
        # skip the first _frame, since it has also been skipped in pass 1
        video_info = self.load_video(cropping_rect=cropping_rect,
                                     frames_skipped_in_this_pass=1)
        
        self.data.create_child('pass3/video', video_info)
        del self.data['pass3/video/filecount']
        
        cropping_cage = self.data['pass1/video/cropping_cage']
        if cropping_cage is not None:
            self.video = FilterCrop(self.video, rect=cropping_cage)
            
        video_info = self.data['pass3/video']
        video_info['cropping_cage'] = cropping_cage
        video_info['frame_count'] = self.video.frame_count
        video_info['size'] = '%d x %d' % tuple(self.video.size),
                
        # initialize data structures
        self.frame_id = -1
        self.background = self.video[0].astype(np.double)
        self.ground_idx = None  #< index of the ground point where the mouse entered the burrow
        self.mouse_trail = None #< line from this point to the mouse (along the burrow)
        self.burrows = []       #< list of current burrows
        self._cache = {}

        # set up parameters
        moving_threshold = self.params['mouse/moving_threshold_cm_sec']
        moving_threshold /= video_info['fps']
        moving_threshold /= self.data['pass2/pixel_size_cm']
        self.params['mouse/moving_threshold_pixel_frame'] = moving_threshold

        # calculate mouse velocities    
        sigma = self.params['tracking/position_smoothing_window']
        self.data['pass2/mouse_trajectory'].calculate_velocities(sigma=sigma)
        
        if self.params['burrows/enabled_pass3']:
            self.result['burrows/tracks'] = BurrowTrackList()

        
    def _iterate_over_video(self, video):
        """ internal function doing the heavy lifting by iterating over the video """
        
        # load data from previous passes
        mouse_track = self.data['pass2/mouse_trajectory']
        ground_profile = self.data['pass2/ground_profile']
        frame_offset = self.result['video/frames'][0]
        if frame_offset is None:
            frame_offset = 0

        # iterate over the video and analyze it
        for self.frame_id, frame in enumerate(display_progress(video),
                                              frame_offset):
            
            # adapt the background to current _frame 
            adaptation_rate = self.params['background/adaptation_rate']
            self.background += adaptation_rate*(frame - self.background)
            
            # copy _frame to debug video
            if 'video' in self.debug:
                self.debug['video'].set_frame(frame, copy=False)
            
            # retrieve data for current _frame
            try:
                self.mouse_pos = mouse_track.pos[self.frame_id, :]
            except IndexError:
                # Sometimes the mouse trail has not been calculated till the end
                self.mouse_pos = (np.nan, np.nan)
            self.ground = ground_profile.get_ground_profile(self.frame_id)

            if self.params['burrows/enabled_pass3']:
                # find the burrow from the mouse trail
                self.find_burrows()

            # find out where the mouse currently is
            self.classify_mouse_state(mouse_track)
            
            # store some information in the debug dictionary
            self.debug_process_frame(frame, mouse_track)


    def write_mouse_state(self):
        """ write out the mouse state as a comma separated value file """
        mouse_state = self.data['pass2/mouse_trajectory'].states
        mouse_state_file = self.get_filename('mouse_state.csv', 'results')
        with open(mouse_state_file, 'w') as fp:
            csv_file = csv.writer(fp, delimiter=',')
            
            # write header
            header = ['%s (%s)' % (name, ', '.join(states))
                      for name, states in mouse.state_converter.get_categories()]
            header.append('Duration [sec]')
            csv_file.writerow(header)
            
            # write data
            frame_duration = 1/self.result['video/fps']
            for state, start, end in contiguous_int_regions_iter(mouse_state):
                data = [c for c in mouse.state_converter.int_to_symbols(state)]
                data.append(frame_duration * (end - start)) 
                csv_file.writerow(data)


    def write_data(self):
        """ write out all the data from this pass """
        # write out the data in the usual format
        super(ThirdPass, self).write_data()
        self.write_mouse_state()


    @staticmethod
    def get_pass_state(data):
        """ check how the run went """
        problems = {}
        
        try:
            frames_analyzed = data['pass3/video/frames_analyzed']
            frame_count = data['pass3/video/frame_count']
        except KeyError:
            # data could not be loaded
            result = {'state': 'not-started'}
        else:    
            # check the number of frames that have been analyzed
            if frames_analyzed < 0.99*frame_count:
                problems['stopped_early'] = True
    
            if problems:
                result = {'state': 'error', 'problems': problems}
            else:
                result = {'state': 'done'}
            
        return result
    
    
    #===========================================================================
    # MOUSE TRACKING
    #===========================================================================


    def extend_mouse_trail(self):
        """ extends the mouse trail using the current mouse position """
        ground_line = self.ground.linestring
        
        # remove points which are in front of the mouse
        if self.mouse_trail:
            spacing = self.params['mouse/model_radius']
            trail = np.array(self.mouse_trail)
            
            # get distance between the current point and the previous ones
            dist = np.hypot(trail[:, 0] - self.mouse_pos[0],
                            trail[:, 1] - self.mouse_pos[1])
            points_close = (dist < spacing)
                
            # delete obsolete points
            if np.any(points_close):
                i = np.nonzero(points_close)[0][0]
                del self.mouse_trail[i:]
           
        # check the two ends of the mouse trail
        if self.mouse_trail:
            # move first point to ground
            ground_point = curves.get_projection_point(ground_line,
                                                       self.mouse_trail[0])
            self.mouse_trail[0] = ground_point

            # check whether a separate point needs to be inserted
            p1, p2 = self.mouse_trail[-1], self.mouse_pos
            if curves.point_distance(p1, p2) > spacing:
                mid_point = (0.5*(p1[0] + p2[0]), 0.5*(p1[1] + p2[1]))
                self.mouse_trail.append(mid_point)

            # append the current point
            self.mouse_trail.append(self.mouse_pos)
            ground_dist = curves.curve_length(self.mouse_trail)
            
        else:
            # create a mouse trail if it is not too far from the ground
            # the latter can happen, when the mouse suddenly appears underground
            ground_point = curves.get_projection_point(ground_line, self.mouse_pos)
            ground_dist = curves.point_distance(ground_point, self.mouse_pos)
            if ground_dist < self.params['mouse/speed_max']:
                self.mouse_trail = [ground_point, self.mouse_pos]

        return ground_dist


    def classify_mouse_state(self, mouse_track):
        """ classifies the mouse in the current _frame """
        if (not np.all(np.isfinite(self.mouse_pos)) or
            self.ground is None):
            
            # Not enough information to do anything
            self.mouse_trail = None
            return
        
        # initialize variables
        state = {}
        margin = self.params['mouse/model_radius']/2
        mouse_radius = self.params['mouse/model_radius']
        
        # check the horizontal position
        if self.mouse_pos[0] > self.background.shape[1]//2:
            state['position_horizontal'] = 'right'
        else:
            state['position_horizontal'] = 'left'
                
        # compare y value of mouse and ground (y-axis points down)
        if self.mouse_pos[1] > self.ground.get_y(self.mouse_pos[0]) + margin:
            # handle mouse trail
            ground_dist = self.extend_mouse_trail()
            
            # store the ground distance as a negative number 
            ground_dist *= -1 
            
            # score the burrow based on its entry point
            if self.ground_idx is None:
                # only necessary if mouse starts inside burrow
                dist = np.linalg.norm(self.ground.points - self.mouse_pos[None, :], axis=1)
                self.ground_idx = np.argmin(dist)
            entry_point = self.ground.points[self.ground_idx]
            if entry_point[1] > self.ground.midline:
                state['location'] = 'burrow'
            else:
                state['location'] = 'dimple'
                
            # check whether we are at the end of the burrow
            for burrow in self.burrows:
                dist = curves.point_distance(burrow.end_point, self.mouse_pos)
                if dist < mouse_radius:
                    state['location_detail'] = 'end point'
                    break
            else:
                state['location_detail'] = 'general'

        else: 
            if self.mouse_pos[1] + 2*mouse_radius < self.ground.get_y(self.mouse_pos[0]):
                state['location'] = 'air'
            elif self.mouse_pos[1] < self.ground.midline:
                state['location'] = 'hill'
            else:
                state['location'] = 'valley'
            state['location_detail'] = 'general'

            # get index of the ground line
            dist = np.linalg.norm(self.ground.points - self.mouse_pos[None, :], axis=1)
            self.ground_idx = np.argmin(dist)
            # get distance from ground line
            mouse_point = geometry.Point(self.mouse_pos)
            ground_dist = self.ground.linestring.distance(mouse_point)
            # report the distance as negative, if the mouse is under the ground line
            if self.mouse_pos[1] > self.ground.get_y(self.mouse_pos[0]):
                ground_dist *= -1
            
            # reset the mouse trail since the mouse is over the ground
            self.mouse_trail = None
            
        # determine whether the mouse is moving or not
        velocity = self.data['pass2/mouse_trajectory'].velocity[self.frame_id, :]
        speed = np.hypot(velocity[0], velocity[1])
        if speed > self.params['mouse/moving_threshold_pixel_frame']:
            state['dynamics'] = 'moving'
        else:
            state['dynamics'] = 'stationary'
            
        # set the mouse state
        mouse_track.set_state(self.frame_id, state, self.ground_idx, ground_dist)

    
    #===========================================================================
    # GROUND HANDELING
    #===========================================================================


    def get_ground_polygon_points(self):
        """ returns a list of points marking the ground region """
        width, height = self.video.size
        ground_points = self.ground.get_polygon_points(height, 0, width)
        return np.asarray(ground_points, np.int32)

        # create a mask for the region below the current mask_ground profile
        ground_points = np.empty((len(self.ground) + 4, 2), np.int32)
        ground_points[:-4, :] = self.ground.points
        ground_points[-4, :] = (width, ground_points[-5, 1])
        ground_points[-3, :] = (width, height)
        ground_points[-2, :] = (0, height)
        ground_points[-1, :] = (0, ground_points[0, 1])
        
        return ground_points


    def get_ground_mask(self):
        """ returns a binary mask distinguishing the ground from the sky """
        # build a mask with potential burrows
        width, height = self.video.size
        mask_ground = np.zeros((height, width), np.uint8)
        
        # create a mask for the region below the current mask_ground profile
        ground_points = self.get_ground_polygon_points()
        cv2.fillPoly(mask_ground, np.array([ground_points], np.int32), color=255)

        return mask_ground


    #===========================================================================
    # BURROW TRACKING
    #===========================================================================


#     def get_burrow_contour_from_mask(self, mask, offset=None):
#         """ creates a burrow object given a contour contour.
#         If offset=(xoffs, yoffs) is given, all the points are translate.
#         May return None if no burrow was found 
#         """
#         if offset is None:
#             offset = (0, 0)
# 
#         # find the contour of the mask    
#         contours = cv2.findContours(mask.astype(np.uint8, copy=False),
#                                     cv2.RETR_EXTERNAL,
#                                     cv2.CHAIN_APPROX_SIMPLE)[1]
#         
#         if not contours:
#             raise RuntimeError('Could not find any contour')
#         
#         # find the contour with the largest area, in case there are multiple
#         contour_areas = [cv2.contourArea(cnt) for cnt in contours]
#         contour_id = np.argmax(contour_areas)
#         
#         if contour_areas[contour_id] < self.params['burrows/area_min']:
#             # disregard small burrows
#             raise RuntimeError('Burrow is too small')
#             
#         # simplify the contour
#         contour = np.squeeze(np.asarray(contours[contour_id], np.double))
#         tolerance = self.params['burrows/outline_simplification_threshold'] \
#                         *curves.curve_length(contour)
#         contour = curves.simplify_curve(contour, tolerance).tolist()
# 
#         # move points close to the ground line onto the ground line
#         ground_point_dist = self.params['burrows/ground_point_distance']
#         ground_line = affinity.translate(self.ground.linestring,
#                                          xoff=-offset[0],
#                                          yoff=-offset[1]) 
#         for k, p in enumerate(contour):
#             point = geometry.Point(p)
#             if ground_line.distance(point) < ground_point_dist:
#                 contour[k] = curves.get_projection_point(ground_line, point)
#         
#         # simplify contour while keeping the area roughly constant
#         threshold = self.params['burrows/simplification_threshold_area']
#         contour = regions.simplify_contour(contour, threshold)
#         
#         # remove potential invalid structures from contour
#         if contour:
#             contour = regions.regularize_contour_points(contour)
#         
# #         if offset[0]:
# #             debug.show_shape(geometry.LinearRing(contour),
# #                              background=mask, wait_for_key=False)
#         
#         # create the burrow based on the contour
#         if contour:
#             contour = curves.translate_points(contour,
#                                               xoff=offset[0],
#                                               yoff=offset[1])
#             try:
#                 return contour
#             except ValueError as err:
#                 raise RuntimeError(err.message)
#             
#         else:
#             raise RuntimeError('Contour is not a simple polygon')
    
    
#     def refine_elongated_burrow_centerline(self, burrow):
#         """ refines the centerline of an elongated burrow """
#         spacing = self.params['burrows/centerline_segment_length']
#         centerline = curves.make_curve_equidistant(burrow.centerline, spacing)
#         contour = burrow.outline_ring
#         
#         # iterate over all but the boundary points
#         ray_len = 10000
# 
#         # determine the boundary points for each centerline point
# #         points = [centerline[0]]
#         dp = []
#         boundary = []
#         for k in xrange(1, len(centerline)):
#             # get local points and slopes
#             if k == len(centerline) - 1:
#                 p_p, p_m =  centerline[k-1], centerline[k]
#                 dx, dy = p_m - p_p
#             else:
#                 p_p, p_m, p_n =  centerline[k-1], centerline[k], centerline[k+1]
#                 dx, dy = p_n - p_p
#             dist = math.hypot(dx, dy)
#             if dist == 0: #< something went wrong 
#                 continue #< skip this point
#             dx /= dist; dy /= dist
# 
#             # determine the points of intersection with the burrow contour         
#             p_a = (p_m[0] - ray_len*dy, p_m[1] + ray_len*dx)
#             p_b = (p_m[0] + ray_len*dy, p_m[1] - ray_len*dx)
#             line = geometry.LineString((p_a, p_b))
#             
#             # find the intersections between the ray and the burrow contour
#             inter = regions.get_intersections(contour, line)
# 
#             if len(inter) < 2:
#                 # not enough information to proceed
#                 continue
#             
#             # find the two closest points
#             dist = [curves.point_distance(p, p_m) for p in inter]
#             k_a = np.argmin(dist)
#             p_a = inter[k_a]
#             dist[k_a] = np.inf
#             p_b = inter[np.argmin(dist)]
#             
#             # set boundary point
# #             points.append(p)
#             dp.append((-dy, dx))
#             boundary.append((p_a, p_b))
# 
# #         points = np.array(points)
#         dp = np.array(dp)
#         boundary = np.array(boundary)
# 
#         # get the points, which are neither at the exit nor the front
#         if len(boundary) == 0:
#             return
#         points = np.mean(boundary, axis=1).tolist()
#         
#         if burrow.two_exits:
#             # the burrow end point is also an exit point 
#             # => find the best approximation for this burrow exit
#             p_far = curves.get_projection_point(self.ground.linestring, points[-1])
#             points = points[:-1] + [p_far]
#             
#         else:
#             # the burrow end point is under ground
#             # => extend the centerline to the burrow front
#             angle = np.arctan2(-dp[-1][0], dp[-1][1])
#             angles = np.linspace(angle - np.pi/4, angle + np.pi/4, 32)
#             p_far, _, _ = regions.get_farthest_ray_intersection(points[-1], angles, contour)
#     
#             if p_far is not None:
#                 points = points + [p_far]
#                 if curves.point_distance(points[-1], points[-2]) < spacing:
#                     del points[-2]
#             
#         # find the best approximation for the burrow exit
#         p_near = curves.get_projection_point(self.ground.linestring, points[0])
#         points = [p_near] + points
#             
#         burrow.centerline = points
    
    
#     def refine_burrow_centerline(self, burrow):
#         """ refines the centerline of a burrow """
#         # check the percentage of contour points close to the ground
#         spacing = self.params['burrows/ground_point_distance']
#         contour = curves.make_curve_equidistant(burrow.contour, spacing)
#         groundline = self.ground.linestring
# 
#         dist_far, p_far = 0, None
#         for p in contour:
#             dist = groundline.distance(geometry.Point(p))
#             if dist > dist_far:
#                 dist_far = dist
#                 p_far = p
#                 
#         threshold_dist = self.params['burrows/shape_threshold_distance']
#         if dist_far > threshold_dist:
#             # burrow has few points close to the ground
#             self.refine_elongated_burrow_centerline(burrow)
#             burrow.elongated = True
#             
#         else:
#             # burrow is close to the ground
#             p_near = curves.get_projection_point(groundline, p_far)
#             burrow.elongated = False
#             
#             burrow.centerline = [p_near, p_far]

    
#     def refine_burrow(self, burrow):
#         """ refine burrow by thresholding background image using the GrabCut
#         algorithm """
#         mask_ground = self.get_ground_mask()
#         _frame = self.background
#         width_min = self.params['burrows/width_min']
#         
#         # get region of interest from expanded bounding rectangle
#         rect = burrow.get_bounding_rect(5*width_min)
#         # get respective slices for the image, respecting image borders 
#         (_, slices), rect = regions.get_overlapping_slices(rect[:2],
#                                                            (rect[3], rect[2]),
#                                                            _frame.shape,
#                                                            anchor='upper left',
#                                                            ret_rect=True)
#         
#         # extract the region of interest from the _frame and the mask
#         img = _frame[slices].astype(np.uint8)
#         mask_ground = mask_ground[slices]
#         mask = np.zeros_like(mask_ground)        
#         
#         centerline = curves.translate_points(burrow.centerline,
#                                              xoff=-rect[0],
#                                              yoff=-rect[1])
# 
#         spacing = self.params['burrows/centerline_segment_length']
#         centerline = curves.make_curve_equidistant(centerline, spacing) 
# 
#         if burrow.contour is not None and len(centerline) > 2:
#             centerline = geometry.LineString(centerline[:-1])
#         else:
#             centerline = geometry.LineString(centerline)
#         
#         def add_to_mask(color, buffer_radius):
#             """ adds the region around the centerline to the mask """
#             polygon = centerline.buffer(buffer_radius)
#             coords = np.asarray(polygon.exterior.xy, np.int).T 
#             cv2.fillPoly(mask, [coords], color=int(color))
# 
#         # setup the mask for the GrabCut algorithm
#         mask.fill(cv2.GC_BGD)
#         add_to_mask(cv2.GC_PR_BGD, 2*self.params['burrows/width'])
#         add_to_mask(cv2.GC_PR_FGD, self.params['burrows/width'])
#         add_to_mask(cv2.GC_FGD, self.params['burrows/width_min']/2)
# 
#         # have to convert to color image, since grabCut only supports color
#         img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
#         bgdmodel = np.zeros((1, 65), np.float64)
#         fgdmodel = np.zeros((1, 65), np.float64)
#         # run GrabCut algorithm
#         try:
#             cv2.grabCut(img, mask, (0, 0, 1, 1),
#                         bgdmodel, fgdmodel, 2, cv2.GC_INIT_WITH_MASK)
#         except:
#             # any error in the GrabCut algorithm makes the whole function useless
#             self.logger.warn('%d: GrabCut algorithm failed on burrow at %s',
#                              self.frame_id, burrow.position)
#             return burrow
# 
# #         debug.show_image(burrow_mask, ground_mask, img, 
# #                          debug.get_grabcut_image(mask),
# #                          wait_for_key=False)
# 
#         # calculate the mask of the foreground
#         mask = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0)
#         
#         # make sure that the burrow is under ground
#         mask[mask_ground == 0] = 0
#         
#         # find the burrow from the mask
#         try:
#             contour = self.get_burrow_contour_from_mask(mask.astype(np.uint8),
#                                                         offset=rect[:2])
#             burrow.contour = contour
#             self.refine_burrow_centerline(burrow)
#             burrow.refined = True
#         except RuntimeError as err:
#             self.logger.debug('%d: Invalid burrow from GrabCut: %s',
#                               self.frame_id, err.message)
#         
#         return burrow
    
    
    def active_burrows(self, time_interval=None):
        """ returns a generator to iterate over all active burrows """
        if time_interval is None:
            time_interval = self.params['burrows/adaptation_interval']
        for track_id, burrow_track in enumerate(self.result['burrows/tracks']):
            if burrow_track.track_end >= self.frame_id - time_interval:
                yield track_id, burrow_track.last


    def burrow_estimate_exit(self, burrow):
        """ estimate burrow exit points """
        
        ground_line = self.ground.linestring
        dist_max = self.params['burrows/ground_point_distance']
        
        # determine burrow points close to the ground
        exit_points = [point for point in burrow.contour
                       if ground_line.distance(geometry.Point(point)) < dist_max]

        if len(exit_points) < 2:
            return exit_points
        
        exit_points = np.array(exit_points)

        # cluster the points to detect multiple connections 
        # this is important when a burrow has multiple exits to the ground
        dist_max = self.params['burrows/width']
        data = cluster.hierarchy.fclusterdata(exit_points, dist_max,
                                              method='single', 
                                              criterion='distance')
        
        # find the exit points
        exits, exit_size = [], []
        for cluster_id in np.unique(data):
            points = exit_points[data == cluster_id]
            xm, ym = points.mean(axis=0)
            dist = np.hypot(points[:, 0] - xm, points[:, 1] - ym)
            exits.append(points[np.argmin(dist)])
            exit_size.append(len(points))

        exits = np.array(exits)
        exit_size = np.array(exit_size)

        # return the exits sorted by their size
        return exits[np.argsort(-exit_size), :]
        

    def calculate_burrow_centerline(self, burrow, point_start=None):
        """ determine the centerline of a burrow with one exit """
        if point_start is None:
            point_start = burrow.centerline[0]
        
        # get a binary image of the burrow
        mask, shift = burrow.get_mask(margin=2, dtype=np.int32, ret_offset=True)
        
        # move starting point onto ground line
        ground_line = self.ground.linestring
        point_start = curves.get_projection_point(ground_line, point_start)
        point_start = (int(point_start[0]) - shift[0],
                       int(point_start[1]) - shift[1])
        mask[point_start[1], point_start[0]] = 1

        # calculate the distance from the start point 
        regions.make_distance_map(mask, [point_start])
        
        # find the second point by locating the farthest point
        _, _, _, p_end = cv2.minMaxLoc(mask)
        
        # find an estimate for the centerline from the shortest distance from
        # the end point to the burrow exit
        points = regions.shortest_path_in_distance_map(mask, p_end)

        # translate the points back to global coordinates 
        centerline = curves.translate_points(points, shift[0], shift[1])
        # save centerline such that burrow exit is first point
        centerline = centerline[::-1]
        
        # add points that might be outside of the burrow contour
        ground_start = curves.get_projection_point(ground_line, centerline[0]) 
        centerline.insert(0, ground_start)
            
        # simplify the curve        
        centerline = cv2.approxPolyDP(np.array(centerline, np.int),
                                      epsilon=1, closed=False)
            
        # save the centerline in the burrow structure
        burrow.centerline = centerline[:, 0, :]
                                
                        
    def store_burrows(self):
        """ associates the current burrows with burrow tracks """
        burrow_tracks = self.result['burrows/tracks']
        ground_polygon = geometry.Polygon(self.get_ground_polygon_points())
        
        # check whether we already know this burrow
        # the burrows in self.burrows will always be larger than the burrows
        # in self.active_burrows. Consequently, it can happen that a current
        # burrow overlaps two older burrows, but the reverse cannot be true
        for burrow in self.burrows:
            # find all tracks to which this burrow may belong
            track_ids = [track_id 
                         for track_id, burrow_last in self.active_burrows()
                         if burrow_last.intersects(burrow)]
            
            if len(track_ids) > 1:
                # merge all burrows to a single track and keep the largest one
                track_longest, length_max = None, 0
                for track_id in track_ids:
                    burrow_last = burrow_tracks[track_id].last
                    # find track with longest burrow
                    if burrow_last.length > length_max:
                        track_longest, length_max = track_id, burrow_last.length
                    # merge the burrows
                    burrow.merge(burrow_last)
                        
            # keep the burrow parts that are below the ground line
            try:
                polygon = burrow.polygon.intersection(ground_polygon)
            except geos.TopologicalError:
                continue
            if polygon.is_empty:
                continue
            
            try:
                burrow.contour = regions.get_enclosing_outline(polygon)
            except TypeError:
                # can occur in corner cases where the enclosing outline cannot
                # be found
                continue
            
            # make sure that the burrow centerline lies within the ground region
            ground_poly = geometry.Polygon(self.get_ground_polygon_points())
            if burrow.linestring.length > 0:
                line = burrow.linestring.intersection(ground_poly)
            else:
                line = None
            
            if isinstance(line, geometry.multilinestring.MultiLineString):
                # pick the longest line if there are multiple
                index_longest = np.argmax(l.length for l in line)
                line = line[index_longest]

            is_line = isinstance(line, geometry.linestring.LineString)
            if not is_line or line.is_empty or line.length <= 1:
                # the centerline disappeared
                # => calculate a new centerline from the burrow contour
                end_point = self.burrow_estimate_exit(burrow)[0]
                self.calculate_burrow_centerline(burrow, point_start=end_point)
            
            else:
                # adjust the burrow centerline to reach to the ground line
                # it could be that the whole line was underground
                # => move the first data point onto the ground line
                line = np.array(line, np.double)
                line[0] = curves.get_projection_point(self.ground.linestring, line[0])
                # set the updated burrow centerline
                burrow.centerline = line
            
            # store the burrow if it is valid    
            if burrow.is_valid:
                if len(track_ids) > 1:
                    # add the burrow to the longest track
                    burrow_tracks[track_longest].append(self.frame_id, burrow)
                elif len(track_ids) == 1:
                    # add the burrow to the matching track
                    burrow_tracks[track_ids[0]].append(self.frame_id, burrow)
                else:
                    # create the burrow track
                    burrow_track = BurrowTrack(self.frame_id, burrow)
                    burrow_tracks.append(burrow_track)
                
        # use the new set of burrows in the next iterations
        self.burrows = [b.copy()
                        for _, b in self.active_burrows(time_interval=0)]
                
          
    def extend_burrow_by_mouse_trail(self, burrow):
        """ takes a burrow shape and extends it using the current mouse trail """
        if 'cage_interior_rectangle' in self._cache:
            cage_interior_rect = self._cache['cage_interior_rectangle']
        else:
            w, h = self.video.size
            points = [[1, 1], [w - 1, 1], [w - 1, h - 1], [1, h - 1]]
            cage_interior_rect = geometry.Polygon(points)
            self._cache['cage_interior_rectangle'] = cage_interior_rect
        
        # get the buffered mouse trail
        trail_width = self.params['burrows/width_min']
        mouse_trail = geometry.LineString(self.mouse_trail)
        mouse_trail_buffered = mouse_trail.buffer(trail_width)
        
        # extend the burrow contour by the mouse trail and restrict it to the
        # cage interior
        polygon = burrow.polygon.union(mouse_trail_buffered)
        polygon = polygon.intersection(cage_interior_rect)
        burrow.contour = regions.get_enclosing_outline(polygon)
            
        # update the centerline if the mouse trail is longer
        if mouse_trail.length > burrow.length:
            burrow.centerline = self.mouse_trail

                
    def find_burrows(self):
        """ locates burrows based on current mouse trail """

        if self.frame_id % self.params['burrows/adaptation_interval'] == 0:
            self.store_burrows()
        
        # check whether the mouse is in a burrow
        if self.mouse_trail is None:
            # mouse trail is unknown => we don't have enough information 
            return
        
        # check whether we already know this burrow
        burrows_with_mouse = []
        trail_line = geometry.LineString(self.mouse_trail)
        for burrow_id, burrow in enumerate(self.burrows):
            # determine whether we are inside this burrow
            dist = burrow.polygon.distance(trail_line)
            if dist < self.params['burrows/width']:
                burrows_with_mouse.append(burrow_id)

        if burrows_with_mouse:
            # extend the burrow in which the mouse is
            burrow_mouse = self.burrows[burrows_with_mouse[0]]
            self.extend_burrow_by_mouse_trail(burrow_mouse)
            
            # merge all the other burrows into this one
            for burrow_id in reversed(burrows_with_mouse[1:]):
                burrow_mouse.merge(self.burrows[burrow_id])
                del self.burrows[burrow_id]
                
        else:
            # create the burrow, since we don't know it yet
            mouse_trail = geometry.LineString(self.mouse_trail)
            trail_width = self.params['burrows/width_min']
            mouse_trail_buffered = mouse_trail.buffer(trail_width)
            contour = mouse_trail_buffered.boundary.coords

            burrow_mouse = Burrow(contour, centerline=self.mouse_trail)
            self.burrows.append(burrow_mouse)

        # simplify the burrow contour
        burrow_mouse.simplify_outline(tolerance=0.001)

                                        
    #===========================================================================
    # DEBUGGING
    #===========================================================================


    def debug_setup(self):
        """ prepares everything for the debug output """
        # load parameters for video output        
        video_output_period = int(self.params['output/video/period'])
        video_extension = self.params['output/video/extension']
        video_codec = self.params['output/video/codec']
        video_bitrate = self.params['output/video/bitrate']
        
        # set up the general video output, if requested
        if 'video' in self.debug_output or 'video.show' in self.debug_output:
            # initialize the writer for the debug video
            debug_file = self.get_filename('pass3' + video_extension, 'debug')
            self.debug['video'] = VideoComposer(debug_file, size=self.video.size,
                                                fps=self.video.fps, is_color=True,
                                                output_period=video_output_period,
                                                codec=video_codec, bitrate=video_bitrate)
            
            if 'video.show' in self.debug_output:
                name = self.name if self.name else ''
                position = self.params['debug/window_position']
                image_window = ImageWindow(self.debug['video'].shape,
                                           title='Debug video pass 3 [%s]' % name,
                                           multiprocessing=self.params['debug/use_multiprocessing'],
                                           position=position)
                self.debug['video.show'] = image_window


    def debug_process_frame(self, frame, mouse_track):
        """ adds information of the current _frame to the debug output """
        
        if 'video' in self.debug:
            debug_video = self.debug['video']
            
            # plot the ground profile
            if self.ground is not None:
                debug_video.add_line(self.ground.points, is_closed=False,
                                     mark_points=True, color='y')
        
            # indicate the mouse position
            trail_length = self.params['output/video/mouse_trail_length']
            time_start = max(0, self.frame_id - trail_length)
            track = mouse_track.pos[time_start:self.frame_id, :]
            if len(track) > 0:
                debug_video.add_line(track, '0.5', is_closed=False)
                debug_video.add_circle(track[-1], self.params['mouse/model_radius'],
                                       'w', thickness=1)
            
            # indicate the current mouse trail    
            if self.mouse_trail:
                debug_video.add_line(self.mouse_trail, 'b', is_closed=False,
                                     mark_points=True, width=2)                
                
            # indicate the currently active burrow shapes
            if self.params['burrows/enabled_pass3']:
                for _, burrow in self.active_burrows():
                    if hasattr(burrow, 'elongated') and burrow.elongated:
                        burrow_color = 'red'
                    else:
                        burrow_color = 'DarkOrange'
                    debug_video.add_line(burrow.centerline, burrow_color,
                                         is_closed=False, mark_points=True,
                                         width=2)
                    if burrow.contour is not None:
                        debug_video.add_line(burrow.contour, burrow_color,
                                             is_closed=True, mark_points=False,
                                             width=1)
                
            # indicate the mouse state
            try:
                mouse_state = mouse_track.states[self.frame_id]
            except IndexError:
                pass
            else:
                debug_video.add_text(mouse.state_converter.int_to_symbols(mouse_state),
                                     (120, 20), anchor='top')
                
            # add additional debug information
            debug_video.add_text(str(self.frame_id), (20, 20), anchor='top')   
            if 'video.show' in self.debug:
                if debug_video.output_this_frame:
                    self.debug['video.show'].show(debug_video._frame)
                else:
                    self.debug['video.show'].show()


    def debug_finalize(self):
        """ close the video streams when done iterating """
        # close the window displaying the video
        if 'video.show' in self.debug:
            self.debug['video.show'].close()
        
        # close the open video streams
        if 'video' in self.debug:
            try:
                self.debug['video'].close()
            except IOError:
                    self.logger.exception('Error while writing out the debug '
                                          'video') 
            
    