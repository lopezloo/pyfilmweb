# -*- coding: utf-8 -*-

from Filmweb import common

class Image:
   def __init__(self, path, associated_item=None, persons=[], sources=[]):
      self.path = path
      self.associated_item = associated_item
      self.persons = persons
      self.sources = sources

   def get_url(self, size='medium'):
      return '{}/ph{}.{}.jpg'.format(common.URL_CDN, self.path, image_sizes[size])
