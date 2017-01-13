# -*- coding: utf-8 -*-
from hashlib import md5
import json
import requests

from Filmweb.Film import *
from Filmweb.Channel import *
from Filmweb.Image import *
from Filmweb.Person import *
from Filmweb import common

def _request(method, params=['']):
   params = [str(v) for v in params]
   data_str = '{} [{}]\n'.format(method, ','.join(params))

   sig = '1.0,'+md5((data_str + 'android' + common.API_KEY).encode()).hexdigest()
   rparams = {
      'version': 1.0,
      'appId': 'android',
      'signature': sig,
      'methods': data_str
   }
   r = requests.get(common.URL_API, params=rparams)

   data = r.text.split('\n')
   status = data[0]
   if status == 'ok':
      return status, json.loads(data[1][:-7])
   return status

def search(text):
   r = requests.get('{}/search/live'.format(common.URL), params={'q': text})

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
            item = Film(item_id, type='film', item_name, poster = item_poster, name_org = item_orgname, year = item_year)

         elif item_type == 's':
            item = Film(item_id, type='serial', item_name, poster = item_poster, name_org = item_orgname, year = item_year)

         elif item_type == 'g':
            item = Film(item_id, type='videogame', item_name, poster = item_poster, name_org = item_orgname, year = item_year)

         elif item_type == 'p':
            item = Person(item_id, item_orgname, poster = item_poster)

      elif item_type == 't':
         item = Channel(data[1], data[2])

      items.append(item)

   return items

def get_popular_films():
   status, data = Filmweb._request('getPopularFilms')

   films = []
   for v in data:
      films.append(Film(name=v[0], year=v[1], rate=v[2], votes=v[3], poster=v[5][:-6], uid=v[6]))

   return films

def get_popular_persons():
   status, data = Filmweb._request('getPopularPersons')

   persons = []
   for v in data:
      persons.append(Person(v[0], v[1], v[2][:-6]))

   return persons

def get_top(film_type, genre, worldwide=True):
   assert film_type in common.film_types
   assert isinstance(genre, str)
   assert isinstance(worldwide, bool)

   # Game genre is sadly ignored
   genre_id = common.get_genre_id(film_type, genre)
   if not genre_id:
      return False

   # Same as country option
   if film_type == 'videogame' and not worldwide:
      return False

   req = 'top_100_{}s_{}'.format('game' if film_type == 'videogame' else film_type, 'world' if worldwide else 'poland')
   status, data = Filmweb._request('getRankingFilms', [req, str(genre_id)])

   results = []
   for v in data:
      film = None
      if film_type == 'film':
         film = Film(v[0], type=film_type, rate=v[1], votes=v[4])
      elif film_type == 'serial':
         film = Film(v[0], type=film_type, rate=v[1], votes=v[4])
      elif film_type == 'videogame':
         film = Film(v[0], type=film_type, rate=v[1], votes=v[4])

      results.append({
         'film': film,
         'position': v[2],
         'position_prev': v[3]
      })

   return results
