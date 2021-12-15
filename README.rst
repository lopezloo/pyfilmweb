=========
pyfilmweb
=========
.. image:: https://readthedocs.org/projects/pyfilmweb/badge/
    :target: https://pyfilmweb.readthedocs.org/
    :alt: Documentation Status

______
**NOTE: This package doesn't work anymore.** Sadly Filmweb decided to discontinue their app and shut down API.
______

Python package for Filmweb unofficial API.

========
Features
========
* search function
* access to movies, games, TV shows, persons, TV channels, cinemas
* access to trailers and Filmweb productions
* access to user features
* no scraping - uses API, which is faster and more reliable
* support for Python 2.7 & 3.4+

============
Installation
============
.. code::

  pip install pyfilmweb


=======
Example
=======
.. code:: python

  from filmweb.filmweb import Filmweb
  fw = Filmweb()
  items = fw.search('Jak działa jamniczek')
  item = items[0] # grab first result
  info = item.get_info() # fetch more info
  print('Title: {} ({}) Rate: {} ({} votes) Description: {}'.format(item.name, item.year, item.rate, item.votes, info['description_short']))


For more, see full documentation - https://pyfilmweb.readthedocs.io/.
