#!/usr/bin/env python

"""
Module: image_processor
Author: Ken Chatfield <ken@robots.ox.ac.uk>
        Kevin McGuinness <kevin.mcguinness@eeng.dcu.ie>
Created on: 19 Oct 2012
"""

import os
import urlparse

import PIL
import imutils
import logging

log = logging.getLogger(__name__)

class FilterException(Exception):
    pass


class ImageProcessorSettings(object):
    """Settings class for ImageProcessor

    Defines the following setting groups:
    
        filter - settings related to filtering out of images from further processing
        conversion - settings related to the standardization and re-writing of
            downloaded images
        thumbnail - settings related to the generation of thumbnails for downloaded images
    """

    def __init__(self):
        self.filter = dict(min_width = 1,
                           min_height = 1,
                           max_width = 10000,
                           max_height = 10000,
                           max_size_bytes = 2*4*1024*1024) #2 MP

        self.conversion = dict(format = 'jpg',
                               suffix = '-clean')

        self.thumbnail = dict(format = 'jpg',
                              suffix = '-thumb',
                              width = 90,
                              height = 90,
                              pad_to_size = True)

    
class ImageProcessor(object):
    """Base class providing utility methods for cleaning up images downloaded
    from the web. Requires the subclass to define the following:

    Attributes:
        opts - ImageProcessorSettings class containing settings for the image processor
    """

    # Create filenames
    
    def _filename_from_urldata(self, urldata):
        extension = os.path.splitext(urlparse.urlparse(urldata['url']).path)[1]
        fn = urldata['image_id'] + extension
        return fn

    def _clean_filename_from_filename(self, fn):
        return (os.path.splitext(fn)[0] +
                self.opts.conversion['suffix'] + '.' +
                self.opts.conversion['format'].lower())

    def _thumb_filename_from_filename(self, fn):
        fmt = '{}{}-{}x{}.{}'
        name = os.path.splitext(fn)[0]
        suffix = self.opts.thumbnail['suffix']
        width, height = self.opts.thumbnail['width'], self.opts.thumbnail['height']
        extension = self.opts.thumbnail['format'].lower()
        return fmt.format(name, suffix, width, height, extension)

    # Process image and standardize it
    def process_image(self, fn):
        """Process a single image, saving a cleaned up version of the image + thumbnail

        Args:
            fn: the filename of the image to process

        Returns:
            A tuple (clean_fn, thumb_fn) containing the filenames of the saved
            cleaned up image and thumbnail
            
        """
        im = imutils.LazyImage(fn)
        self._filter_image(fn)

        # write converted version
        clean_fn = self._clean_filename_from_filename(fn)
        if not imutils.image_exists(clean_fn):
            imutils.save_image(clean_fn, im.image)
        else:
            log.info('Converted image available: %s', clean_fn)

        # write thumbnail
        thumb_fn = self._thumb_filename_from_filename(fn)
        if not imutils.image_exists(thumb_fn):
            thumbnail = imutils.create_thumbnail(im.image,
                                                 (self.opts.thumbnail['width'],
                                                  self.opts.thumbnail['height']))
            imutils.save_image(thumb_fn, thumbnail)
        else:
            log.info('Thumbnail image available: %s', thumb_fn)

        return clean_fn, thumb_fn

    def _filter_image(self, fn):
        # This is faster than reading the full image into memory: the PIL open
        # function is lazy and only reads the header until the data is requested
        im = PIL.Image.open(fn)
        w, h = im.size
        # This is an in memory size *estimate*
        nbytes = w * h * len(im.mode)

        if w < self.opts.filter['min_width']:
            raise FilterException, 'w < min_width'
        if h < self.opts.filter['min_height']:
            raise FilterException, 'h < min_height'
        if w > self.opts.filter['max_width']:
            raise FilterException, 'w > max_width'
        if h > self.opts.filter['max_height']:
            raise FilterException, 'h > max_height'
        if nbytes > self.opts.filter['max_size_bytes']:
            raise FilterException, 'nbytes > max_size_bytes'
