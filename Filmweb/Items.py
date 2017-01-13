# -*- coding: utf-8 -*-

from Filmweb import Filmweb, common
from datetime import datetime

class Film:
   def __init__(self, uid, type='unknown', name=None, poster=None, name_org=None, year=None, rate=None, votes=None, duration=None):
      self.uid = uid
      self.type = type
      self.name = name
      self.poster = poster if poster != '' else None
      self.name_org = name_org
      self.year = year
      self.rate = rate
      self.votes = votes
      self.duration = duration

   def __repr__(self):
      return '<Film uid: {} type: {} name: {}>'.format(self.uid, self.type, self.name)

   @property
   def url(self):
      if self.name and self.year:
         return '{}/{}/{}-{}-{}'.format(common.URL, self.type, self.name.replace(' ', '+'), self.year, self.uid)
      else:
         return '{}/entityLink?entityName={}&id={}'.format(common.URL, self.type, self.uid)

   def get_poster(self, size='small'):
      if self.poster:
         return '{}/po{}.{}.jpg'.format(common.URL_CDN, self.poster, poster_sizes[size])

   def get_description(self):
      status, data = Filmweb._request('getFilmDescription', [self.uid])
      return data[0]

   def get_info(self):
      status, data = Filmweb._request('getFilmInfoFull', [self.uid])

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
         'type':              common.get_film_type_name(data[15]),
         'season_count':      data[16],
         'episode_count':     data[17],
         'countries':         data[18].split(','),
         'description_short': data[19]
      }

      # Update object
      self.type = result['type']
      self.name = result['name']
      self.year = result['year']
      self.rate = result['rate']
      self.votes = result['votes']
      self.duration = result['duration']
      if result['poster_small']:
         self.poster = result['poster_small'][:-6]

      return result

   def get_persons(self, role_type, offset=0):
      assert role_type in common.person_role_types
      assert isinstance(offset, int)
      limit = 50 # Sadly ignored
      status, data = Filmweb._request('getFilmPersons', [self.uid, common.get_role_type_id(role_type), offset, limit])

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
      status, data = Filmweb._request('getFilmImages', [[self.uid, offset, limit]])
      results = []
      for v in data:
         persons = []
         # If this image has marked persons on it
         if v[1]:
            for pdata in v[1]:
               persons.append(Person(uid=pdata[0], name=pdata[1], poster=pdata[2][:-6] if pdata[2] else None))

         results.append(Image(path=v[0][:-6], sources=v[2], associated_film=self, persons=persons))

      return results

   def get_platforms(self):
      if self.type != 'videogame':
         return False

      status, data = Filmweb._request('getGameInfo', [self.uid])
      if data:
         return data[0].split(', ')

   def get_broadcasts(self):
      # Seems to be ignored
      offset = 0
      limit = 100

      status, data = Filmweb._request('getFilmsNearestBroadcasts', [[self.uid, offset, limit]])

      results = []
      for v in data:
         results.append({
            'channel': Channel(uid=v[1]),
            'datetime': datetime.strptime(v[3]+v[2], '%Y-%m-%d%H:%M'),
            'uid': v[4]
         })

      return results

class Person:
   def __init__(self, uid, name=None, poster=None, rate=None, votes=None, date_birth=None, date_death=None):
      self.uid = uid
      self.name = name
      self.poster = poster
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
      if self.poster:
         return '{}/p{}.{}.jpg'.format(common.URL_CDN, self.poster, 0 if size == 'tiny' else 1)

   def get_biography(self):
      status, data = Filmweb._request('getPersonBiography', [self.uid])
      if data:
         return data[0]

   def get_info(self):
      status, data = Filmweb._request('getPersonInfoFull', [self.uid])

      result = {
         'name': data[0],
         'birth_date': common.str_to_date(data[1]),
         'birth_place': common.str_to_date(data[2]),
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
      self.date_birth = result['birth_date']
      self.date_death = result['death_date']

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

         results.append(Image(path=v[0][:-6], sources=v[2], associated_film=Film(uid=v[3], name=v[4]), persons=persons))

      return results

   # Ordered by popularity
   def get_roles(self, limit=50):
      status, data = Filmweb._request('getPersonFilmsLead', [self.uid, limit])

      results = []
      for v in data:
         results.append({
            'film': Film(type=v[0], uid=v[2], name=v[4], poster=v[5][:6] if v[5] else None, year=v[6]),
            'role_type_id': v[1],
            'role': v[3],
            'role_extra_info': v[7]
         })

      return results

   # Ordered from newest
   def get_films(self, film_type, role_type, offset=0, limit=50):
      status, data = Filmweb._request('getPersonFilms', [self.uid, common.get_film_type_id(film_type), common.get_role_type_id(role_type), offset, limit])

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
      self.path = path
      self.associated_film = associated_film
      self.persons = persons
      self.sources = sources

   def get_url(self, size='medium'):
      return '{}/ph{}.{}.jpg'.format(common.URL_CDN, self.path, image_sizes[size])

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