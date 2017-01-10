# -*- coding: utf-8 -*-
from hashlib import md5
import json
import requests

API_KEY = 'qjcGhW2JnvGT9dfCt3uT_jozR3s'
URL     = 'http://www.filmweb.pl'
URL_CDN = 'http://1.fwcdn.pl'
URL_API = 'https://ssl.filmweb.pl/api'

class Filmweb:
   @staticmethod
   def _request(method, params):
      data_str = ''
      for arg in params:
         data_str += '{} [{}]\n'.format(method, arg)

      sig = '1.0,'+md5((data_str + 'android' + API_KEY).encode()).hexdigest()
      rparams = {
         'version': 1.0,
         'appId': 'android',
         'signature': sig,
         'methods': data_str
      }
      r = requests.get(URL_API, params=rparams)
      data = r.text.split('\n')
      status = data[0]
      if status == 'ok':
         return status, json.loads(data[1][:-7])

   @staticmethod
   def search(text):
      r = requests.get('{}/search/live'.format(URL), params={'q': text})

      items = []
      for item in r.text.split('\\a'):
         item_data = item.split('\\c')
         item_type = item_data[0]
         item_id = item_data[1]
         item_poster = item_data[2][:-6]
         item_orgname = item_data[3]
         item_name = item_data[4]
         item_year = item_data[6]

         if item_type == 'f':
            item = Film(item_id, item_name, poster = item_poster, name_org = item_orgname, year = item_year)

         elif item_type == 's':
            item = Serial(item_id, item_name, poster = item_poster, name_org = item_orgname, year = item_year)

         elif item_type == 'g':
            item = Videogame(item_id, item_name, poster = item_poster, name_org = item_orgname, year = item_year)

         elif item_type == 'p':
            item = Person(item_id, item_orgname, poster = item_poster)

         items.append(item)

      return items

# Poster sizes for film/serial/videogame
poster_sizes = {
   'large':  3,
   'big':    5,
   'normal': 6,
   'small':  2,
   'mini':   4,
   'tiny':   0,
   'square': 1
}

class Item:
   def __init__(self, uid, name=None, poster=None, name_org=None, year=None):
      self.uid = uid
      self.name = name
      self.poster = poster if poster != '' else None
      self.name_org = name_org
      self.year = year

   def __repr__(self):
      return '<Item id: {} name: {} poster: {}>'.format(self.uid, self.name, self.poster)

   @property
   def url(self):
      return '{}/{}/{}-{}-{}'.format(URL, self.type, self.name.replace(' ', '+') if self.name else 'A', self.year or '0000', self.uid)

   def get_poster(self, size='small'):
      if self.poster:
         return '{}/po{}.{}.jpg'.format(URL_CDN, self.poster, poster_sizes[size])

   def get_description(self):
      status, data = Filmweb._request('getFilmDescription', [self.uid])
      return data[0]

   def get_info(self):
      status, data = Filmweb._request('getFilmInfoFull', [self.uid])

      item_type = 'film'
      if data[15] == 1:
         item_type = 'serial'
      elif data[16] == 2:
         item_type = 'videogame'

      data = {
         'name':              data[0],
         'name_org':          data[1],
         'rate':              data[2],
         'voters':            data[3],
         'genres':            data[4].split(','),
         'year':              data[5],
         'duration':          data[6],
        #'unk':               data[7],
         'discussion_url':    data[8],
        #'unk':               data[9],
        #'unk':               data[10],
         'poster_small':      data[11],
         'trailers':          data[12],
         'premiere':          data[13], # YYYY-MM-DD
         'premiere_local':    data[14], # YYYY-MM-DD
         'type':              item_type,
         'season_count':      data[16],
         'episode_count':     data[17],
         'countries':         data[18].split(','),
         'description_short': data[19]
      }
      return data

class Film(Item):
   def __init__(self, uid, name=None, poster=None, name_org=None, year=None):
      super(Film, self).__init__(uid, name, poster=poster, name_org=name_org, year=year)

   @property
   def type(self):
      return 'film'

class Serial(Item):
   def __init__(self, uid, name=None, poster=None, name_org=None, year=None):
      super(Serial, self).__init__(uid, name, poster=poster, name_org=name_org, year=year)

   @property
   def type(self):
      return 'serial'

class Videogame(Item):
   def __init__(self, uid, name=None, poster=None, name_org=None, year=None):
      super(Videogame, self).__init__(uid, name, poster, name_org)

   @property
   def type(self):
      return 'videogame'

class Person:
   def __init__(self, uid, name=None, poster=None):
      self.uid = uid
      self.name = name
      self.poster = poster

   @property
   def url(self):
      return '{}/person/{}'.format(URL, self.name.replace(' ', '.'))

   def get_poster(self, size='small'):
      if self.poster:
         return '{}/p{}.{}.jpg'.format(URL_CDN, self.poster, 0 if size == 'tiny' else 1)
