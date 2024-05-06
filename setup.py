import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.txt')) as f:
    CHANGES = f.read()

"""We're using conda to create dependencies, mainly because rpy2 installation
works much better that way, so we will omit all dependencies here.
requires = [
    'pandas',
    'tables',
    'pyramid',
    'pyramid_beaker',
    'pyramid_mailer',
    'pyramid_mako',
    'pyramid_debugtoolbar',
    'SQLAlchemy',
    'zope.sqlalchemy',
    'pyramid_tm',
    'transaction',
    'waitress',
    'genedataset',
    'rpy2==2.7.0',
    'selenium',
    'itsdangerous',
    ]
"""
requires = []

tests_require = [
    'locustio',
    ]

tests_require = [
    'webtest',
    'locustio',
    ]

setup(name='haemosphere',
      version='0.0',
      description='haemosphere',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='Jarny Choi',
      author_email='haemosphere@gmail.com',
      url='haemosphere.org',
      keywords='bioinformatics',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      extras_require={
          'testing': tests_require,
      },
      install_requires=requires,
      tests_require=requires,
      test_suite="haemosphere",
      entry_points="""\
      [paste.app_factory]
      main = haemosphere:main
      [console_scripts]
      initdb = initdb:main
      migrate_hdf2db = migrate_hdf2db:main
      init_testdata = init_testdata:main
      """,
      )
