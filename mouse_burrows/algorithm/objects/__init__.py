"""
This package contains classes that represent objects which can be tracked
""" 

from .burrow import Burrow, BurrowTrack, BurrowTrackList
from .ground import GroundProfile, GroundProfileList, GroundProfileTrack
from .moving_objects import MovingObject, ObjectTrack,ObjectTrackList
from .mouse import MouseTrack

# define a simple object representing the cage rectangle
from video.analysis.shapes import Rectangle
Cage = Rectangle