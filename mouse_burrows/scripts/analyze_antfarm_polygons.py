#!/usr/bin/env python2
'''
Created on Jan 30, 2015

@author: David Zwicker <dzwicker@seas.harvard.edu>
'''

from __future__ import division

import argparse
import collections
import cPickle as pickle
import functools
import logging
import multiprocessing as mp
import os.path
import operator
import sys
import traceback

import cv2
import numpy as np
from scipy import cluster, ndimage, spatial
from shapely import geometry
import pint

# add the root of the video-analysis project to the path
this_path = os.path.dirname(__file__)
project_path = os.path.join(this_path, '..', '..')
sys.path.append(project_path)

from mouse_burrows.algorithm.objects import Burrow, GroundProfile
from video.analysis import curves, image, regions, shapes
from utils import data_structures, math, misc
from utils.files import ensure_directory_exists

from video import debug  # @UnusedImport


default_parameters = {
    'image/remove_border': 2, #< pixels to remove around the border
    'burrow_parameters': {'ground_point_distance': 2},
    'burrow/area_min': 1000,
    'burrow/width_typical': 30,
    'burrow/branch_length_min': 150,
    'burrow/branch_point_separation': 100,
    'burrow/angle_measurement_distance_cm': 8,
    'cage/width_norm': 85.5,
    'cage/width_min': 60,
    'cage/width_max': 110,
    'colors/burrow': (1, 1, 0),      #< burrow color in RGB
    'colors/ground_line': (0, 1, 0), #< ground line color in RGB
    'colors/scale_bar': (1, 1, 1),   #< scale bar color in RGB
    'colors/isolation_closing_radius': 10, #< radius of mask for closing op.
    'scale_bar/area_max': 1000,
    'scale_bar/length_min': 100,
    'scale_bar/dist_bottom': 0.1,
    'scale_bar/dist_left': 0.1,
    'scale_bar/length_cm': 10,
}



ScaleBar = collections.namedtuple('ScaleBar', ['size', 'angle'])



class AntfarmShapes(object):
    """ class that manages shapes in an antfarm """

    def __init__(self, parameters=None, name=''):
        """ initializes the polygon collection
        `polygons` is a list of polygons
        `parameters` are parameters for the algorithms of this class
        `name` is the name of the collection
        `debug_output` can be a folder to which debug output will be written
        """
        self.name = name
        self.image = None

        self.burrows = []
        self.ground_line = None
        self.scale_bar = None

        self._debug = {'possible_branches': []}

        self.params = default_parameters.copy()
        if parameters is not None:
            self.params.update(parameters)


    @classmethod
    def load_from_file(cls, path, **kwargs):
        """ load polygons from a file """
        # handle the file
        _, filename = os.path.split(path)
        name, ext = os.path.splitext(filename)
        ext = ext.lower()

        obj = cls(name=name, **kwargs)

        # determine which loader to use for the individual files
        if ext == '.jpg' or ext == '.png':
            logging.debug('Use OpenCV image loader to read file `%s`', path)

            img = cv2.imread(path)
            obj.image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) #< convert to RGB

            # remove some part of the border if requested
            remove_border = obj.params['image/remove_border']
            if remove_border > 0:
                obj.image = obj.image[remove_border:-remove_border,
                                      remove_border:-remove_border]

            obj.filename = filename

        else:
            raise ValueError("Don't know how to read `*%s` files" % ext)

        obj.analyze_image()

        return obj


    def analyze_image(self):
        """ load the data from an image """
        # load parameters
        color_scale_bar = self.params['colors/scale_bar']
        color_ground_line = self.params['colors/ground_line']
        color_burrow = self.params['colors/burrow']

        # find the scale bar
        scale_mask = self.isolate_color(self.image, color_scale_bar)
        self.scale_bar = self.get_scalebar_from_image(scale_mask)

        # find the ground line
        dilate = self.params['colors/isolation_closing_radius']
        ground_mask = self.isolate_color(self.image, color_ground_line, dilate=dilate)
        self.ground_line = self.get_groundline_from_image(ground_mask)

        # find all the burrows
        burrow_mask = self.isolate_color(self.image, color_burrow)
        self.burrows = self.get_burrows_from_image(burrow_mask, self.ground_line)

        # determine additional burrow properties
        for burrow in self.burrows:
            self.calculate_burrow_properties(burrow, self.ground_line)


    def _add_burrow_angle_statistics(self, burrow, ground_line):
        """ adds statistics about the burrow slopes to the burrow object """
        # determine the fraction of the burrow that goes upwards
        cline = burrow.centerline
        clen = curves.curve_segment_lengths(cline)
        length_upwards = clen[np.diff(cline[:, 1]) < 0].sum()

        # distinguish left from right burrows
        center = (ground_line.points[0, 0] + ground_line.points[-1, 0]) / 2
        burrow_on_left = (burrow.centroid[0] < center)
        cline_left2right = (cline[0, 0] < cline[-1, 0])
        if burrow_on_left ^ cline_left2right:
            # burrow is on the left and centerline goes from right to left
            # or burrow is on the right and centerline goes left to right
            # => We measured the correct portion of the burrow
            burrow.length_upwards = min(burrow.length, length_upwards)

        else:
            # burrow is on the left and centerline goes from left to right
            # or burrow is on the right and centerline goes right to left
            # => We measured the compliment of what we actually want
            burrow.length_upwards = max(0, burrow.length - length_upwards)


    def calculate_burrow_properties(self, burrow, ground_line=None):
        """ calculates additional properties of the burrow """

        # load some parameters
        burrow_width = self.params['burrow/width_typical']
        min_length = self.params['burrow/branch_length_min']

        # determine the burrow end points
        endpoints = burrow.get_endpoints(ground_line)

        # get distance map from centerline
        distance_map, offset = burrow.get_mask(margin=2, dtype=np.uint16,
                                               ret_offset=True)
        cline = burrow.centerline
        start_points = curves.translate_points(cline, -offset[0], -offset[1])
        regions.make_distance_map(distance_map, start_points)

        # determine endpoints, which are not already part of the centerline
        end_coords = np.array([ep.coords for ep in endpoints])
        dists = spatial.distance.cdist(end_coords, cline)
        extra_ends = end_coords[dists.min(axis=1) > burrow_width, :].tolist()
        extra_ends = curves.translate_points(extra_ends, -offset[0], -offset[1])

        # get additional points that are far away from the centerline
        map_max = ndimage.filters.maximum_filter(distance_map, burrow_width)
        map_maxima =  (distance_map == map_max) & (distance_map > min_length)
        maxima = np.array(np.nonzero(map_maxima)).T

        # determine the object from which we measure the distance to the sky
        if ground_line is not None:
            outside = ground_line.linestring
        else:
            outside = geometry.MultiPoint(end_coords)

        # define a helper function for checking the connection to the ground
        burrow_poly = burrow.polygon.buffer(2)
        def _direct_conn_to_ground(point, has_offset=False):
            """ helper function checking the connection to the ground """
            if has_offset:
                point = (point[0] + offset[0], point[1] + offset[1])
            p_ground = curves.get_projection_point(outside, point)
            conn_line = geometry.LineString([point, p_ground])
            return conn_line.length < 1 or conn_line.within(burrow_poly)

        branch_points = []
        branch_point_separation = self.params['burrow/branch_point_separation']
        if maxima.size > 0:
            if len(maxima) == 1:
                clusters = [0]
            else:
                # cluster maxima to reduce them to single end points
                # this is important when a burrow has multiple exits to the ground
                clusters = cluster.hierarchy.fclusterdata(
                    maxima, branch_point_separation,
                    method='single', criterion='distance'
                )

            cluster_ids = np.unique(clusters)
            logging.debug('Found %d possible branch point(s)' % len(cluster_ids))

            # find the additional point from the clusters
            for cluster_id in cluster_ids:
                candidates = maxima[clusters == cluster_id, :]

                # get point with maximal distance from center line
                dists = [distance_map[x, y] for x, y in candidates]
                y, x = candidates[np.argmax(dists)]

                # check whether this point is close to an endpoint
                point = geometry.Point(x + offset[0], y + offset[1])
                branch_depth = point.distance(outside)
                if (branch_depth > min_length or
                        not _direct_conn_to_ground((x, y), has_offset=True)):
                    branch_points.append((x, y))

            # save some output for debugging
            self._debug['possible_branches'] = \
                    curves.translate_points(branch_points, offset[0], offset[1])

        # find the burrow branches
        burrow.branches = []

        if extra_ends or branch_points:
            num_branches = len(extra_ends) + len(branch_points)
            logging.info('Found %d possible branch(es)' % num_branches)

            # create generator for iterating over all additional points
            gen = ((p_class, p_coords)
                   for p_class, points in enumerate([extra_ends, branch_points])
                   for p_coords in points)

            # connect all additional points to the centerline -> branches
            for ep_id, ep in gen:
                line = regions.shortest_path_in_distance_map(distance_map, ep)
                line = curves.translate_points(line, offset[0], offset[1])

                # estimate the depth of the branch
                depth = max(geometry.Point(p).distance(outside)
                            for p in (line[0], line[-1]))

                # check whether the line corresponds to an open branch
                # open branches are branches where all connection lines between
                # the branch and ground line are fully contained in the burrow
                # polygon
                if ep_id == 1 and depth < min_length:
                    num_direct = sum(1 for p_branch in line
                                     if _direct_conn_to_ground(p_branch))
                    ratio_direct = num_direct / len(line)
                    if ratio_direct > 0.75:
                        # the ground is directly reachable from most points
                        line = None

                if line is not None:
                    burrow.branches.append(line)

        # fix the centerline in certain cases
        if len(burrow.centerline) < 2:
            if len(burrow.endpoints) == 2:
                burrow.centerline = [[e.x, e.y] for e in burrow.endpoints]

        if ground_line:
            self._add_burrow_angle_statistics(burrow, ground_line)

        return


    def add_debug_output(self):
        """ make debug output image """
        logging.info('Creating debug output')

        for point in self._debug['possible_branches']:
            coords = tuple([int(c) for c in point])
            cv2.circle(self.image, coords, 10, color=(255, 255, 255),
                       thickness=-1)

        for burrow in self.burrows:
            # draw the morphological graph
#             for points in burrow.morphological_graph.get_edge_curves():
#                 cv2.polylines(self.image, [np.array(points, np.int)],
#                               isClosed=False, color=(255, 255, 255),
#                               thickness=2)


            # draw the additional branches
            for points in burrow.branches:
                cv2.polylines(self.image, [np.array(points, np.int)],
                              isClosed=False, color=(255, 255, 255),
                              thickness=2)

            # draw the smooth centerline
            cline = burrow.centerline
            cv2.polylines(self.image, [np.array(cline, np.int)],
                          isClosed=False, color=(255, 0, 0), thickness=3)

            # mark the end points
            for e_p in burrow.endpoints:
                if e_p.is_exit:
                    color = (0, 0, 255)
                else:
                    color = (0, 255, 0)
                coords = tuple([int(c) for c in e_p.coords])
                cv2.circle(self.image, coords, 10, color, thickness=-1)

#             # mark beginning of the centerline
#             p = burrow.centerline[0]
#             cv2.circle(self.image, (int(p[0]), int(p[1])), 15, (255, 255, 255),
#                        thickness=2)


    def write_debug_image(self, filename):
        """ write the debug output image to file """
        self.add_debug_output()

        img = cv2.cvtColor(self.image, cv2.COLOR_RGB2BGR) #< convert to BGR

        cv2.imwrite(filename, img)

        logging.info('Wrote output file `%s`' % filename)


    def show_debug_image(self):
        """ shows the debug image on screen """
        self.add_debug_output()
        debug.show_image(self.image)


    def _get_line_from_contour(self, contour):
        """ determines a line described by a contour """
        # calculate the distance between all points on this contour
        dist = spatial.distance.pdist(contour, 'euclidean')
        dist = spatial.distance.squareform(dist)

        # start from the left most point and find all points
        p_cur = np.argmin(contour[:, 0])
        p_avail = np.ones(len(contour), np.bool)
        p_avail[p_cur] = False

        points = []
        while True:
            # add the current point to our list
            points.append(contour[p_cur, :])

            # find the closest points
            p_close = np.where((dist[p_cur, :] < 4) & p_avail)[0]
            if len(p_close) == 0:
                break

            # find the next point
            k = np.argmax(dist[p_cur, p_close])
            p_cur = p_close[k]

            # remove all old points that are in the same surrounding
            p_avail[p_close] = False
        return points


    def get_scalebar_from_image(self, mask):
        """ finds the scale bar in the image """
        # determine contours in the mask
        contours = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_NONE)[1]

        if len(contours) == 0:
            logging.warn('Could not find any scale bar in `%s`', self.name)
            return None

        # pick the contour with the largest extent in either axes
        contour = max(contours, key=lambda cnt: cnt.ptp(axis=0).max())
        
        # debug.show_shape(geometry.LineString(np.squeeze(contour)),
        #                  background=self.image)

        # determine the rectangle that describes the contour best
        _, (w, h), rot = cv2.minAreaRect(contour)

        if max(w, h) > self.params['scale_bar/length_min']:
            # we found the scale bar
            if w > h:
                scale_bar = ScaleBar(size=w, angle=rot)
            else:
                scale_bar = ScaleBar(size=h, angle=(rot + 90) % 180)

            logging.debug('Did find scale bar of length %g.', scale_bar.size)
            
        else:
            logging.warn('Did not find a large enough scale bar in `%s`.',
                         self.name)
            scale_bar = None

        return scale_bar


    def get_groundline_from_image(self, mask):
        """ load burrow polygons from an image """
        # get the skeleton of the image
        mask = image.mask_thinning(mask, method='guo-hall')
        
        # get the path between the two points in the mask that are farthest
        points = regions.get_farthest_points(mask, ret_path=True)

        # build the ground line from this
        ground_line = GroundProfile(points)

#         debug.show_shape(ground_line.linestring, background=mask)

        return ground_line


    def get_burrows_from_image(self, mask, ground_line):
        """ load burrow polygons from an image """
        # turn image into gray scale
        height, width = mask.shape

        # get a polygon for cutting away the sky
        above_ground = ground_line.get_polygon(0, left=0, right=width)

        # determine contours in the mask
        contours = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_SIMPLE)[1]
                                    
        # iterate through the contours
        burrows = []
        for contour in contours:
            points = contour[:, 0, :]
            if len(points) <= 2:
                continue

            # get the burrow area
            area = cv2.contourArea(contour)

            if area < self.params['scale_bar/area_max']:
                # object could be a scale bar
                rect = shapes.Rectangle(*cv2.boundingRect(contour))

                at_left = (rect.left < self.params['scale_bar/dist_left']*width)
                max_dist_bottom = self.params['scale_bar/dist_bottom']
                at_bottom = (rect.bottom > (1 - max_dist_bottom) * height)
                hull = cv2.convexHull(contour)
                hull_area = cv2.contourArea(hull)
                is_simple = (hull_area < 2*area)

                if at_left and at_bottom and is_simple:
                    # the current polygon is the scale bar
                    _, (w, h), _ = cv2.minAreaRect(contour)

                    if max(w, h) > self.params['scale_bar/length_min']:
                        raise RuntimeError('Found something that looks like a '
                                           'scale bar')
                        
            if area < self.params['burrow/area_min']:
                # burrow is too small
                logging.debug('Disregard burrow, because its area is too small '
                              '(%g < %g)', area, self.params['burrow/area_min'])
                
            else:
                # build polygon out of the contour points
                burrow_poly = geometry.Polygon(points)

                # regularize the points to remove potential problems
                burrow_poly = regions.regularize_polygon(burrow_poly)

                # build the burrow polygon by removing the sky
                burrow_poly = burrow_poly.difference(above_ground)

                # create a burrow from the outline
                boundary = regions.get_enclosing_outline(burrow_poly)

                # check if a correct burrow was produced
                if len(boundary.coords) < 3:
                    continue

                burrow = Burrow(boundary.coords,
                                parameters=self.params['burrow_parameters'])
                burrows.append(burrow)

        logging.info('Found %d polygon(s)' % len(burrows))
        return burrows


    def isolate_color(self, img, color, white_background=None, dilate=0):
        """ isolates a certain color channel from the image. Color should be a
        binary vector only containing 0 and 1 """
        # determine whether the background is white or black if not given
        if white_background is None:
            white_background = (np.mean(img) > 128)
            if white_background:
                logging.debug('Image appears to have a white background.')
            else:
                logging.debug('Image appears to have a black background.')

        # Determine the limits of the color function
        # Here, each limit is a tuple of two numbers, which define the range
        # of acceptable colors. Note that there are two ranges, depending on
        # whether the color channel should be absent or present
        if white_background:
            limits_absent = (0, 230)
            limits_present = (128, 255)
        else: # dark background
            limits_absent = (0, 30)
            limits_present = (30, 255)
        limits = (limits_absent, limits_present)
        bounds = np.array([limits[int(c)] for c in color], np.uint8)

        # find the mask highlighting the respective colors
        mask = cv2.inRange(img, bounds[:, 0], bounds[:, 1])

        # dilate the mask to close gaps in the outline
        w = int(self.params['colors/isolation_closing_radius'])
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                           (2*w + 1, 2*w + 1))
        mask_dilated = cv2.dilate(mask, kernel)

        # fill the objects
        contours = cv2.findContours(mask_dilated.copy(), cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_SIMPLE)[1]

        for contour in contours:
            cv2.fillPoly(mask_dilated, [contour[:, 0, :]], color=(255, 255, 255))

        # erode the mask and return it
        if dilate != 0:
            w = int(self.params['colors/isolation_closing_radius'] - dilate)
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                               (2*w + 1, 2*w + 1))
        mask = cv2.erode(mask_dilated, kernel)

        # make sure nothing touches the border
        image.set_image_border(mask, size=1, color=0)

        return mask


    def _get_burrow_exit_length(self, burrow):
        """ calculates the length of all exists of the given burrow """
        # identify all points that are close to the ground line
        dist_max = burrow.parameters['ground_point_distance']
        g_line = self.ground_line.linestring
        points = burrow.contour
        exitpoints = [g_line.distance(geometry.Point(point)) < dist_max
                      for point in points]

        # find the indices of contiguous true regions
        indices = math.contiguous_true_regions(exitpoints)

        # find the total length of all exits
        exit_length = 0
        for a, b in indices:
            exit_length += curves.curve_length(points[a : b+1])

        # handle the first and last point if they both belong to an exit
        if exitpoints[0] and exitpoints[-1]:
            exit_length += curves.point_distance(points[0], points[-1])

        return exit_length


    def _centerline_is_oriented(self, burrow):
        """ returns True if the centerline is oriented correctly, i.e. if it
        starts at the lowest exit """
        first_point = burrow.centerline[0]
        last_point = burrow.centerline[-1]

        # determine the exit points
        exit_points = [e_p.coords for e_p in burrow.endpoints if e_p.is_exit]

        if len(exit_points) == 0:
            first_is_exit = last_is_exit = False

        else: # there are exit points
            exit_points = geometry.MultiPoint(exit_points)

            # check whether the points are exit points
            burrow_width = self.params['burrow/width_typical']
            first_is_exit = (exit_points.distance(geometry.Point(first_point))
                             < burrow_width)
            last_is_exit = (exit_points.distance(geometry.Point(last_point))
                            < burrow_width)

        if first_is_exit:
            if last_is_exit:
                # check whether the first point is lower than the last point
                # note that the y-axis points down
                return (first_point[1] > last_point[1])
            else:
                # only the first point is an exit
                return True

        else: # first point is not an exit
            if last_is_exit:
                # only the last point is an exit
                return False
            else:
                # neither of the points is an exit
                return True


    def get_statistics(self):
        """ returns statistics for all the polygons """
        result = {'name': self.name}

        # save results about ground line
        points = self.ground_line.points
        ground_width_px = abs(points[0, 0] - points[-1, 0])
        ground_cm_per_pixel = self.params['cage/width_norm'] / ground_width_px
        result['ground'] = {'ground_length': self.ground_line.length,
                            'ground_width_pixel': ground_width_px,
                            'cm_per_pixel': ground_cm_per_pixel}

        # check the scale bar
        if self.scale_bar:
            logging.info('Found %d pixel long scale bar' % self.scale_bar.size)
            cm_per_pixel = self.params['scale_bar/length_cm'] / self.scale_bar.size
            units = pint.UnitRegistry()
            scale_factor = cm_per_pixel * units.cm

            # check the ground line
            points = self.ground_line.points
            len_x_cm = abs(points[0, 0] - points[-1, 0]) * scale_factor
            w_min = self.params['cage/width_min'] * units.cm
            w_max = self.params['cage/width_max'] * units.cm
            if not w_min < len_x_cm < w_max:
                raise RuntimeError('The length (%s) of the ground line is '
                                   'not in [%s, %s] for image `%s`.'
                                   % (len_x_cm, w_min, w_max, self.name))

            result['scale_bar'] = {'length_pixel': self.scale_bar.size,
                                   'cm_per_pixel': cm_per_pixel}

        else:
            # there is no scale bar
            scale_factor = 1
            result['scale_bar'] = None
            logging.warn('Could not find a scale bar in the image `%s`',
                         self.name)

        # determine some parameters
        try:
            angle_dist_px = (self.params['burrow/angle_measurement_distance_cm']
                             / cm_per_pixel)
        except UnboundLocalError:
            angle_dist_px = self.params['burrow/angle_measurement_distance_cm']

        # collect result of all burrows
        result['burrows'] = []
        for burrow in self.burrows:
            # calculate some additional statistics
            perimeter_exit = self._get_burrow_exit_length(burrow)
            exit_count = sum(1 for ep in burrow.endpoints if ep.is_exit)
            branch_length = sum(curves.curve_length(points)
                                for points in burrow.branches)

            # determine burrow angles and distance between end points
            angle1 = np.rad2deg(burrow.get_entry_angle(angle_dist_px))
            angle2 = np.rad2deg(burrow.get_exit_angle(angle_dist_px))
            level_difference = (burrow.centerline[0, 1]
                                - burrow.centerline[-1, 1])

            # make sure the values are reported correctly
            if self._centerline_is_oriented(burrow):
                angle_entrance, angle_exit = angle1, angle2
            else:
                # switch the measurements as if the centerline was reoriented
                angle_entrance, angle_exit = angle2, angle1
                level_difference *= -1

            # get the branch angles, measured at the point on the centerline
            branch_angles = []
            for branch in burrow.branches:
                p0, p1 = branch[-1], branch[0]
                # calculate the angle, note that y-axis points down
                angle = np.arctan2(p0[1] - p1[1], p1[0] - p0[0])
                branch_angles.append(np.rad2deg(angle))

            while len(branch_angles) < 2:
                branch_angles.append(np.nan)

            #graph = burrow.morphological_graph
            data = {'pos_x': burrow.centroid[0] * scale_factor,
                    'pos_y': burrow.centroid[1] * scale_factor,
                    'area': burrow.area * scale_factor**2,
                    'length': burrow.length * scale_factor,
                    'length_upwards': burrow.length_upwards * scale_factor,
                    'fraction_upwards': burrow.length_upwards / burrow.length,
                    'exit_count': exit_count,
                    'entrance_angle [degree]': angle_entrance,
                    'exit_angle [degree]': angle_exit,
                    'entrance_exit_difference': level_difference * scale_factor,
#                     'centerline_oriented': self._centerline_is_oriented(burrow),
                    'branch_length': branch_length * scale_factor,
                    'branch_count': len(burrow.branches),
                    'branch_angle_1 [degree]': branch_angles[0],
                    'branch_angle_2 [degree]': branch_angles[1],
                    'total_length': (branch_length + burrow.length)*scale_factor,
                    'perimeter': burrow.perimeter * scale_factor,
                    'perimeter_exit': perimeter_exit * scale_factor,
                    'openness': perimeter_exit / burrow.perimeter}
            result['burrows'].append(data)

        return result



def process_polygon_file(path, output_folder=None, suppress_exceptions=False,
                         debug=False, 
                         scale=default_parameters['scale_bar/length_cm']):
    """ process a single shape file given by path """
    if suppress_exceptions:
        # run the function within a catch-all try-except-block
        try:
            result = process_polygon_file(path, output_folder, False, debug)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            traceback.print_exc()
            print('Exception occurred for file `%s`' % path)
            result = None

    else:
        # do the actual computation
        logging.info('Analyzing file `%s`' % path)

        # load from image
        parameters = {'scale_bar/length_cm': scale}
        pc = AntfarmShapes.load_from_file(path, parameters=parameters)

        if output_folder:
            output_file = os.path.join(output_folder, pc.filename)
            pc.write_debug_image(output_file)

        if debug:
            pc.show_debug_image()

        result = pc.get_statistics()

    return result



def main():
    """ main routine of the program """
    # parse the command line arguments
    parser = argparse.ArgumentParser(description='Analyze antfarm polygons')
    parser.add_argument('-c', '--result_csv', dest='result_csv', type=str,
                        metavar='FILE.csv',
                        help='csv file to which statistics about the burrows '
                             'are written')
    parser.add_argument('-p', '--result_pkl', dest='result_pkl', type=str,
                        metavar='FILE.pkl',
                        help='python pickle file to which all results from the '
                             'algorithm are written')
    parser.add_argument('-l', '--load_pkl', dest='load_pkl', type=str,
                        metavar='FILE.pkl',
                        help='python pickle file from which data is loaded')
    parser.add_argument('-f', '--folder', dest='folder', type=str,
                        help='folder where output images will be written to')
    parser.add_argument('--scale', dest='scale', type=float,
                        default=default_parameters['scale_bar/length_cm'],
                        help='length of the scale bar in cm')
    flags = parser.add_mutually_exclusive_group(required=False)
    flags.add_argument('-m', '--multi-processing', dest='multiprocessing',
                        action='store_true', help='turns on multiprocessing')
    flags.add_argument('-d', '--debug', dest='debug', action='store_true',
                        help='does debug output')
    parser.add_argument('files', metavar='FILE', type=str, nargs='*',
                        help='files to analyze')

    # parse the command line arguments
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.folder:
        ensure_directory_exists(args.folder)

    if args.load_pkl:
        # load file from pickled data
        logging.info('Loading data from file `%s`.' % args.load_pkl)
        with open(args.load_pkl, "rb") as fp:
            results = pickle.load(fp)

    else:
        # get files to analyze
        files = args.files
        logging.info('Analyzing %d files.' % len(files))

        # collect burrows from all files
        if args.multiprocessing:
            # use multiple processes to analyze data
            job_func = functools.partial(process_polygon_file,
                                         output_folder=args.folder,
                                         suppress_exceptions=True,
                                         scale=args.scale)
            pool = mp.Pool()
            results = pool.map(job_func, files)

        else:
            # analyze data in the current process
            job_func = functools.partial(process_polygon_file,
                                         output_folder=args.folder,
                                         suppress_exceptions=False,
                                         debug=args.debug, scale=args.scale)
            
            # iterate over all files
            results = []
            for path in misc.display_progress(files):
                results.append(job_func(path))

        # filter results
        results = [res for res in results if res is not None]

        # write complete results as pickle file if requested
        if args.result_pkl:
            with open(args.result_pkl, "wb") as fp:
                pickle.dump(results, fp)

    # write burrow results as csv file if requested
    if args.result_csv:
        # create a dictionary of lists
        table = collections.defaultdict(list)
        # iterate through all experiments and save information about the burrows
        for data in results:
            if data:
                # sort the burrows from left to right
                burrows = sorted(data['burrows'],
                                 key=operator.itemgetter('pos_x'))
                # create a single row per burrow
                for burrow_id, properties in enumerate(burrows, 1):
                    properties['burrow_id'] = burrow_id
                    properties['experiment'] = data['name']
                    # iterate over all burrow properties
                    for k, v in properties.iteritems():
                        table[k].append(v)

        # write the data to a csv file
        first_columns = ['experiment', 'burrow_id']
        data_structures.misc.save_dict_to_csv(table, args.result_csv,
                                              first_columns=first_columns)



if __name__ == '__main__':
    main()

