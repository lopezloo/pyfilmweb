# -*- coding: utf-8 -*-
from hashlib import md5
import json
import requests

from .utils import *

API_KEY = 'qjcGhW2JnvGT9dfCt3uT_jozR3s'
URL     = 'http://www.filmweb.pl'
URL_CDN = 'http://1.fwcdn.pl'
URL_API = 'https://ssl.filmweb.pl/api'

class Filmweb:
   @staticmethod
   def _request(method, params=['']):
      data_str = '{} [{}]\n'.format(method, ','.join(params))

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
         data = item.split('\\c')
         print(str(data).encode('utf-8'))
         item_type = data[0]
         item_id = data[1]
         item_poster = data[2][:-6]
         if item_type in ['f', 's', 'g', 'p']:
            item_orgname = data[3]
            item_name = data[4]
            item_year = data[6]

            if item_type == 'f':
               item = Film(item_id, item_name, poster = item_poster, name_org = item_orgname, year = item_year)

            elif item_type == 's':
               item = Serial(item_id, item_name, poster = item_poster, name_org = item_orgname, year = item_year)

            elif item_type == 'g':
               item = Videogame(item_id, item_name, poster = item_poster, name_org = item_orgname, year = item_year)

            elif item_type == 'p':
               item = Person(item_id, item_orgname, poster = item_poster)

         elif item_type == 't':
            item = Channel(data[1], data[2])

         items.append(item)

      return items

   @staticmethod
   def get_popular_films():
      status, data = Filmweb._request('getPopularFilms')

      films = []
      for v in data:
         films.append(Film(name=v[0], year=v[1], rate=v[2], votes=v[3], poster=v[5][:-6], uid=v[6]))

      return films

   @staticmethod
   def get_popular_persons():
      status, data = Filmweb._request('getPopularPersons')

      persons = []
      for v in data:
         persons.append(Person(v[0], v[1], v[2][:-6]))

      return persons

   @staticmethod
   def get_top(item_type, genre, worldwide=True):
      assert item_type in ['film', 'serial', 'videogame']
      assert isinstance(genre, str)
      assert isinstance(worldwide, bool)

      # Game genre is sadly ignored
      genre_id = get_genre_id(item_type, genre)
      if not genre_id:
         return False

      # Same as country option
      if item_type == 'videogame' and not worldwide:
         return False

      req = 'top_100_{}s_{}'.format('game' if item_type == 'videogame' else item_type, 'world' if worldwide else 'poland')
      status, data = Filmweb._request('getRankingFilms', [req, str(genre_id)])

      results = []
      for v in data:
         item = None
         if item_type == 'film':
            item = Film(v[0], rate=v[1], votes=v[4])
         elif item_type == 'serial':
            item = Serial(v[0], rate=v[1], votes=v[4])
         elif item_type == 'videogame':
            item = Videogame(v[0], rate=v[1], votes=v[4])

         results.append({
            'item': item,
            'position': v[2],
            'position_prev': v[3]
         })

      return results

class Item:
   def __init__(self, uid, name=None, poster=None, name_org=None, year=None, rate=None, votes=None):
      self.uid = uid
      self.name = name
      self.poster = poster if poster != '' else None
      self.name_org = name_org
      self.year = year
      self.rate = rate
      self.votes = votes

   def __repr__(self):
      return '<Item id: {} name: {} poster: {}>'.format(self.uid, self.name, self.poster)

   @property
   def url(self):
      if self.name and self.year:
         return '{}/{}/{}-{}-{}'.format(URL, self.type, self.name.replace(' ', '+'), self.year, self.uid)
      else:
         return '{}/entityLink?entityName={}&id={}'.format(URL, self.type, self.uid)

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
      elif data[15] == 2:
         item_type = 'videogame'

      data = {
         'name':              data[0],
         'name_org':          data[1],
         'rate':              data[2],
         'votes':             data[3],
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

      # Update object
      self.name = data['name']
      self.year = data['year']
      self.rate = data['rate']
      self.votes = data['votes']
      if data['poster_small']:
         self.poster = data['poster_small'][:-6]

      return data

class Film(Item):
   def __init__(self, uid, name=None, poster=None, name_org=None, year=None, rate=None, votes=None):
      Item.__init__(self, uid, name, poster=poster, name_org=name_org, year=year, rate=rate, votes=votes)

   @property
   def type(self):
      return 'film'

class Serial(Item):
   def __init__(self, uid, name=None, poster=None, name_org=None, year=None, rate=None, votes=None):
      Item.__init__(self, uid, name, poster=poster, name_org=name_org, year=year, rate=rate, votes=votes)

   @property
   def type(self):
      return 'serial'

class Videogame(Item):
   def __init__(self, uid, name=None, poster=None, name_org=None, year=None, rate=None, votes=None):
      Item.__init__(self, uid, name, poster=poster, name_org=name_org, year=year, rate=rate, votes=votes)

   @property
   def type(self):
      return 'videogame'

class Person:
   def __init__(self, uid, name=None, poster=None):
      self.uid = uid
      self.name = name
      self.poster = poster

   @property
   def type(self):
      return 'person'

   @property
   def url(self):
      if self.name:
         return '{}/person/{}'.format(URL, self.name.replace(' ', '.').replace('?', ''))
      else:
         return '{}/entityLink?entityName={}&id={}'.format(URL, self.type, self.uid)

   def get_poster(self, size='small'):
      if self.poster:
         return '{}/p{}.{}.jpg'.format(URL_CDN, self.poster, 0 if size == 'tiny' else 1)

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
         return '{}/program-tv/{}'.format(URL, self.name.replace(' ', '+'))
      else:
         return '{}/entityLink?entityName={}&id={}'.format(URL, self.type, self.uid)

   def get_icon(self, size='small'):
      return '{}/channels/{}.{}.png'.format(URL_CDN, self.uid, channel_icon_sizes[size])
