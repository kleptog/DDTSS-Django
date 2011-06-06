from setuptools import setup, find_packages
#from distutils.core import setup, Extension

setup(name="ddtp", version="0.1",
      description='Debian Distributed Translation System Satellite',
      author='Martijn van Oosterhout',
      author_email='kleptog@svana.org',
      packages = find_packages('src'),
      package_dir = {'': 'src'},
      zip_safe=False,      
      install_requires=['setuptools', 
                        'psycopg2', 
                        'SQLalchemy',
                        'django-debug-toolbar'])
