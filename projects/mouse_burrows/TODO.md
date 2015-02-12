* Write a manual of assumption we make about the videos in order to track everything
* Gather more statistics about why certain parts of the algorithm failed
* Refine the centerline by moving the points more toward the actual center
	- this could be done by segmenting the current centerline in equally spaced segments
	- each inner point on this center line can be put at the midpoint between the outlines
		to prevent problems, the point should be displaced by at most 0.5*burrow_width
	- Alternatively, find centerline by using active snake guided by current centerline and distance map
* Pass1:
    - Make sure that background video is always produced when we need it later
* Pass2:
* Pass3:
    - detect when burrow has multiple exits and adjust the centerline accordingly
* Pass4:
	- connect two burrows that face each other (which happens for burrows with two exits)
* Fix detection status of ffmpeg-errors that we recovered from
    => When checking for ffmpeg-errors, check also whether they are followed by
    an "FFmpeg error occurred! Repeat the analysis." and do not issue a warning
    in that case  

Performance improvements:
-------------------------
* Make sure that images and masks are not copied to often (rather use internal cache structures, which should be faster)
	- Do operations in place as often as possible
* Generally cache all kernels for morphological operations, since these are costly to make
* Minimize writing to home directory and use /n/holyscratch instead
    - copy files at the end of the job


Low priority enhancements:
--------------------------