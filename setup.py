from setuptools import setup, find_packages

setup(
    name = 'nextbus',
    version = '0.1',
    author = 'Daniel Duckworth',
    author_email = 'duckworthd@gmail.com',
    description = 'An API for nextbus.com',
    license = 'BSD',
    keywords = 'bus data muni',
    url = 'github.com/duckworthd/nextbus',
    packages = find_packages(),
    classifiers = [
      'Development Status :: 4 - Beta',
      'License :: OSI Approved :: BSD License',
      'Operating System :: OS Independent',
      'Programming Language :: Python',
    ],
    install_requires = [     # dependencies
      'configurati',
      'requests',
    ],
    tests_require = [     # test dependencies
    ]
)
