# -*- coding: utf-8 -*-

from Filmweb import Filmweb, common
from Filmweb.Film import *

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

   # date: max +13, min -1 days
   def get_schedule(self, date):
      status, data = Filmweb._request('getTvSchedule', [self.uid, str(date)])

      results = []
      for v in data:
         results.append({
            'uid': v[0],
            'title': v[1],
            'description': v[2],
            'time': v[3], # HH-MM
            'type': v[4],
            'film': Film(uid=v[5], name=v[1], year=v[6], duration=v[7], poster=v[8][:-6] if v[8] else None) if v[5] else None
         })
      return results
