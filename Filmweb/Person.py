# -*- coding: utf-8 -*-
from Filmweb import Filmweb, common
from Filmweb.Film import *

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
