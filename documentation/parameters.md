Parameters
====

analysis
--------
* `analysis/burrow_pass = 3`: Determines the video analysis pass from which the burrow data is loaded to do analysis.
* `analysis/frames = None`: Frames of the video which are included in the report of the analysis [start and end index should be given]. If this is omitted, all analyzed frames are included

background
----------
* `background/adaptation_rate = 0.01`: Rate at which the background is adapted
* `base_folder = .`: Base folder in which all files are kept

burrows
-------
* `active_contour`
  * `burrows/active_contour/convergence_rate = 0.01`: Convergence rate of the active contour algorithm used for refining the burrow shape.
  * `burrows/active_contour/blur_radius = 2`: Blur radius of the active contour algorithm used for refining the burrow shape.
  * `burrows/active_contour/stiffness = 10000.0`: Stiffness of the active contour algorithm used for refining the burrow shape.
  * `burrows/active_contour/max_iterations = 100`: Maximal number of iterations of the active contour algorithm used for refining the burrow shape.
* `burrows/activity_ignore_interval = 9000`: The time interval of the burrow trajectory that is ignored in the activity analysis. This is mainly done to circumvent problems with the initial predug.
* `burrows/activity_smoothing_interval = 54000`: The standard deviation of the Gaussian that is used for smoothing temporal data that is associated with activity measurements.
* `burrows/adaptation_interval = 100`: How often are the burrow shapes adapted
* `burrows/area_min = 400`: Minimal area a burrow cross section has to have
* `burrows/cage_margin = 30`: Margin of a potential burrow to the cage boundary
* `burrows/centerline_segment_length = 15`: Length of a segment of the center line of a burrow
* `burrows/chunk_area_min = 50`: Minimal area a burrow chunk needs to have in order to be considered.
* `burrows/chunk_dist_max = 30`: Maximal distance between a burrow chunk and another structure (either another chunk or the ground line), such that the chunk is connected to the other structure.
* `burrows/curvature_radius_max = 30`: Maximal radius of curvature the centerline is allowed to have
* `burrows/enabled_pass1 = False`: Whether burrows should be located in the first pass
* `burrows/enabled_pass3 = True`: Whether burrows should be located in the third pass
* `burrows/enabled_pass4 = True`: Whether burrows should be located in the fourth pass
* `burrows/fitting_edge_R2min = -10`: Minimal value of the Coefficient of Determination (R^2) above which the fit of a burrow edge is considered good enough and will be used
* `burrows/fitting_edge_width = 3`: Width of the burrow edge used in the template for fitting
* `burrows/fitting_length_threshold = 100`: Length above which burrows are refined by fitting
* `burrows/fitting_width_threshold = 30`: Width below which burrows are refined by fitting
* `burrows/grabcut_burrow_core_area_min = 500`: Minimal area the sure region of the mask for the grab cut algorithm is supposed to have
* `burrows/ground_point_distance = 10`: Maximal distance of ground profile to outline points that are considered exit points
* `burrows/image_statistics_overlap_threshold = 0.5`: The threshold value of the allowed overlap of the background and foreground statistics. If the distributions overlap more than this value the point is considered to be background since it cannot be discriminated reliably.
* `burrows/image_statistics_window = 50`: Half of the size of the window over which the statistics of the image are calculated.
* `burrows/initiation_threshold = 300`: Minimal area that a burrow has to be dug in order to be counted as `initiated`
* `burrows/outline_simplification_threshold = 0.005`: Determines how much the burrow outline might be simplified. The quantity determines by what fraction the total outline length is allowed to change
* `burrows/predug_analyze_time = 1800`: The time duration after burrow detection at which the predug is analyzed.
* `burrows/predug_area_threshold = 1000`: The minimal area in pixels the burrow has to have in order to be considered as a predug.
* `burrows/shape_threshold_distance = 50`: Threshold value for the distance of burrow points from the ground points. If all points are closer than this threshold, the burrow is called a "wide burrow". Otherwise, the burrow will be treated as a "long burrow".
* `burrows/simplification_threshold_area = 50`: Burrow outline points are removed when the resulting effective change is below this threshold
* `burrows/width = 20`: Typical width of a burrow
* `burrows/width_min = 10`: Minimal width of a burrow

cage
----
* `cage/boundary_detection_bottom_estimate = 0.95`: Fraction of the image height that is used to estimate the position of the bottom of the frame
* `cage/boundary_detection_thresholds = [0.7, 0.3, 0.7, 0.9]`: Thresholds for the boundary detection algorithm. The four values are the fraction of bright pixels necessary to define the boundary for [left, top, right, bottom], respectively.
* `cage/determine_boundaries = True`: Flag indicating whether the cropping rectangle should be determined automatically. If False, we assume that the original video is already cropped
* `cage/height_max = 500`: Maximal height of the cage. This is only used to make a plausibility test of the results
* `cage/height_min = 300`: Minimal height of the cage. This is only used to make a plausibility test of the results
* `cage/linescan_length = 50`: Length of the line scan that is used to determine the cage boundary.
* `cage/linescan_smooth = 5`: Standard deviation used for smoothing the line scan profile
* `cage/linescan_width = 30`: Width of the line scan use to extend the ground line to the cage frame.
* `cage/rectangle_buffer = 5`: Margin by which the estimated cage rectangle is enlarged before it is located by fitting.
* `cage/refine_by_fitting = True`: Flag determining whether the cage rectangle should be refined by using fitting to locate the cage boundaries.
* `cage/restrict_to_largest_patch = True`: Determines whether the cage analysis will be restricted to the largest patch in the first thresholded image.
* `cage/threshold_basic = otsu`: Determines the basic method that is used for thresholding. The default is `otsu`, which implements and automatic threshold. Alternatively, a number between 0 and 255 can be given, which is then used directly.
* `cage/threshold_zscore = 0.5`: Factor that determines the threshold for producing the binary image that is used to located the frame of the cage. The threshold is calculated according to the formula thresh = img_mean - factor*img_std, where factor is the factordetermined here.
* `cage/width_cm = 85.5`: Measured width of the cages/antfarms. The width is measured inside the cage, not including the frame.
* `cage/width_max = 800`: Maximal width of the cage. This is only used to make a plausibility test of the results
* `cage/width_min = 550`: Minimal width of the cage. This is only used to make a plausibility test of the results

colors
------
* `colors/adaptation_interval = 1000`: How often are the color estimates adapted
* `colors/std_min = 5`: Minimal standard deviation of sky and sand colors

debug
-----
* `debug/folder = debug/`: Folder to which debug videos are written
* `debug/output = []`: List of identifiers determining what debug output is produced. Supported identifiers include 'video', 'explored_area', 'background', 'difference', 'cage_estimate', 'predug', 'ground_estimate', 'explored_area_mask'.
* `debug/use_multiprocessing = True`: Flag indicating whether multiprocessing should be used to read and display videos
* `debug/window_position = None`: Position (x, y) of the top-left corner of the debug window

explored_area
-------------
* `explored_area/adaptation_rate_burrows = 0`: Rate at which the explored area is adapted inside burrows
* `explored_area/adaptation_rate_outside = 0.001`: Rate at which the explored area is adapted outside of burrows

ground
------
* `ground/active_snake_beta = 1000000.0`: Stiffness of the active snake evolution algorithm for finding the ground line. Larger values lead to straighter lines.
* `ground/active_snake_gamma = 0.1`: Time scale of the active snake evolution algorithm for finding the ground line. Too large gammas may lead to instabilities in the algorithm, while too small gammas may cause a very slow convergence.
* `ground/adaptation_interval = 100`: How often is the ground profile adapted
* `ground/frame_margin = 50`: Width of the margin to the frame in which the ground profile is not determined
* `ground/grabcut_uncertainty_margin = 50`: Width of the region around the estimated profile, in which the GrabCut algorithm may optimize
* `ground/length_max = 1500`: Maximal length of the ground profile above which it is rejected
* `ground/point_spacing = 20`: Spacing of the support points describing the ground profile
* `ground/ridge_width = 5`: Width of the ground profile ridge
* `ground/slope_detector_max_factor = 0.4`: Factor important in the ridge detection step, where the ridge is roughly located by looking at vertical line scans and points with large slopes are located. The smaller this factor, the more such points are detected and the further up the profile is estimated to be
* `ground/slope_max = 3`: Maximal slope of the side ridges
* `ground/smoothing_sigma = 1000`: Standard deviation for Gaussian smoothing over time
* `ground/template = `: Name of the ground template stored in the assets directory. If the template is not given or could not be found, an alternative method based on line scans is used.
* `ground/template_aspect_factors = [ 0.7  0.8  0.9  1.   1.1  1.2  1.3]`: Different factors to try for scaling the template aspect ratio
* `ground/template_margin = 40`: Margin on the top and the bottom of the template.
* `ground/template_width_factors = [ 0.7   0.75  0.8   0.85  0.9   0.95  1.  ]`: Different factors to try for scaling the template width with respect to the cage width.
* `ground/template_width_fraction = 0.8`: Fraction of the full template width that is used for matching.

logging
-------
* `logging/enabled = True`: Flag indicating whether logging is enabled
* `logging/folder = logging/`: Folder to which the log file is written
* `logging/level_file = INFO`: Level of messages to log to file if folder is set [standard python logging levels]
* `logging/level_stderr = INFO`: Level of messages to log to stderr [standard python logging levels]

mouse
-----
* `mouse/activity_smoothing_interval = 54000`: The standard deviation of the Gaussian that is used for smoothing temporal data that is associated with activity measurements.
* `mouse/area_max = 5000`: Maximal area of a feature to be considered in tracking
* `mouse/area_mean = 700`: Mean area of a mouse, which is used to score the mouse
* `mouse/area_min = 100`: Minimal area of a feature to be considered in tracking
* `mouse/digging_rate_time_min = 1800`: Minimal time span the mouse has to be digging before we calculate a digging rate.
* `mouse/intensity_threshold = 1`: Determines how much brighter than the background (usually the sky) the mouse has to be. This value is measured in terms of standard deviations of the sky color
* `mouse/max_count = 1`: Maximal number of mice to be found. Most of the code has only been tested with `max_count = 1`, but we eventually want to extend this to more mice.
* `mouse/max_rel_area_change = 0.5`: Maximal area change allowed between consecutive frames
* `mouse/model_radius = 25`: Radius of the mouse model
* `mouse/moving_threshold_cm_sec = 5`: The threshold value of the speed above which the mouse is considered to be moving.
* `mouse/speed_max = 30`: Maximal speed of the mouse

output
------
* `output/folder = results/`: Folder to which the YAML and HDF5 result files are written
* `output/hdf5_compression = gzip`: Compression algorithm to be used for the HDF5 data. Possible options might be None, "gzip", "lzf", and "szip".
* `output/output_period = 1`: How often are frames written to the output file or shown on the screen
* `video`
  * `output/video/crop_border_buffer = 5`: Size by which the cropping rectangle is extended when creating a cropped movie.
  * `output/video/folder_underground = results/underground_video/`: Folder to which the underground video is written
  * `output/video/extension = .mov`: File extension used for debug videos
  * `output/video/underground_video_length = 36000`: Typical length of the underground video in number of frames
  * `output/video/enabled = True`: Flag determining whether the final video should be produced
  * `output/video/period = 100`: How often are frames written to the output file
  * `output/video/codec = libx264`: ffmpeg video codec used for debug videos
  * `output/video/underground_display_item = {time} [{frame}]`: The data that is displayed in the underground video. Placeholders like `{time}` and `{frame}` are replaced by the data of the current frame.
  * `output/video/folder = results/`: Folder to which the result video is written
  * `output/video/bitrate = 2000k`: Bitrate used for debug videos
  * `output/video/mouse_trail_length = 1000`: The length of the trail indicating the mouse position in the past

predug
------
* `predug/debug_with_lines = True`: Flag indicating whether lines should be drawn on the debug image of the predug.
* `predug/locate_predug = True`: Flag determining whether the predug should be located.
* `predug/location = auto`: Where the predug is located. Can be one of [`left`, `right`, `auto`]. For `auto`, the predug is searched on both sides.
* `predug/scale_predug = True`: Flag indicating whether the predug template will be scaled to the sizes given in `predug/template_width` and `predug/template_height`.
* `predug/search_height_factor = 1`: Determines the height of the area in which the predug is searched for. Half the height is this factor times the maximal vertical span of the ground line.
* `predug/search_width_factor = 0.75`: Determines the width of the area in which the predug is searched for. Half the width is this factor times the width of the valley defined by the ground line.
* `predug/simplify_threshold = 5`: Threshold value for simplifying the contour line of the predug.
* `predug/template_file = predug.yaml`: Name of the template for detecting the predug.
* `predug/template_height = 100`: Width of the predug template. This will be scaled to the right dimensions
* `predug/template_width = 100`: Width of the predug template. This will be scaled to the right dimensions
* `predug/wait_interval = 300`: The time period after which the predug is detected.

project
-------
* `project/symlink_folder = None`: If set, a symlink pointing to the base_folder will be created in this directory when a project is created.
* `python_paths = ['__video_analysis_path__', '__project_path__']`: List of paths that will be appended to the python path.

resources
---------
* `resources/notification_email = dzwicker@seas.harvard.edu`: Email address of the user to be notified in case of problems.
* `pass0`
  * `resources/pass0/cores = 1`: Number of cores for pass 0
  * `resources/pass0/memory = 1000`: Maximal RAM per core for pass 0 [in MB]
  * `resources/pass0/job_id = None`: Job id of pass 0
  * `resources/pass0/time = 600`: Maximal computation minutes for pass 0
* `pass1`
  * `resources/pass1/cores = 3`: Number of cores for pass 1
  * `resources/pass1/memory = 1000`: Maximal RAM per core for pass 1 [in MB]
  * `resources/pass1/job_id = None`: Job id of pass 1
  * `resources/pass1/time = 3000`: Maximal computation minutes for pass 1
* `pass2`
  * `resources/pass2/cores = 1`: Number of cores for pass 2
  * `resources/pass2/memory = 8000`: Maximal RAM per core for pass 2 [in MB]
  * `resources/pass2/job_id = None`: Job id of pass 2
  * `resources/pass2/time = 1500`: Maximal computation minutes for pass 2
* `pass3`
  * `resources/pass3/cores = 2`: Number of cores for pass 3
  * `resources/pass3/memory = 1000`: Maximal RAM per core for pass 3 [in MB]
  * `resources/pass3/job_id = None`: Job id of pass 3
  * `resources/pass3/time = 1800`: Maximal computation minutes for pass 3
* `pass4`
  * `resources/pass4/cores = 2`: Number of cores for pass 4
  * `resources/pass4/memory = 2000`: Maximal RAM per core for pass 4 [in MB]
  * `resources/pass4/job_id = None`: Job id of pass 4
  * `resources/pass4/time = 1500`: Maximal computation minutes for pass 4
* `pass7`
  * `resources/pass7/cores = 2`: Number of cores for pass 7
  * `resources/pass7/memory = 2000`: Maximal RAM per core for pass 7 [in MB]
  * `resources/pass7/job_id = None`: Job id of pass 7
  * `resources/pass7/time = 3000`: Maximal computation minutes for pass 7
* `pass9`
  * `resources/pass9/cores = 2`: Number of cores for pass 9
  * `resources/pass9/memory = 2000`: Maximal RAM per core for pass 9 [in MB]
  * `resources/pass9/job_id = None`: Job id of pass 9
  * `resources/pass9/time = 3000`: Maximal computation minutes for pass 9
* `resources/slurm_partition = general`: Name of the slurm partition to use for submitting jobs

tracking
--------
* `tracking/end_node_interval = 1000`: What time duration do we consider for start and end nodes
* `tracking/initial_score_threshold = 1000`: Initial threshold for building the tracking graph
* `tracking/max_track_count = 5000`: Maximal number of tracks that can be connected. If there are more tracks, we throw out small tracks until the count decreased to the one given here.
* `tracking/maximal_gap = 10`: Maximal gap length where we will use linear interpolation to determine the mouse position
* `tracking/maximal_jump = 50`: Maximal distance between two tracks where we will use linear interpolation to determine the intermediated mouse positions.
* `tracking/mouse_distance_threshold = 500`: Distance over which an object must move in order to call it a mouse. This is used to identify tracks which surely belong to mice. Graph matching is then used to fill in the gaps.
* `tracking/mouse_min_mean_speed = 0.5`: Minimal average speed an object must have in order to be surely considered as a mouse. This is introduced to prevent stationary objects to be called a mouse.
* `tracking/moving_threshold = 1`: Threshold speed above which an object is said to be moving
* `tracking/moving_window = 200`: Number of consecutive frames used for motion detection
* `tracking/object_count_max = 7`: Maximal number of objects allowed in a single frame. If there are more objects, the entire frame is discarded
* `tracking/position_smoothing_window = 5`: The number of frames over which the mouse position is smoothed in order to calculate its velocity
* `tracking/score_threshold_max = 10000000000.0`: Maximal threshold above which the graph based tracking is aborted.
* `tracking/splitting_duration_min = 10`: Track duration above which two overlapping tracks are split
* `tracking/time_scale = 10`: Time duration of not seeing the mouse after which we do not know where it is anymore
* `tracking/tolerated_overlap = 50`: How much are two consecutive tracks allowed to overlap
* `tracking/weight = 0.5`: Relative weight of distance vs. size of objects for matching them
* `use_threads = True`: Determines whether multithreading is used in analyzing the videos. Generally, multithreading should speed up the analysis, but this is not always the case, especially for small videos, where the thread overhead is large.

video
-----
* `video/blur_method = gaussian`: The method to be used for reducing noise in the video. The supported methods are `mean`, `gaussian`, `bilateral`, in increasing complexity, i.e. decreasing speed.
* `video/blur_radius = 3`: Radius of the blur filter to remove noise
* `video/blur_sigma_color = 0`: Standard deviation in color space of the bilateral filter
* `video/cropping_rect = None`: Rectangle to which the video is cropped. This can be either four numbers [left, top, width, height] or some string like 'upper left', 'lower right', etc.
* `video/filename_pattern = raw_video/*.MTS`: Filename pattern used to look for videos
* `video/folder_temporary = None`: Folder in which the video should be stored temporarily, e.g. to speed up the analysis.
* `video/frames = None`: Frames of the video which are analyzed [start and end index should be given]
* `video/frames_skip = 0`: Number of frames that are skipped before starting the analysis. This value is only considered if `video/frames` is None.
* `video/initial_adaptation_frames = 100`: Number of initial frames to skip during analysis
* `video/rotation = 0`: Specifies how much the video will be rotated in counter-clockwise direction. The value specified will be multiplied by 90 degrees to specify the amount of rotation.
* `video_parameters`
  * `video/video_parameters/seek_method = auto`: Method used for seeking in videos. Can be any of ['exact', 'keyframe', 'auto']. If 'auto', the method is determined based on the ffmpeg version.
  * `video/video_parameters/ffprobe_cache = /Users/zwicker/.videos.sqlite`: File where video information obtained from ffprobe will be stored to prevent multiple runs of ffprobe on the same video
  * `video/video_parameters/video_info_method = ffprobe`: Determines how video information, like the total number of frames are determined. Possible values are `header` and `ffprobe`. Note that the header information might be inaccurate but using ffprobe requires iterating through the video once.
  * `video/video_parameters/seek_offset = 1`: The time the rough seek is placed before the target in order to make sure a keyframe is hit. This is only used if 'keyframe' is chosen as a 'seek_method'
  * `video/video_parameters/reopen_delay = 0`: Delay in seconds before a video is reopened. This can prevent some problems with filesystems
  * `video/video_parameters/seek_max_frames = 100`: The maximal number of frames that will be seeked by simply iterating the video. If larger jumps are desired, the video will be reopened.

water_bottle
------------
* `water_bottle/remove_from_video = True`: Flag that indicates whether the water bottle should be removed from the video
* `water_bottle/search_region = [0.8, 1.0, 0.0, 0.3]`: Defines the region [x_min, x_max, y_min, y_max] in which the upper left corner of the water bottle rectangle lies. The coordinates are given relative to the cage width and height. This is used to restrict the template matching to a sensible region.
* `water_bottle/template_height = 60`: Width of the water bottle template. This will be scaled to the right dimensions
* `water_bottle/template_image = water_bottle.png`: Name of the template for removing the water bottle from the background estimate.
* `water_bottle/template_width = 60`: Width of the water bottle template. This will be scaled to the right dimensions

Deprecated parameters
====
* `factor_length = 1`: A factor by which all length scales will be scaled.Deprecated since 2014-12-20. Instead, `scale_length` should be used, which will be processed when loading the parameters once
* `ground/curvature_energy_factor = 1`: Relative strength of the curvature energy to the image energy in the snake model of the ground line.Deprecated since 2014-12-19.
* `ground/linescan_length = 50`: Length of the line scan used to determine the ground profile. Deprecated since 2014-12-19
* `ground/snake_energy_max = 10`: Determines the maximal energy the snake is allowed to have. Deprecated since 2014-12-19
* `mouse/moving_threshold_pixel_frame = None`: Deprecated since 2014-12-01.
* `mouse/speed_smoothing_window = 25`: Deprecated since 2014-11-29. Use `tracking/position_smoothing_window` instead.
