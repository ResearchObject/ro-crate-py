#!/usr/bin/env python

## Copyright 2019 The University of Manchester, UK
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##     http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.

__author__      = "Stian Soiland-Reyes <http://orcid.org/0000-0001-9842-9718>"
__copyright__   = """© 2019-2020 The University of Manchester, UK
© 2020 Vlaams Instituut voor Biotechnologie (VIB), DE
© 2020 Barcelona Supercomputing Center (BSC), ES
"""

__license__     = "Apache License, version 2.0 (https://www.apache.org/licenses/LICENSE-2.0)"

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
  long_description = f.read()

with open(path.join(here, 'requirements.txt'), encoding='utf-8') as f:
    required = f.read().splitlines()

setup(
  name = 'rocrate',
  packages = find_packages(exclude=['contrib', 'docs', 'tests']),
  version = '0.1.0',
  description = 'RO-Crate metadata generator/parser',
  long_description_content_type='text/markdown',
  long_description=long_description,
  author = 'Bert Droesbeke, Ignacio Eguinoa, Stian Soiland-Reyes, Laura Rodríguez Navas, Alban Gaignard',
  python_requires='>=3.6',
  author_email = 'stain@apache.org',
  package_data={'': ['data/*.jsonld','templates/*.j2']},
  license = "Apache-2.0", ## SPDX, pending https://github.com/pombredanne/spdx-pypi-pep/pull/2
  url = 'https://github.com/ResearchObject/ro-crate-py/',
  #download_url = 'https://github.com/researchobject/ro-crate-py/archive/0.1.0.tar.gz',
  keywords = "researchobject ro-crate ro metadata jsonld",
  install_requires=[required],
  test_suite='test',
  classifiers=[
    'Operating System :: OS Independent',
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'Intended Audience :: Information Technology',
    'Topic :: Software Development :: Libraries',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Topic :: Internet',
    'Topic :: Internet :: WWW/HTTP',
    'Topic :: System :: Archiving',
    'Topic :: System :: Archiving :: Packaging',
],
  
)
