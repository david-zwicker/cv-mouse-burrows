cv-mouse-burrows
================

This project is about tracking mice during burrowing activities. It analyzes
the dynamics of the mouse, the ground line, and the actual burrows.


Necessary python packages:

Package     | Usage                                      
------------|-------------------------------------------
cv2         | OpenCV python bindings for computer vision 
h5py        | HDF5 python binding for writing out data    
matplotlib  | Plotting library used for output           
networkx    | Graph library for graph based tracking
numpy       | Array library used for manipulating data
scipy       | Miscellaneous scientific functions
shapely     | Library for manipulating geometric shapes
yaml        | YAML binding for writing out data


Optional python packages that can be installed via pip:

Package      | Usage                                      
-------------|-------------------------------------------
dateutil     | Being less picky about date formats
descartes    | Debug plotting of shapes
faulthandler | Detecting low level crashes
grip         | Converting markdown to html 
json         | For reading the output of ffprobe
pandas       | Writing results to csv files
pint         | Reporting results with physical units
sharedmem    | Showing the videos in a separate process while iterating
thinning     | package for thinning binary images
tqdm         | Showing a progress bar while iterating



The MIT License (MIT) [OSI Approved License]
--------------------------------------------

Copyright (c) 2014 Zulko

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
