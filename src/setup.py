__author__="Matthias Bady <aegirxx at gmail.com>"
__date__ ="$31.05.2013 00:11:03$"

from setuptools import setup,find_packages

setup (
  name = 'IngressBot',
  version = '0.1',
  packages = find_packages(),

  # Declare your packages' dependencies here, for eg:
  install_requires=['foo>=3'],

  # Fill in these to make your Egg ready for upload to
  # PyPI
  author = 'Matthias Bady <aegirxx at gmail.com>',
  author_email = '',

  summary = 'Just another Python package for the cheese shop',
  url = '',
  license = '',
  long_description= 'Long description of the package',

  # could also include long_description, download_url, classifiers, etc.

  
)