# -*- coding: utf-8 -*-

import filmweb
from . import common
from datetime import datetime

class Film:
   def __init__(self, uid, type='unknown', name=None, poster=None, name_org=None, year=None, rate=None, votes=None, duration=None):
      self.uid = uid
      self.type = type
      self.name = name #: Localized name.
      self.poster = poster if poster != '' else None #: Relative poster path, use :func:`get_poster` for absolute path.
      self.name_org = name_org #: Original name.
      self.year = year
      self.rate = rate
      self.votes = votes
      self.duration = duration #: Duration in minutes.

   def __repr__(self):
      return '<Film uid: {} type: {} name: {}>'.format(self.uid, self.type, self.name)

   @property
   def url(self):
      if self.name and self.year:
         return '{}/{}/{}-{}-{}'.format(common.URL, self.type, self.name.replace(' ', '+'), self.year, self.uid)
      else:
         return '{}/entityLink?entityName={}&id={}'.format(common.URL, self.type, self.uid)

   def get_poster(self, size='small'):
      assert isinstance(size, str)
      """Returns absolute URL of specified size poster.

      :param str size: poster size (see common.poster_sizes)
      :return: URL
      :rtype: str or None      
      """
      if self.poster:
         return '{}/po{}.{}.jpg'.format(common.URL_CDN, self.poster, common.poster_sizes[size])

   def get_description(self):
      """Returns full film description.

      :return: description
      :rtype: str
      """
      data = filmweb.filmweb._request('getFilmDescription', [self.uid])
      return data[0]

   def get_info(self):
      """Returns informations about film and updates object variables.

      :return: info
      :rtype: dict

      .. code:: python

         {
            'name':              str(),
            'name_org':          str(),
            'rate':              float(),
            'votes':             int(),
            'genres':            [],
            'year':              str(),
            'duration':          int(), # in minutes
            'discussion_url':    str(), # absolute url
            'has_review':        bool(),
            'has_description':   bool(),
            'poster_small':      str(),
            'trailer':           Video(uid, category, film, img, min_age, vid_urls),
            'premiere':          date(),
            'premiere_local':    date(),
            'type':              str(),
            'season_count':      int(),
            'episode_count':     int(),
            'countries':         [],
            'description_short': str(),
            'top_pos':           int(),
            'wanna_see_count':   int(),
            'not_interested_count': int(),
            'recommended':       bool()
            'curiosities_count': int(),
            'boxoffice':         int(),
            'boxoffice_top_pos': int(),
            'budget':            int()
         }
      """
      data = filmweb.filmweb._request('getFilmInfoFull', [self.uid])

      trailer = None
      if data[12]:
         img = data[12][0]
         uid = common.video_img_url_to_uid(img)

         vid_urls = {
            'main': data[12][1],
            '480p': data[12][3],
            '720p': data[12][2]
         }

         trailer = Video(
             uid=uid, category='zwiastun', film=self, img=data[12][0], min_age=data[12][4], vid_urls=vid_urls
         )

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
         'has_review':        bool(data[9]),
         'has_description':   bool(data[10]),
         'poster_small':      data[11],
         'trailer':           trailer,
         'premiere':          common.str_to_date(data[13]),
         'premiere_local':    common.str_to_date(data[14]),
         'type':              common.get_film_type_name(data[15]),
         'season_count':      data[16],
         'episode_count':     data[17],
         'countries':         data[18].split(','),
         'description_short': data[19],
         'top_pos':           data[20],
         'wanna_see_count':   data[21],
         'not_interested_count': data[22], # not 100% sure
         'recommended':       bool(data[23]),
         'curiosities_count': data[24],
         'boxoffice':         data[25],
         'boxoffice_top_pos': data[26],
         'budget':            data[27]
      }

      # Update object
      self.type = result['type']
      self.name = result['name']
      self.year = result['year']
      self.rate = result['rate']
      self.votes = result['votes']
      self.duration = result['duration']
      if result['poster_small']:
         self.poster = common.poster_path_to_relative(result['poster_small'])

      return result

   def get_persons(self, role_type, offset=0):
      """Returns persons which has role in this film.

      :param str role_type: see common.person_role_types
      :param int offset: start position

      :return: list
      :rtype: list of dicts

      .. code:: python

         [
            {
               'person': Person(uid, name, poster),
               'role': str(), # see common.person_role_types
               'role_extra_info': str()
            }
         ]
      """
      assert role_type in common.person_role_types
      assert isinstance(offset, int)
      limit = 50 # Sadly ignored
      data = filmweb.filmweb._request('getFilmPersons', [self.uid, common.get_role_type_id(role_type), offset, limit])

      results = []
      for v in data:
         results.append({
            'person': Person(uid=v[0], name=v[3], poster=common.poster_path_to_relative(v[4])),
            'role': v[1],
            'role_extra_info': v[2]
         })
      return results

   def get_images(self, offset=0):
      """Returns film images.

      :param str offset: start position
      :return: list of :class:`Image`'s
      :rtype: list
      """
      assert isinstance(offset, int)
      limit = 100 # ignored
      data = filmweb.filmweb._request('getFilmImages', [[self.uid, offset, limit]])
      results = []
      for v in data:
         persons = []
         # If this image has marked persons on it
         if v[1]:
            for pdata in v[1]:
               persons.append(Person(uid=pdata[0], name=pdata[1], poster=common.poster_path_to_relative(pdata[2])))

         results.append(Image(path=common.poster_path_to_relative(v[0]), sources=v[2], associated_film=self, persons=persons))

      return results

   def get_platforms(self):
      """Returns videogame platforms. Throws ValueError if it's not videogame.
      
      :return: list of platforms
      :rtype: list of strings
      """
      if self.type != 'videogame':
         raise ValueError('unsupported object type (expected videogame)')

      data = filmweb.filmweb._request('getGameInfo', [self.uid])
      if data:
         return data[0].split(', ')

   def get_broadcasts(self):
      """Returns film TV broadcasts.

      :return: list of broadcasts
      :rtype: list of dicts

      .. code:: python
   
         [
            {
               'channel': Channel(uid),
               'datetime': datetime(),
               'uid': int()
            }
         ]
      """

      # Seems to be ignored
      offset = 0
      limit = 100

      data = filmweb.filmweb._request('getFilmsNearestBroadcasts', [[self.uid, offset, limit]])

      results = []
      for v in data:
         results.append({
            'channel': Channel(uid=v[1]),
            'datetime': datetime.strptime(v[3]+v[2], '%Y-%m-%d%H:%M'),
            'uid': v[4]
         })

      return results

   def get_videos(self, offset=0, limit=10):
      """Returns film videos.

      :param int offset: start position
      :param int limit: limit
      :return: list of :class:`Video`'s
      :rtype: list
      """
      assert isinstance(offset, int)
      assert isinstance(limit, int)
      data = filmweb.filmweb._request('getFilmVideos', [self.uid, offset, limit])

      results = []
      for v in data:
         #img_low = v[0]
         img = v[1]
         uid = common.video_img_url_to_uid(img)
         results.append(
            Video(uid=uid, category='zwiastun', film=self, img=img, vid_urls={'main': v[2]}, min_age=v[3])
         )

      return results

class Person:
   def __init__(self, uid, name=None, poster=None, rate=None, votes=None, date_birth=None, date_death=None):
      self.uid = uid
      self.name = name
      self.poster = poster #: Relative poster path, use get_poster() for absolute path
      self.rate = rate
      self.votes = votes
      self.date_birth = date_birth
      self.date_death = date_death

   @property
   def type(self):
      return 'person'

   @property
   def url(self):
      if self.name:
         return '{}/person/{}'.format(common.URL, self.name.replace(' ', '.').replace('?', ''))
      else:
         return '{}/entityLink?entityName={}&id={}'.format(common.URL, self.type, self.uid)

   def get_poster(self, size='small'):
      """Returns absolute URL of specified size poster.

      :param str size: poster size (small or tiny)
      :return: URL
      :rtype: str or None
      """
      if self.poster:
         return '{}/p{}.{}.jpg'.format(common.URL_CDN, self.poster, 0 if size == 'tiny' else 1)

   def get_biography(self):
      """Returns full person biography.

      :return: biography
      :rtype: str or None
      """
      data = filmweb.filmweb._request('getPersonBiography', [self.uid])
      if data:
         return data[0]

   def get_info(self):
      """Returns informations about person and updates object variables.

      :return: info
      :rtype: dict

      .. code:: python

         {
            'name': str(),
            'birth_date': date(),
            'birth_place': date(),
            'votes': int(),
            'rate': float(),
            'poster': str(),
            'has_bio': bool(),
            'film_known_for': Film(uid),
            'sex': int(),
            'name_full': str(),
            'death_date': date(),
            'height': int(),
         }
      """
      data = filmweb.filmweb._request('getPersonInfoFull', [self.uid])

      result = {
         'name': data[0],
         'birth_date': common.str_to_date(data[1]),
         'birth_place': common.str_to_date(data[2]),
         'votes': data[3],
         'rate': data[4],
         'poster': common.poster_path_to_relative(data[5]),
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
      self.date_birth = result['birth_date']
      self.date_death = result['death_date']
      return result

   def get_images(self, offset=0):
      """Returns person images.

      :param str offset: start position
      :return: list of :class:`Image`'s
      :rtype: list
      """
      assert isinstance(offset, int)
      limit = 100 # ignored
      data = filmweb.filmweb._request('getPersonImages', [self.uid, offset, limit])

      results = []
      for v in data:
         persons = []
         # If this image has marked persons on it
         if v[1]:
            for pdata in v[1]:
               persons.append(Person(uid=pdata[0], name=pdata[1], poster=common.poster_path_to_relative(pdata[2])))

         results.append(Image(path=common.poster_path_to_relative(v[0]), sources=v[2], associated_film=Film(uid=v[3], name=v[4]), persons=persons))

      return results

   def get_roles(self, limit=10):
      """Returns person roles ordered by popularity.

      :param str limit: results limit
      :return: dict
      :rtype: dict

      .. code:: python

         {
            'film': Film(uid, type, name, poster, year),
            'role_type_id': int(), # see common.person_role_types
            'role': str(),
            'role_extra_info': str()
         }
      """
      assert isinstance(offset, limit)
      data = filmweb.filmweb._request('getPersonFilmsLead', [self.uid, limit])

      results = []
      for v in data:
         results.append({
            'film': Film(type=v[0], uid=v[2], name=v[4], poster=v[5][:6] if v[5] else None, year=v[6]),
            'role_type_id': v[1], # todo: convert this into common.person_role_types
            'role': v[3],
            'role_extra_info': v[7]
         })

      return results

   def get_films(self, film_type, role_type, offset=0, limit=10):
      """Returns films in which this person has role (ordered by newest).

      :param str film_type: film, serial or videogame
      :param str role_type: see common.person_role_types
      :param int offset: start position
      :param int limit: results limit

      :return: list of dicts
      :rtype: list

      .. code:: python

         [
            {
               'film': Film(uid, type, name, poster, year, name_org),
               'role': str(),
               'role_extra_info': str()
            }
         ]
      """
      assert film_type in common.film_types
      assert role_type in common.person_role_types
      assert isinstance(offset, int)
      assert isinstance(limit, int)
      data = filmweb.filmweb._request('getPersonFilms', [self.uid, common.get_film_type_id(film_type), common.get_role_type_id(role_type), offset, limit])

      results = []
      for v in data:
         results.append({
            'film': Film(uid=v[0], type=film_type, name=v[2], poster=v[3][:6] if v[3] else None, year=v[4], name_org=v[6]),
            'role': v[1],
            'role_extra_info': v[5]
         })

      return results

class Image:
   def __init__(self, path, associated_film=None, persons=[], sources=[]):
      self.path = path #: Relative path, use :func:`get_url` for absolute
      self.associated_film = associated_film #: :class:`Film` instance
      self.persons = persons #: list of :class:`Person` instances
      self.sources = sources

   def get_url(self, size='medium'):
      return '{}/ph{}.{}.jpg'.format(common.URL_CDN, self.path, common.image_sizes[size])

class Channel:
   def __init__(self, uid, name=None):
      self.uid = uid
      self.name = name

   def __repr__(self):
      return '<Channel uid: {} name: {}>'.format(self.uid, self.name)

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
      """Returns absolute URL of specified size icon.

      :param str size: icon size (see common.channel_icon_sizes)
      :return: URL
      :rtype: str
      """
      assert size in common.channel_icon_sizes
      return '{}/channels/{}.{}.png'.format(common.URL_CDN, self.uid, common.channel_icon_sizes[size])

   # date: max +13, min -1 days
   def get_schedule(self, date):
      data = filmweb.filmweb._request('getTvSchedule', [self.uid, str(date)])

      results = []
      for v in data:
         results.append({
            'uid': v[0],
            'title': v[1],
            'description': v[2],
            'time': v[3], # HH-MM
            'type': v[4],
            'film': Film(uid=v[5], name=v[1], year=v[6], duration=v[7], poster=common.poster_path_to_relative(v[8])) if v[5] else None
         })
      return results

class Video:
   def __init__(self, uid, category=None, film=None, date=None, img=None, name=None, min_age=None, vid_urls=[]):
      self.uid = uid
      self.category = category
      self.film = film
      self.date = date
      self.img = img
      self.name = name
      self.min_age = min_age
      self.vid_urls = vid_urls

   def __repr__(self):
      return '<Video uid: {} category: {} name: {}>'.format(self.uid, self.category, self.name)

   @property
   def url(self):
      if self.uid:
         return '{}/video/{}/{}-{}'.format(common.URL, self.category or 'zwiastun', self.name.replace(' ', '+') or 'A', self.uid)

   def get_video(self, size='main'):
      """Returns absolute URL of specified quality video.

      :param str size: quality (main, 480p, 720p)
      :return: URL
      :rtype: str
      """
      assert size in ['main', '480p', '720p']
      if size in self.vid_urls:
         return self.vid_urls[size]

class Cinema:
   def __init__(self, uid, name=None, city_name=None, address=None, coords=None):
      self.uid = uid
      self.name = name
      self.city_name = city_name
      self.address = address
      self.coords = coords

   def __repr__(self):
      return '<Cinema uid: {} name: {}>'.format(self.uid, self.name)

   def get_repertoire(self, date):
      """Returns unsorted cinema repertoire.

      :param date date: date
      :return: seances
      :rtype: list

      .. code:: python

         [
            {
               'film': Film(name, year, rate, votes, duration, poster, uid),
               'hours': [], # ex. ['13:05', '17:05']
               'attributes': int(),
               'notes': str(),
               'dubbing_langs': [],
               'subtitles_langs': []
            }
         ]
      """
      data = filmweb.filmweb._request('getRepertoireByCinema', [self.uid, str(date)])

      if len(data) == 0:
         return []

      # Last element is list which contains films data
      films_data = data[len(data)-1]
      films = {}
      for v in films_data:
         uid = v[6]
         films[uid] = Film(name=v[0], year=v[1], rate=v[2], votes=v[3], duration=v[4], poster=common.poster_path_to_relative([5]), uid=uid)

      results = []
      # For all seances
      for v in data[:-1]:
         film_uid = v[0]
         results.append({
            'film': films[film_uid],
            'hours': v[1].split(' '),
            'attributes': v[2],
            'notes': v[3],
            'dubbing_langs': v[4].split('+') if v[4] else None,
            'subtitles_langs': v[5].split('+') if v[5] else None,
         })

      return results
