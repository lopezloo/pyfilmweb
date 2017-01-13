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
      params = [str(v) for v in params]
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
      return status

   @staticmethod
   def search(text):
      r = requests.get('{}/search/live'.format(URL), params={'q': text})

      items = []
      for item in r.text.split('\\a'):
         data = item.split('\\c')
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

      result = {
         'name':              data[0],
         'name_org':          data[1],
         'rate':              data[2],
         'votes':             data[3],
         'genres':            data[4].split(','),
         'year':              data[5],
         'duration':          data[6],
        #'comments_count':    data[7], # leftover, always 0
         'discussion_url':    data[8],
         'has_review':        data[9],
         'has_description':   data[10],
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
      self.name = result['name']
      self.year = result['year']
      self.rate = result['rate']
      self.votes = result['votes']
      if result['poster_small']:
         self.poster = result['poster_small'][:-6]

      return result

   def get_persons(self, role_type, offset=0):
      assert role_type in person_role_types
      assert isinstance(offset, int)
      limit = 50 # Sadly ignored
      status, data = Filmweb._request('getFilmPersons', [self.uid, get_role_type_id(role_type), offset, limit])

      results = []
      for v in data:
         results.append({
            'person': Person(uid=v[0], name=v[3], poster=v[4][:-6] if v[4] else None),
            'role': v[1],
            'role_extra_info': v[2]
         })
      return results

   def get_images(self, offset=0):
      limit = 100 # ignored
      status, data = Filmweb._request('getFilmImages', [self.uid, offset, limit])
      results = []
      for v in data:
         persons = []
         # If this image has marked persons on it
         if v[1]:
            for pdata in v[1]:
               persons.append(Person(uid=pdata[0], name=pdata[1], poster=pdata[2][:-6] if pdata[2] else None))

         results.append(Image(path=v[0][:-6], sources=v[2], associated_item=self, persons=persons))

      return results

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

   def get_platforms(self):
      status, data = Filmweb._request('getGameInfo', [self.uid])
      if data:
         return data[0].split(', ')

class Person:
   def __init__(self, uid, name=None, poster=None, rate=None, votes=None):
      self.uid = uid
      self.name = name
      self.poster = poster
      self.rate = rate
      self.votes = votes

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

   def get_biography(self):
      status, data = Filmweb._request('getPersonBiography', [self.uid])
      if data:
         return data[0]

   def get_info(self):
      status, data = Filmweb._request('getPersonInfoFull', [self.uid])

      result = {
         'name': data[0],
         'birth_date': data[1],
         'birth_place': data[2],
         'votes': data[3],
         'rate': data[4],
         'poster': data[5][:-6] if data[5] else None,
         'has_bio': data[6],
         'film_known_for': Film(uid=data[7]) if data[7] else None,
         'sex': data[8],
         'name_full': data[9],
         'death_date': data[10],
         'height': data[11],
      }

      # Update object
      self.name = result['name']
      self.poster = result['poster']
      self.rate = result['rate']
      self.votes = result['votes']

      return result

   def get_images(self, offset=0):
      limit = 100 # ignored
      status, data = Filmweb._request('getPersonImages', [self.uid, offset, limit])

      results = []
      for v in data:
         persons = []
         # If this image has marked persons on it
         if v[1]:
            for pdata in v[1]:
               persons.append(Person(uid=pdata[0], name=pdata[1], poster=pdata[2][:-6] if pdata[2] else None))

         results.append(Image(path=v[0][:-6], sources=v[2], associated_item=Item(uid=v[3], name=v[4]), persons=persons))

      return results


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

class Image:
   def __init__(self, path, associated_item=None, persons=[], sources=[]):
      self.path = path
      self.associated_item = associated_item
      self.persons = persons
      self.sources = sources

   def get_url(self, size='medium'):
      return '{}/ph{}.{}.jpg'.format(URL_CDN, self.path, image_sizes[size])
