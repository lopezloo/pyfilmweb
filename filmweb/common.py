# -*- coding: utf-8 -*-

import _strptime
from datetime import datetime
import time
import re

API_KEY = 'qjcGhW2JnvGT9dfCt3uT_jozR3s'
API_VER = 2.7
URL     = 'http://www.filmweb.pl'
URL_CDN = 'http://1.fwcdn.pl'
URL_API = 'https://ssl.filmweb.pl/api'

# Poster sizes for film/serial/videogame
poster_sizes = {
   'large':  3,
   'big':    5,
   'normal': 6,
   'small':  2,
   'mini':   4,
   'tiny':   0,
   'square': 1
}

channel_icon_sizes = {
   'small':  0,
   'medium': 1,
   'big':    2
}

video_thumb_sizes = {
   'tiny':   0,
   'small':  3,
   'medium': 1,
   'big':    2,
   'large':  4
}

# Film, serial genres
film_genres = {
   'Akcja' : 28,
   'Animacja' : 2,
   'Anime' : 66,
   'Baśń' : 42,
   'Biblijny' : 55,
   'Biograficzny' : 3,
   'Czarna komedia' : 47,
   'Dla dzieci' : 4,
   'Dla młodzieży' : 41,
   'Dokumentalizowany' : 57,
   'Dokumentalny' : 5,
   'Dramat' : 6,
   'Dramat historyczny' : 59,
   'Dramat obyczajowy' : 37,
   'Dramat sądowy' : 65,
   'Dramat społeczny' : 69,
   'Dreszczowiec' : 46,
   'Edukacyjny' : 64,
   'Erotyczny' : 7,
   'Etiuda' : 45,
   'Fabularyzowany dok.' : 70,
   'Familijny' : 8,
   'Fantasy' : 9,
   'Fikcja literacka' : 75,
   'Film-Noir' : 27,
   'Gangsterski' : 53,
   'Groteska filmowa' : 60,
   'Historyczny' : 11,
   'Horror' : 12,
   'Karate' : 54,
   'Katastroficzny' : 40,
   'Komedia' : 13,
   'Komedia dokumentalna' : 74,
   'Komedia kryminalna' : 58,
   'Komedia obycz.' : 29,
   'Komedia rom.' : 30,
   'Kostiumowy' : 14,
   'Krótkometrażowy' : 50,
   'Kryminał' : 15,
   'Melodramat' : 16,
   'Musical' : 17,
   'Muzyczny' : 44,
   'Niemy' : 67,
   'Nowele filmowe' : 18,
   'Obyczajowy' : 19,
   'Poetycki' : 62,
   'Polityczny' : 43,
   'Prawniczy' : 52,
   'Propagandowy' : 76,
   'Przygodowy' : 20,
   'Przyrodniczy' : 73,
   'Psychologiczny' : 38,
   'Płaszcza i szpady' : 68,
   'Religijny' : 51,
   'Romans' : 32,
   'Satyra' : 39,
   'Sci-Fi' : 33,
   'Sensacyjny' : 22,
   'Sportowy' : 61,
   'Surrealistyczny' : 10,
   'Szpiegowski' : 63,
   'Sztuki walki' : 72,
   'Thriller' : 24,
   'Western' : 25,
   'Wojenny' : 26,
   'XXX' : 71
}

# Game genres
game_genres = {
   'Przygodowa': 1,
   'Zręcznościowa': 2,
   'TPP': 3,
   'RPG': 4,
   'FPP': 5,
   'FPS': 6,
   'RTS': 7,
   'Strategia': 8,
   'Platformowa': 9,
   'Familijna': 10,
   'Wyścigi': 11,
   'TPP/FPS': 12,
   'Filmowa': 13,
   'Shooter': 14,
   'Survival Horror': 15,
   'Bijatyka': 16,
   'Sportowa': 17,
   'Ekonomiczna': 18,
   'Symulator': 19,
   'MMORPG': 20,
   'Skradanka': 21,
   'Edukacyjna': 22,
   'Logiczna': 23,
   'Turowa': 24,
   'Quiz': 25,
   'Planszowa': 26,
   'Taktyczna': 27,
   'Hazard': 28,
   'Tekstowa': 29,
   'Dla dzieci': 30,
   'Pornografia': 31,
   'Akcja': 32,
   'TPS': 33,
   'Muzyczna': 34,
   'Menedżer': 35,
   'Sieciowa': 36,
   'Fitness': 37,
   'Taneczna': 38
}

def get_genre_id(film_type, genre_name):
   if film_type == 'film' or film_type == 'serial':
      container = film_genres
   elif film_type == 'videogame':
      container = game_genres

   if genre_name in container:
      return container[genre_name]

person_role_types = {
   'Reżyser': 1,
   'Scenarzysta': 2,
   'Autor muzyki': 3,
   'Operator zdjęć': 4,
   'Na podstawie': 5,
   'Aktor': 6,
  #'Aktor': 7, # same as 6? 
  #'Aktor': 8, # same as 6?
   'Producent': 9,
   'Montażysta': 10
}

def get_role_type_id(role_name):
   if role_name in person_role_types:
      return person_role_types[role_name]

def get_role_type_str(rid):
   for k, v in person_role_types.items():
      if v == rid:
         return k

image_sizes = {
   'small': 0,
   'big': 1,
   'square': 2,
   'medium': 3
}

film_types = ['film', 'serial', 'videogame']
film_type_ids = {
   'film': 0,
   'serial': 1,
   'videogame': 2
}

def get_film_type_id(film_name):
   if film_name in film_type_ids:
      return film_type_ids[film_name]

def get_film_type_name(film_id):
   return film_types[film_id]

def trailer_url_to_uid(url):
   if url:
      r = re.match('http:\/\/mm.filmweb.pl\/(.*)\..*\.mp4', url)
      if r:
         return int(r.group(1))

def video_img_url_to_uid(url):
   if url:
      r = re.search('\.(\d+)', url)
      if r:
         return int(r.group(1))

def sex_id_to_str(uid):
   if uid == 1:
      return 'F'
   elif uid == 2:
      return 'M'

def img_path_to_relative(path):
   if path:
      return path[:-6].replace(URL_CDN, '')
