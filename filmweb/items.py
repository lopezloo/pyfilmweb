# -*- coding: utf-8 -*-

import filmweb
from . import common, exceptions

class Object:
   def _request(self, method, params=[], hmethod='GET'):
      return self.fw._request(method, params, hmethod)

   def check_auth(self):
      if self.fw.session is None:
         raise exceptions.NotAuthenticated

class Film(Object):
   def __init__(self, fw, uid, type='unknown', name=None, poster=None, name_org=None, year=None, rate=None, votes=None, duration=None):
      self.fw = fw #: :class:`Filmweb` instance
      self.uid = uid
      self.type = type #: film, serial or videogame.
      self.name = name #: Localized name.
      self.poster = poster if poster != '' else None #: Relative poster path, use :func:`get_poster` for absolute path.
      self.name_org = name_org #: Original name.
      self.year = year
      self.rate = rate
      self.votes = votes #: Amount of how many people voted on this film.
      self.duration = duration #: Duration in minutes.

   def __repr__(self):
      return '<Film uid: {} type: {} name: {}>'.format(
         self.uid,
         self.type,
         self.name.encode('ascii', 'replace') if self.name else None
      )

   @property
   def url(self):
      if self.name and self.year:
         return u'{}/{}/{}-{}-{}'.format(common.URL, self.type, self.name.replace(' ', '+'), self.year, self.uid)
      else:
         return u'{}/entityLink?entityName={}&id={}'.format(common.URL, self.type, self.uid)

   def get_poster(self, size='small'):
      """Returns absolute path of specified size poster.

      :param str size: poster size (see common.poster_sizes)
      :return: URL
      :rtype: str or None      
      """
      assert isinstance(size, str)
      if self.poster:
         return u'{}/po{}.{}.jpg'.format(common.URL_CDN, self.poster, common.poster_sizes[size])

   def get_description(self):
      """Returns full film description.

      :return: description
      :rtype: str
      """
      data = self._request('getFilmDescription', [self.uid])
      return data[0]

   def get_review(self):
      """Returns film review.

      :return: review
      :rtype: dict or None

      .. code:: python

         {
            'title': str(),
            'content': str(),
            'author': User(uid, name, img)
         }
      """
      data = self._request('getFilmReview', [self.uid])

      if len(data) >= 5:
         result = {
            'title': data[4],
            'content': data[3],
            'author': User(fw=self.fw, uid=data[1], name=data[0], img=common.img_path_to_relative(data[2])),
         }
         return result

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
            'discussion_url':    str(),
            'has_review':        bool(),
            'has_description':   bool(),
            'poster_small':      str(),
            'trailer':           Video(uid, category, film, img, min_age, vid_urls),
            'premiere':          str(), # Y-m-d
            'premiere_local':    str(), # Y-m-d
            'type':              str(),
            'season_count':      int(),
            'episode_count':     int(),
            'countries':         [],
            'description_short': str(),
            'top_pos':           int(),
            'wanna_see_count':   int(),
            'not_interested_count': int(), # unconfirmed
            'recommended':       bool()
            'curiosities_count': int(),
            'boxoffice':         int(),
            'boxoffice_top_pos': int(),
            'budget':            int()
         }

      .. note::
         You can use :func:`Filmweb.update_films_info` if you want get basic info about multiple Film instances with only one request.
      """
      data = self._request('getFilmInfoFull', [self.uid])

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
            fw=self.fw,
            uid=uid,
            category='zwiastun',
            film=self,
            img=common.img_path_to_relative(data[12][0]),
            min_age=data[12][4],
            vid_urls=vid_urls
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
         'premiere':          data[13],
         'premiere_local':    data[14],
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
         self.poster = common.img_path_to_relative(result['poster_small'])

      return result

   def get_persons(self, role_type, offset=0):
      """Returns persons with specified role type in this film.

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
      data = self._request('getFilmPersons', [self.uid, common.get_role_type_id(role_type), offset, limit])

      results = []
      for v in data:
         results.append({
            'person': Person(fw=self.fw, uid=v[0], name=v[3], poster=common.img_path_to_relative(v[4])),
            'role': v[1],
            'role_extra_info': v[2]
         })
      return results

   def get_persons_lead(self):
      """Returns film lead persons.

      :return: list
      :rtype: list of dicts

      .. code:: python

         [
            {
               'person': Person(uid, name, poster),
               'role_type': str(), # see common.person_role_types
               'role': str(),
               'role_extra_info': str()
            }
         ]
      """
      limit = 10 # ignored
      data = self._request('getFilmPersonsLead', [self.uid, limit])

      results = []
      for v in data:
         results.append({
            'person': Person(fw=self.fw, uid=v[1], name=v[4], poster=common.img_path_to_relative(v[5])),
            'role_type': common.get_role_type_str(v[0]),
            'role': v[2],
            'role_extra_info': v[3]
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
      data = self._request('getFilmImages', [[self.uid, offset, limit]])
      results = []
      for v in data:
         persons = []
         # If this image has marked persons on it
         if v[1]:
            for pdata in v[1]:
               persons.append(Person(fw=self.fw, uid=pdata[0], name=pdata[1], poster=common.img_path_to_relative(pdata[2])))

         results.append(Image(fw=self.fw, path=common.img_path_to_relative(v[0]), sources=v[2], associated_film=self, persons=persons))

      return results

   def get_platforms(self):
      """Returns videogame platforms. Throws ValueError if it's not videogame.
      
      :return: list of platforms
      :rtype: list of strings
      """
      if self.type != 'videogame':
         raise ValueError('unsupported object type (expected videogame)')

      data = self._request('getGameInfo', [self.uid])
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
               'time': str(), # H:M
               'date': str(), # Y-m-d
               'uid': int()
            }
         ]
      """

      # Seems to be ignored
      offset = 0
      limit = 100

      data = self._request('getFilmsNearestBroadcasts', [[self.uid, offset, limit]])

      results = []
      for v in data:
         results.append({
            'channel': Channel(fw=self.fw, uid=v[1]),
            'time': v[2],
            'date': v[3],
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
      data = self._request('getFilmVideos', [self.uid, offset, limit])

      results = []
      for v in data:
         #img_low = v[0]
         img = common.img_path_to_relative(v[1])
         uid = common.video_img_url_to_uid(img)
         results.append(
            Video(
               fw=self.fw,
               uid=uid,
               category='zwiastun',
               film=self,
               img=img,
               vid_urls={'main': v[2]},
               min_age=v[3]
            )
         )

      return results

class Person(Object):
   def __init__(self, fw, uid, name=None, poster=None, rate=None, votes=None, date_birth=None, date_death=None, sex=None):
      self.fw = fw #: :class:`Filmweb` instance
      self.uid = uid
      self.name = name
      self.poster = poster #: Relative poster path, use :func:`get_poster` for absolute path
      self.rate = rate
      self.votes = votes
      self.date_birth = date_birth
      self.date_death = date_death
      self.sex = sex #: F/M

   @property
   def type(self):
      return 'person'

   @property
   def url(self):
      if self.name:
         return u'{}/person/{}-{}'.format(common.URL, self.name.replace(' ', '+').replace('?', ''), self.uid)
      else:
         return u'{}/entityLink?entityName={}&id={}'.format(common.URL, self.type, self.uid)

   def get_poster(self, size='small'):
      """Returns absolute path of specified size poster.

      :param str size: poster size (small or tiny)
      :return: URL
      :rtype: str or None
      """
      assert size in ['small', 'tiny']
      if self.poster:
         return u'{}/p{}.{}.jpg'.format(common.URL_CDN, self.poster, 0 if size == 'tiny' else 1)

   def get_biography(self):
      """Returns full person biography.

      :return: biography
      :rtype: str or None
      """
      data = self._request('getPersonBiography', [self.uid])
      if data:
         return data[0]

   def get_info(self):
      """Returns informations about person and updates object variables.

      :return: info
      :rtype: dict

      .. code:: python

         {
            'name': str(),
            'birth_date': str(), # Y-m-d
            'birth_place': str(),
            'votes': int(),
            'rate': float(),
            'poster': str(),
            'has_bio': bool(),
            'film_known_for': Film(uid),
            'sex': str(), # F/M
            'name_full': str(),
            'death_date': str(), # Y-m-d
            'height': int(),
         }
      """
      data = self._request('getPersonInfoFull', [self.uid])

      result = {
         'name': data[0],
         'birth_date': data[1],
         'birth_place': data[2],
         'votes': data[3],
         'rate': data[4],
         'poster': common.img_path_to_relative(data[5]),
         'has_bio': bool(data[6]),
         'film_known_for': Film(fw=self.fw, uid=data[7]) if data[7] else None,
         'sex': common.sex_id_to_str(data[8]),
         'name_full': data[9],
         'death_date': data[10],
         'height': int(data[11]) if data[11] else None,
      }

      # Update object
      self.name = result['name']
      self.poster = result['poster']
      self.rate = result['rate']
      self.votes = result['votes']
      self.date_birth = result['birth_date']
      self.date_death = result['death_date']
      self.sex = result['sex']
      return result

   def get_images(self, offset=0):
      """Returns person images.

      :param str offset: start position
      :return: list of :class:`Image`'s
      :rtype: list
      """
      assert isinstance(offset, int)
      limit = 100 # ignored
      data = self._request('getPersonImages', [self.uid, offset, limit])

      results = []
      for v in data:
         persons = []
         # If this image has marked persons on it
         if v[1]:
            for pdata in v[1]:
               persons.append(Person(fw=self.fw, uid=pdata[0], name=pdata[1], poster=common.img_path_to_relative(pdata[2])))

         results.append(Image(fw=self.fw, path=common.img_path_to_relative(v[0]), sources=v[2], associated_film=Film(fw=self.fw, uid=v[3], name=v[4]), persons=persons))

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
      data = self._request('getPersonFilmsLead', [self.uid, limit])

      results = []
      for v in data:
         results.append({
            'film': Film(fw=self.fw, type=v[0], uid=v[2], name=v[4], poster=v[5][:6] if v[5] else None, year=v[6]),
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
      data = self._request('getPersonFilms', [self.uid, common.get_film_type_id(film_type), common.get_role_type_id(role_type), offset, limit])

      results = []
      for v in data:
         results.append({
            'film': Film(fw=self.fw, uid=v[0], type=film_type, name=v[2], poster=v[3][:6] if v[3] else None, year=v[4], name_org=v[6]),
            'role': v[1],
            'role_extra_info': v[5]
         })

      return results

class Image(Object):
   def __init__(self, fw, path, associated_film=None, persons=[], sources=[]):
      self.fw = fw #: :class:`Filmweb` instance
      self.path = path #: Relative path, use :func:`get_url` for absolute
      self.associated_film = associated_film #: :class:`Film` instance
      self.persons = persons #: list of :class:`Person` instances
      self.sources = sources

   def get_url(self, size='medium'):
      """Returns absolute path for image of given size.

      :param str size: size, see common.image_sizes
      :return: URL
      :rtype: str
      """
      return u'{}/ph{}.{}.jpg'.format(common.URL_CDN, self.path, common.image_sizes[size])

class Channel(Object):
   def __init__(self, fw, uid, name=None):
      self.fw = fw #: :class:`Filmweb` instance
      self.uid = uid
      self.name = name

   def __repr__(self):
      return '<Channel uid: {} name: {}>'.format(
         self.uid,
         self.name.encode('ascii', 'replace') if self.name else None
      )

   @property
   def type(self):
      return 'channel'

   @property
   def url(self):
      if self.name:
         return u'{}/program-tv/{}'.format(common.URL, self.name.replace(' ', '+'))
      else:
         return u'{}/entityLink?entityName={}&id={}'.format(common.URL, self.type, self.uid)

   def get_icon(self, size='small'):
      """Returns absolute path of specified size icon.

      :param str size: icon size (see common.channel_icon_sizes)
      :return: URL
      :rtype: str
      """
      assert size in common.channel_icon_sizes
      return u'{}/channels/{}.{}.png'.format(common.URL_CDN, self.uid, common.channel_icon_sizes[size])

   def get_schedule(self, date):
      """Returns channel schedule for given date.

      :param date date: date (min -1, max +13 days)
      :return: schedule
      :rtype: list

      .. code:: python

         [
            {
               'uid': int(),
               'title': str(),
               'description': str(),
               'time': str(), # HH-MM
               'type': str(),
               'film': None or Film(uid, name, year, duration, poster)
            }
         ]
      """
      data = self._request('getTvSchedule', [self.uid, str(date)])

      results = []
      for v in data:
         results.append({
            'uid': v[0],
            'title': v[1],
            'description': v[2],
            'time': v[3], # HH-MM
            'type': v[4],
            'film': Film(fw=self.fw, uid=v[5], name=v[1], year=v[6], duration=v[7], poster=common.img_path_to_relative(v[8])) if v[5] else None
         })
      return results

class Video(Object):
   def __init__(self, fw, uid, category=None, film=None, date=None, img=None, name=None, min_age=None, vid_urls=[]):
      self.fw = fw #: :class:`Filmweb` instance
      self.uid = uid
      self.category = category
      self.film = film
      self.date = date
      self.img = img #: Relative thumbnail path, use :func:`get_thumb` for absolute path
      self.name = name
      self.min_age = min_age
      self.vid_urls = vid_urls

   def __repr__(self):
      return '<Video uid: {} category: {} name: {}>'.format(
         self.uid,
         self.category,
         self.name.encode('ascii', 'replace') if self.name else None
      )

   @property
   def url(self):
      if self.uid:
         return u'{}/video/{}/{}-{}'.format(common.URL, self.category or 'zwiastun', self.name.replace(' ', '+') or 'A', self.uid)

   def get_video(self, size='main'):
      """Returns absolute path of specified quality video.

      :param str size: quality (main, 480p, 720p)
      :return: URL
      :rtype: str
      """
      assert size in ['main', '480p', '720p']
      if size in self.vid_urls:
         return self.vid_urls[size]

   def get_thumb(self, size='medium'):
      """Returns absolute path of specified size thumbnail.

      :param str size: thumbnail size (see common.video_thumb_sizes)
      :return: URL
      :rtype: str or None
      """
      assert size in common.video_thumb_sizes
      if self.img:
         return u'{}{}.{}.jpg'.format(common.URL_CDN, self.img, common.video_thumb_sizes[size])

class Cinema(Object):
   def __init__(self, fw, uid, name=None, city_name=None, address=None, coords=None):
      self.fw = fw #: :class:`Filmweb` instance
      self.uid = uid
      self.name = name
      self.city_name = city_name
      self.address = address
      self.coords = coords

   def __repr__(self):
      return u'<Cinema uid: {} name: {}>'.format(
         self.uid,
         self.name.encode('ascii', 'replace') if self.name else None
      )

   @property
   def url(self):
      if self.name and self.city_name:
         return u'{}/{}/{}-{}'.format(common.URL, self.city_name.replace(' ', '+'), self.name.replace(' ', '+'), self.uid)
      else:
         return u'{}/entityLink?entityName=cinema&id={}'.format(common.URL, self.uid)

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
      data = self._request('getRepertoireByCinema', [self.uid, str(date)])

      if len(data) == 0:
         return []

      # Last element is list which contains films data
      films_data = data[len(data)-1]
      films = {}
      for v in films_data:
         uid = v[6]
         films[uid] = Film(fw=self.fw, name=v[0], year=v[1], rate=v[2], votes=v[3], duration=v[4], poster=common.img_path_to_relative([5]), uid=uid)

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

class User(Object):
   def __init__(self, fw, uid=None, name=None, img=None, sex=None, birth_date=None, uid_fb=None, name_full=None):
      self.fw = fw #: :class:`Filmweb` instance
      self.uid = uid
      self.name = name
      self.img = img #: Relative avatar path, use :func:`get_avatar` for absolute path
      self.sex = sex #: F/M
      self.birth_date = birth_date
      self.uid_fb = uid_fb
      self.name_full = name_full

   @property
   def url(self):
      if self.name:
         return u'{}/user/{}'.format(common.URL, self.name.replace(' ', '+'))
      else:
         return u'{}/entityLink?entityName=user&id={}'.format(common.URL, self.uid)

   def get_avatar(self, size='big'):
      """Returns absolute path of specified size avatar.

      :param str size: poster size (see common.image_sizes)
      :return: URL
      :rtype: str or None
      """
      assert size in common.image_sizes
      if self.img:
         return u'{}/u{}.{}.jpg'.format(common.URL_CDN, self.img, common.image_sizes[size])

   def get_info(self):
      """Returns basic info about user and updates object parameters.

      :return: basic info
      :rtype: dict

      .. code:: python

         {
            'name': str(),
            'img': str() or None
         }
      """
      self.check_auth()
      # (this accept few uids)
      data = self._request('getUsersInfoShort', [[self.uid]])

      uinfo = data[0]
      result = {
         'name': uinfo[0],
         'img': common.img_path_to_relative(uinfo[1]),
        #'uid': uinfo[1]
      }
      self.name = result['name']
      self.img = result['img']
      return result

   def get_film_votes(self):
      """Returns unsorted film votes.

      :return: film votes
      :rtype: list

      .. code:: python

         [
            {
               'film': Film(uid, type),
               'date': str(), # Y-m-d
               'rate': int(),
               'favorite': bool(),
               'comment': str()
            }
         ]

      .. note::
         * This user need to have public votes or be authenticated user friend. Raises :func:`exceptions.RequestFailed` ('exc', 'PermissionDeniedException') otherwise.
         * This doesn't return film name. See :func:`Filmweb.update_films_info`

      """
      self.check_auth()
      unk = -1
      data = self._request('getUserFilmVotes', [self.uid, unk])

      #unk = data[0]
      results = []
      for v in data[1:]:
         results.append({
            'film': Film(fw=self.fw, uid=v[0], type=common.get_film_type_name(v[5])),
            'date': v[1],
            'rate': v[2],
            'favorite': bool(v[3]),
            'comment': v[4]
         })

      return results

   def get_want_to_see(self):
      """Returns list with wanted to see films.

      .. code:: python

         [
            {
               'film': Film(uid, type),
               'timestamp': int(), # in ms!
               'level': int() # 1-5
            }
         ]

      .. note::
         * This user needs to be authenticated user friend. Raises :func:`exceptions.RequestFailed` ('exc', 'PermissionDeniedException') otherwise.
         * This doesn't return film name. Use :func:`Filmweb.update_films_info`.

      """
      self.check_auth()
      unk = -1
      data = self._request('getUserFilmsWantToSee', [self.uid, unk])

      #unk = data[0]
      results = []
      for v in data[1:]:
         results.append({
            'film': Film(fw=self.fw, uid=v[0], type=common.get_film_type_name(v[3])),
            'timestamp': v[1],
            'level': v[2]
         })

      return results

class LoggedUser(User):
   def get_friends(self):
      """Returns friends.

      :return: friends
      :rtype: list

      .. code:: python

         [
            {
               'user': User(uid, name, img, sex, uid_fb, name_full),
               'similarity': int() or None,
               'following': bool()
            }
         ]
      """
      self.check_auth()
      data = self._request('getUserFriends')

      results = []
      for v in data:
         results.append({
            'user': User(fw=self.fw, uid=v[4], name=v[0], img=common.img_path_to_relative(v[1]), sex=v[6], uid_fb=v[5], name_full=v[3]),
            'similarity': v[2],
            'following': bool(v[7])
         })

      return results

   def get_person_votes(self):
      self.check_auth()
      unk = -1
      data = self._request('getUserPersonVotes', [self.uid, unk])

      #unk = data[0]
      results = []
      for v in data[1:]:
         results.append({
            'person': Person(fw=self.fw, uid=v[0]),
            'timestamp': v[1], # in ms
            'rate': v[2],
            'favorite': bool(v[3])
         })

      return results

   def remove_film_vote(self, film):
      """Removes film vote.

      :param :class:`Film` film: film
      """
      #self.set_film_vote(self, film=film, rate=-1, favorite=False, comment='')
      self._request('removeUserFilmVote', [film.uid], hmethod='POST')

   def set_film_vote(self, film, rate, favorite=False, comment=''):
      """Sets film vote.

      :param :class:`Film` film: film
      :param int rate: rate (0 = seen but no rate, 1 - 10 = rates)
      :param bool favorite: favorite
      :param str comment: film comment (max length = 160)

      .. note::
         * Raises :class:`ValueError` if comment length is greater than 160 characters.
         * It's not possible to remove comment using this. You need remove entire vote first.

      """
      assert isinstance(film, Film)
      assert isinstance(rate, int)
      assert isinstance(favorite, bool)
      assert isinstance(comment, str)
      if len(comment) > 160:
         raise ValueError('Comment max length is 160.')

      self.check_auth()
      self._request('addUserFilmVote', [[film.uid, rate, comment, int(favorite)]], hmethod='POST')

   def set_film_seen_date(self, film, date):
      """Changes film seen date.

      :param :class:`Film` film: film
      :param str date: seen date (can be incomplete)

      .. note:
         * Raises RequestFailed('exc', 'beforePremiere') if date is below film premiere.
         * Raises RequestFailed('exc', 'futureDate') if date is from future.
         * Raises RequestFailed('exc', 'unknownVote') if film doesn't have set premiere date.
      """
      self.check_auth()
      self._request('updateUserFilmVoteDate', [film.uid, str(date)], hmethod='POST')

   def set_want_to_see(self, film, level=3):
      """Mark film as wanted to see.

      :param :class:`Film` film: film
      :param int level: level (0-5)
      """
      self.check_auth()
      self._request('addUserFilmWantToSee', [film.uid, level], hmethod='POST')

   def read_notifications(self):
      """Marks notifications as read."""
      self.check_auth()
      self._request('markNotificationsRead', hmethod='POST')
