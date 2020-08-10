try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'A version of a Snake Game with Pygame',
    'author': 'Niklas Moberg',
    'url': 'URL to get it at.',
    'download_url': 'Where to download it.',
    'author_email': '',
    'version': '0.1',
    'install_requires': ['pygame'],
    'packages': ['snake'],
    'scripts': [],
    'name': 'snake'
}


setup(**config)
