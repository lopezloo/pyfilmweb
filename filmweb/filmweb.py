# -*- coding: utf-8 -*-
from hashlib import md5
import json
import requests

from . import common, exceptions
from .items import *

import logging

class Filmweb:
   def __init__(self):
      self.session = None

   def login(self, name, password):
      """Authenticates user.

      :param str name: account name
      :param str password: account password

      .. note::
         Throws :class:`exceptions.RequestFailed` (20, 'badCreadentials') if bad credentials are passed.
      """
      self.session = requests.session()

      remember = True
      data = self._request('login', [name, password, int(remember)], hmethod='POST')
      return LoggedUser(fw=self, uid=data[3], name=data[0], img=common.img_path_to_relative(data[1]), sex=data[4], birth_date=data[5])

   # This method is one big TODO.
   def _request(self, method, params=[], hmethod='GET'):
      params = [v if v is not None else 'null' for v in params]
      data_str = '{} {}\n'.format(method, str(params))
      logging.debug('Calling {}'.format(data_str))

      sig = '{},{}'.format(common.API_VER, md5((data_str + 'android' + common.API_KEY).encode()).hexdigest())
      rparams = {
         'version': common.API_VER,
         'appId': 'android',
         'signature': sig,
         'methods': data_str
      }

      o = self.session if self.session else requests
      if hmethod == 'GET':
         r = o.get(common.URL_API, params=rparams)
      elif hmethod == 'POST':
         r = o.post(common.URL_API, data=rparams)

      data = r.text.split('\n')
      status = data[0].split(',')

      if status[0] != 'ok':
         d = data[1].split(', ')
         error_code, error_msg = int(d[0]), d[1]
         raise exceptions.RequestFailed(error_code, error_msg)

      if data[1][:3] == 'exc':
         raise exceptions.RequestFailed('exc', data[1][4:])

      # Everything okay, just 0 results
      if data[1] == 'null' or data[1] == '':
         return []

      if hmethod == 'GET':
         if data[1][-1:] == 's':
            return json.loads(data[1][:-1])
         else:
            return json.loads(data[1][:-7])
      elif hmethod == 'POST':
         return json.loads(data[1])

   def search(self, query):
      """Searches in Filmweb database.

      :param str query: search query
      :return: list containing result items (they can be: :class:`Film`, :class:`Person`, :class:`Channel`, :class:`Cinema`)
      :rtype: list

      :Example:

      .. code:: python

         fw = Filmweb()
         items = fw.search('Jak działa jamniczek')
         if len(items) > 0 and isinstance(items[0], Film):
            print(items[0].name, items[0].year)
      """
      r = requests.get('{}/search/live'.format(common.URL), params={'q': query})

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

            item = Film(fw=self, uid=int(v[1]), type=ftype, name=v[4], poster=common.img_path_to_relative(v[2]), name_org=v[3], year=v[6])

         elif item_type == 'p':
            item = Person(fw=self, uid=int(v[1]), name=v[3], poster=common.img_path_to_relative(v[2]))

         elif item_type == 't':
            item = Channel(fw=self, uid=int(v[1]), name=v[2])

         elif item_type == 'c':
            item = Cinema(fw=self, uid=int(v[1]), name=v[2], city_name=v[3], address=v[4], coords=v[5])

         items.append(item)

      return items

   def get_popular_films(self):
      """Returns 100 popular films.

      :return: list of :class:`Films`'s
      """
      data = self._request('getPopularFilms')

      films = []
      for v in data:
         films.append(Film(fw=self, name=v[0], year=v[1], rate=v[2], votes=v[3], poster=common.img_path_to_relative(v[5]), uid=v[6]))

      return films

   def get_popular_persons(self):
      """Returns 100 popular persons.

      :return: list of :class:`Person`'s
      """
      data = self._request('getPopularPersons')

      persons = []
      for v in data:
         persons.append(Person(fw=self, uid=v[0], name=v[1], poster=common.img_path_to_relative(v[2])))

      return persons

   def get_top(self, film_type, genre=None, worldwide=True):
      """Returns TOP 500 popular films.

      :param str film_type: :class:`Film` type (film, serial, videogame)
      :param str genre: genre name (ignored if film_type==videogame)
      :param bool worldwide: determines if returned top :class:`Film`'s should be from any country or only Poland (can't be False if film_type==videogame)

      :return: list of results

      .. code:: python

         [
            {
               'film': Film(uid, type, rate, votes),
               'position': int(),
               'position_prev': int()
            }
         ]

      """
      assert film_type in common.film_types
      assert isinstance(worldwide, bool)

      # Game genre is sadly ignored
      genre_id = common.get_genre_id(film_type, genre) if genre else None

      # Same as country option
      if film_type == 'videogame' and not worldwide:
         raise ValueError('videogame type doesn\'t support worldwide=False')

      req = 'top_100_{}s_{}'.format('game' if film_type == 'videogame' else film_type, 'world' if worldwide else 'poland')
      data = self._request('getRankingFilms', [req, genre_id])

      results = []
      for v in data:
         results.append({
            'film': Film(fw=self, uid=v[0], type=film_type, rate=v[1], votes=v[4]),
            'position': v[2],
            'position_prev': v[3]
         })

      return results

   def get_upcoming_films(self, above_date=None):
      """Returns upcoming :class:`Film`'s

      :param date above_date: date which above results are returned

      :return: list of results
      
      .. code:: python

         [
            {
               'date': str(),
               'films': [
                  {
                     'film': Film(uid, name, year, poster),
                     'person_names': [str(), str()]
                  }
               ]
            }
         ]

      """

      # Nice typo, Filmweb!
      data = self._request('getUpcommingFilms', [above_date])

      results = []
      for day in data:
         films = []
         for v in day[1]:
            films.append({
               'film': Film(fw=self, uid=v[0], name=v[1], year=v[2], poster=common.img_path_to_relative(v[3])),
               'person_names': [v[4], v[5]]
            })

         result = {
            'date': day[0],
            'films': films
         }
         results.append(result)

      return results

   def get_born_today_persons(self):
      """Returns born today persons.

      :return: list of :class:`Person`'s
      """
      data = self._request('getBornTodayPersons')
      results = []
      for v in data:
         results.append(Person(fw=self, uid=v[0], name=v[1], poster=common.img_path_to_relative(v[2]), date_birth=v[3], date_death=v[4]))
      return results

   def get_trailers(self, offset=0, limit=10):
      """Returns trailer from newest.

      :param int offset: start position
      :param int limit: maximum of results

      :return: list of :class:`Video`'s
      """
      data = self._request('getTrailers', [offset, limit])
      results = []
      for v in data:
         img = common.img_path_to_relative(v[3])
         uid = common.video_img_url_to_uid(img)

         vid_urls = {
            'main': v[4],
            '480p': v[7],
            '720p': v[8]
         }

         film = Film(fw=self, uid=v[2], name=v[0], poster=common.img_path_to_relative(v[5]))
         results.append(
            Video(fw=self, film=film, date=v[1], img=img, name=v[6], min_age=v[9], uid=uid, vid_urls=vid_urls)
         )
      return results

   def get_popular_trailers(self, offset=0, limit=10):
      """Returns popular trailers.

      :param int offset: start position
      :param int limit: maximum of results

      :return: list of :class:`Video`'s
      """
      data = self._request('getPopularTrailers', [offset, limit])
      results = []
      for v in data:
         img = v[3]
         uid = common.video_img_url_to_uid(img)

         vid_urls = {
            'main': v[4],
            '480p': v[8],
            '720p': v[7]
         }

         film = Film(fw=self, uid=v[2], name=v[0], poster=common.img_path_to_relative(v[5]))
         results.append(
            Video(
               fw=self,
               uid=uid,
               name=v[6],
               film=film,
               date=v[1],
               img=common.img_path_to_relative(img),
               min_age=v[9],
               vid_urls=vid_urls
            )
         )
      return results

   def get_video_categories(self):
      """Returns Filmweb productions categories.

      :return: list of categories

      .. code:: python

         [
            {
               'name': str(),
               'name_friendly': str(),
               'description': str()
            }
         ]
      """
      data = self._request('getVideoConfiguration')
      results = []
      for v in data:
         results.append({
            'name':           v[0],
            'name_friendly':  v[1],
            'description':    v[2]
         })
      return results

   def get_filmweb_productions(self, category, offset=0, limit=10):
      """Returns newest Filmweb productions from given category.

      :param int offset: start position
      :param int limit: maximum of results

      :return: list

      .. code:: python

         [
            {
               'category_description': str(),
               'videos': [Video(uid, category, name, date, img, min_age, vid_urls)]
            }
         ]

      .. note::
         This gonna throw :class:`exceptions.RequestFailed` (20, 'IllegalArgumentException') if category is unknown.
      """
      unk = -1
      category = category.lower().replace(' ', '_')
      data = self._request('getFilmwebProductions', [unk, category, offset, limit])

      result = {
        #'unk': data[0],
         'category_description': data[1],
         'videos': []
      }
      for v in data[2:]:
         img = common.img_path_to_relative(v[2])
         uid = common.video_img_url_to_uid(img)

         vid_urls = {
            'main': v[3],
            '480p': v[5],
            '720p': v[4]
         }

        #unk=data[6] # int
         result['videos'].append({
            Video(fw=self, uid=uid, category=category, name=v[0], date=v[1], img=img, min_age=v[7], vid_urls=vid_urls)
         })

      return result

   def update_films_info(self, films):
      """Updates multiple film instances with basic info (name, year, rate, votes, duration, poster).

      :param list films: list of :class:`Film`'s instances (max = 100)
      """
      assert isinstance(films, list)
      if len(films) > 100:
         raise ValueError('Too much.')

      uids = []
      for film in films:
         uids.append(film.uid)

      data = self._request('getFilmsInfoShort', [uids])
      for k, v in enumerate(data):
         films[k].name = v[0]
         films[k].year = v[1]
         films[k].rate = v[2]
         films[k].votes = v[3]
         films[k].duration = v[4]
         films[k].poster = common.img_path_to_relative(v[5])
