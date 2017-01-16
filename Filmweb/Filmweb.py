# -*- coding: utf-8 -*-
from hashlib import md5
import json
import requests

from Filmweb.Items import *
from Filmweb import common, exceptions

def _request(method, params=[]):
   params = [v if v is not None else 'null' for v in params]
   data_str = '{} {}\n'.format(method, str(params))

   sig = '{},{}'.format(common.API_VER, md5((data_str + 'android' + common.API_KEY).encode()).hexdigest())
   rparams = {
      'version': common.API_VER,
      'appId': 'android',
      'signature': sig,
      'methods': data_str
   }
   r = requests.get(common.URL_API, params=rparams)

   data = r.text.split('\n')
   status = data[0].split(',')

   if status[0] != 'ok':
      d = data[1].split(', ')
      error_code, error_msg = int(d[0]), d[1]
      raise exceptions.RequestFailed(error_code, error_msg)

   if data[1][:3] == 'exc':
      raise exceptions.RequestFailed('exc', data[1][4:])

   return json.loads(data[1][:-7])

def search(text):
   r = requests.get('{}/search/live'.format(common.URL), params={'q': text})

   items = []
   for item in r.text.split('\\a'):
      v = item.split('\\c')

      item_type = v[0]
      if item_type in ['f', 's', 'g']:
         ftype = 'film'
         if item_type == 's':
            ftype = 'serial'
         elif item_type == 'g':
            ftype = 'videogame'

         item = Film(uid=v[1], type=ftype, name=v[4], poster=v[2][:-6] if v[2] else None, name_org=v[3], year=v[6])

      elif item_type == 'p':
         item = Person(uid=v[1], name=v[3], poster=v[2][:-6] if v[2] else None)

      elif item_type == 't':
         item = Channel(uid=v[1], name=v[2])

      elif item_type == 'c':
         item = Cinema(uid=int(v[1]), name=v[2], city_name=v[3], address=v[4], coords=v[5])

      items.append(item)

   return items

def get_popular_films():
   data = Filmweb._request('getPopularFilms')

   films = []
   for v in data:
      films.append(Film(name=v[0], year=v[1], rate=v[2], votes=v[3], poster=v[5][:-6], uid=v[6]))

   return films

def get_popular_persons():
   data = Filmweb._request('getPopularPersons')

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
      raise ValueError('videogame type doesn\'t support worldwide=False')

   req = 'top_100_{}s_{}'.format('game' if film_type == 'videogame' else film_type, 'world' if worldwide else 'poland')
   data = Filmweb._request('getRankingFilms', [req, genre_id])

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
   data = Filmweb._request('getUpcommingFilms', [above_date])

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
   data = Filmweb._request('getBornTodayPersons')
   results = []
   for v in data:
      results.append(Person(uid=v[0], name=v[1], poster=v[2][:-6] if v[2] else None, date_birth=common.str_to_date(v[3]), date_death=common.str_to_date(v[4])))
   return results

def get_trailers(offset=0, limit=10):
   data = Filmweb._request('getTrailers', [offset, limit])
   results = []
   for v in data:
      img = v[3]
      uid = common.video_img_url_to_uid(img)

      vid_urls = {
         'main': v[4],
         '480p': v[7],
         '720p': v[8]
      }

      film = Film(uid=v[2], name=v[0], poster=v[5][:-6] if v[5] else None)
      results.append(
         Video(film=film, date=common.str_to_date(v[1]), img=img, name=v[6], min_age=v[9], vid_uid=vid_uid, vid_urls=vid_urls)
      )
   return results

def get_popular_trailers(offset=0, limit=10):
   data = Filmweb._request('getPopularTrailers', [offset, limit])
   results = []
   for v in data:
      img = v[3]
      uid = common.video_img_url_to_uid(img)

      vid_urls = {
         'main': v[4],
         '480p': v[8],
         '720p': v[7]
      }

      film = Film(uid=v[2], name=v[0], poster=v[5][:-6] if v[5] else None)
      results.append(
         Video(uid=uid, name=v[6], film=film, date=common.str_to_date(v[1]), img=img, min_age=v[9], vid_urls=vid_urls)
      )
   return results

# this gonna throw RequestFailed(20, 'IllegalArgumentException') if category is unknown
# and doesn't accept trailers category
def get_filmweb_productions(category, offset=0, limit=100):
   unk = -1
   category = category.lower().replace(' ', '_')
   data = Filmweb._request('getFilmwebProductions', [unk, category, offset, limit])

   result = {
     #'unk': data[0],
      'category_description': data[1],
      'videos': []
   }
   for v in data[2:]:
      img = v[2]
      uid = common.video_img_url_to_uid(img)

      vid_urls = {
         'main': v[3],
         '480p': v[5],
         '720p': v[4]
      }

     #unk=data[6] # int
      result['videos'].append({
         Video(uid=uid, category=category, name=v[0], date=common.str_to_date(v[1]), img=img, min_age=v[7], vid_urls=vid_urls)
      })

   return result
