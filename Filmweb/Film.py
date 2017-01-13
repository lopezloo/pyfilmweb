# -*- coding: utf-8 -*-
from Filmweb import Filmweb, common

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
      return '<Film id: {} name: {} poster: {}>'.format(self.uid, self.name, self.poster)

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

         results.append(Image(path=v[0][:-6], sources=v[2], associated_film=self, persons=persons))

      return results

   def get_platforms(self):
      if self.type != 'videogame':
         return False

      status, data = Filmweb._request('getGameInfo', [self.uid])
      if data:
         return data[0].split(', ')
