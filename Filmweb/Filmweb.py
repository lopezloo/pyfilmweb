# -*- coding: utf-8 -*-
from hashlib import md5
import json
import requests

from Filmweb.Items import *
from Filmweb import common

def _request(method, params=['']):
   params = [str(v if v is not None else 'null') for v in params]
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
            item = Film(item_id, 'film', item_name, poster=item_poster, name_org=item_orgname, year=item_year)

         elif item_type == 's':
            item = Film(item_id, 'serial', item_name, poster=item_poster, name_org=item_orgname, year=item_year)

         elif item_type == 'g':
            item = Film(item_id, 'videogame', item_name, poster=item_poster, name_org=item_orgname, year=item_year)

         elif item_type == 'p':
            item = Person(item_id, item_orgname, poster=item_poster)

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

def get_top(film_type, genre=None, worldwide=True):
   assert film_type in common.film_types
   assert isinstance(genre, str)
   assert isinstance(worldwide, bool)

   # Game genre is sadly ignored
   genre_id = common.get_genre_id(film_type, genre) if genre else None

   # Same as country option
   if film_type == 'videogame' and not worldwide:
      return False

   req = 'top_100_{}s_{}'.format('game' if film_type == 'videogame' else film_type, 'world' if worldwide else 'poland')
   status, data = Filmweb._request('getRankingFilms', [req, genre_id])

   results = []
   for v in data:
      results.append({
         'film': Film(v[0], type=film_type, rate=v[1], votes=v[4]),
         'position': v[2],
         'position_prev': v[3]
      })

   return results

def get_upcoming_films(above_date=None):
   # Nice typo, Filmweb!
   status, data = Filmweb._request('getUpcommingFilms', [above_date])

   results = []
   for day in data:
      films = []
      for v in day[1]:
         films.append({
            'film': Film(uid=v[0], name=v[1], year=v[2], poster=v[3][:-6] if v[3] else None),
            'person_names': [v[4], v[5]]
         })

      result = {
         'date': common.str_to_date(day[0]),
         'films': films
      }
      results.append(result)

   return results

def get_born_today_persons():
   status, data = Filmweb._request('getBornTodayPersons')
   results = []
   for v in data:
      results.append(Person(uid=v[0], name=v[1], poster=v[2][:-6] if v[2] else None, date_birth=common.str_to_date(v[3]), date_death=common.str_to_date(v[4])))
   return results
