'''
Created on Dec 19, 2014

@author: David Zwicker <dzwicker@seas.harvard.edu>
'''

from __future__ import division

import collections
import datetime
import os
import warnings

import numpy as np
import h5py



def get_chunk_size(shape, num_elements):
    """ tries to determine an optimal chunk size for an array with a given 
    shape by chunking the longest axes first """
    chunks = list(shape)
    while np.prod(chunks) > num_elements:
        dim_long = np.argmax(chunks) #< get longest dimension
        chunks[dim_long] = 1 #< temporary set to one for np.prod 
        chunks[dim_long] = max(1, num_elements // np.prod(chunks))
    return tuple(chunks)
    


class LazyValue(object):
    """ base class that represents a value that is only loaded when it is
    accessed """
    def load(self):
        raise NotImplementedError
    


class LazyHDFValue(LazyValue):
    """ class that represents a value that is only loaded from HDF when it is
    accessed """
    chunk_elements = 10000
    compression = None
    

    def __init__(self, data_cls, key, hdf_filename):
        self.data_cls = data_cls
        self.key = key
        self.hdf_filename = hdf_filename
        

    def __repr__(self):
        return '%s(data_cls=%s, key="%s", hdf_filename="%s")' % (
                    self.__class__.__name__, self.data_cls.__name__,
                    self.key, self.hdf_filename)
        
        
    def set_hdf_folder(self, hdf_folder):
        """ replaces the folder of the hdf file """
        hdf_name = os.path.basename(self.hdf_filename)
        self.hdf_filename = os.path.join(hdf_folder, hdf_name)
        
        
    def get_yaml_string(self):
        """ returns a representation of the object as a single string, which
        is useful for referencing the object in YAML """
        hdf_name = os.path.basename(self.hdf_filename)
        return '@%s:%s' % (hdf_name, self.key)
        
        
    @classmethod
    def create_from_yaml_string(cls, value, data_cls, hdf_folder):
        """ create an instance of the class from the yaml string and additional
        information """

        # consistency check
        if value[0] != '@':
            raise RuntimeError('Item with lazy loading does not start with `@`')
        
        # read the link
        data_str = value[1:] # strip the first character, which should be an @
        hdf_name, key = data_str.split(':')
        hdf_filename = os.path.join(hdf_folder, hdf_name)
        return cls(data_cls, key, hdf_filename)
        
    
    @classmethod    
    def create_from_data(cls, key, data, hdf_filename):
        """ store the data in a HDF file and return the storage object """
        data_cls = data.__class__
        with h5py.File(hdf_filename, 'a') as hdf_file:
            # delete possible previous key to have a clean storage
            if key in hdf_file:
                del hdf_file[key]
                
            # save actual data as an array
            data_array = np.asarray(data.to_array())
            if cls.compression is None or data_array.size < cls.chunk_elements:
                hdf_file.create_dataset(key, data=data_array, track_times=True)
            else:
                chunks = get_chunk_size(data_array.shape, cls.chunk_elements)
                hdf_file.create_dataset(key, data=data_array, track_times=True,
                                        chunks=chunks, compression=cls.compression)
                
            # add attributes to describe data 
            hdf_file[key].attrs['written_on'] = str(datetime.datetime.now())
            if hasattr(data_cls, 'hdf_attributes'):        
                for attr_key, attr_value in data_cls.hdf_attributes.iteritems():
                    hdf_file[key].attrs[attr_key] = attr_value
            
        return cls(data_cls, key, hdf_filename)
    
        
    def load(self):
        """ load the data and return it """
        # open the associated HDF5 file and read the data
        with h5py.File(self.hdf_filename, 'r') as hdf_file:
            data = hdf_file[self.key][:]  #< copy data into RAM
            result = self.data_cls.create_from_array(data)
        
        # create object
        return result



class LazyHDFCollection(LazyHDFValue):
    """ class that represents a collection of values that are only loaded when they are accessed """

    @classmethod    
    def create_from_data(cls, key, data, hdf_filename):
        """ store the data in a HDF file and return the storage object """
        data_cls = data.__class__

        # save a collection of objects to hdf
        with h5py.File(hdf_filename, 'a') as hdf_file:
            # reset the whole structure if it is there
            if key in hdf_file:
                del hdf_file[key]
                
            # create group in case data is empty
            hdf_file.create_group(key)

            # write all objects as individual datasets            
            key_format = '{}/%0{}d'.format(key, len(str(len(data))))
            for index, obj in enumerate(data):
                obj.save_to_hdf5(hdf_file, key_format % index)
    
            hdf_file[key].attrs['written_on'] = str(datetime.datetime.now())
            if hasattr(data_cls, 'hdf_attributes'):        
                for attr_key, attr_value in data_cls.hdf_attributes.iteritems():
                    hdf_file[key].attrs[attr_key] = attr_value

        return cls(data_cls, key, hdf_filename)
    
        
    def load(self):
        """ load the data and return it """
        # open the associated HDF5 file and read the data
        item_cls = self.data_cls.item_class
        with h5py.File(self.hdf_filename, 'r') as hdf_file:
            # iterate over the data and create objects from it
            data = hdf_file[self.key]
            if data:
                result = self.data_cls(item_cls.create_from_array(data[index][:])
                                       for index in sorted(data.keys()))
                # here, we have to use sorted() to iterate in the correct order 
            else: # empty dataset
                result = self.data_cls()
                
        return result



def prepare_data_for_yaml(data):
    """ recursively converts all numpy types to their closest python equivalents """
    if isinstance(data, np.ndarray):
        return data.tolist()
    elif isinstance(data, np.floating):
        return float(data)
    elif isinstance(data, np.integer):
        return int(data)
    elif isinstance(data, collections.MutableMapping):
        return {k: prepare_data_for_yaml(v) for k, v in data.iteritems()}
    elif isinstance(data, (list, tuple)):
        return [prepare_data_for_yaml(v) for v in data]
    elif isinstance(data, LazyHDFValue):
        return data.get_yaml_string()
    elif data is not None and not isinstance(data, (bool, int, float, list, basestring)):
        warnings.warn('Encountered unknown instance of `%s` in YAML preparation' %
                      data.__class__)
    return data