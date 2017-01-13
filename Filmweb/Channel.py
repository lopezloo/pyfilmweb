# -*- coding: utf-8 -*-

from Filmweb import common

class Channel:
   def __init__(self, uid, name=None):
      self.uid = uid
      self.name = name

   @property
   def type(self):
      return 'channel'

   @property
   def url(self):
      if self.name:
         return '{}/program-tv/{}'.format(common.URL, self.name.replace(' ', '+'))
      else:
         return '{}/entityLink?entityName={}&id={}'.format(common.URL, self.type, self.uid)

   def get_icon(self, size='small'):
      return '{}/channels/{}.{}.png'.format(common.URL_CDN, self.uid, common.channel_icon_sizes[size])
