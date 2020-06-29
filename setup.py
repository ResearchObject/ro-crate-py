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
__copyright__   = "Copyright 2019 The University of Manchester"
__license__     = "Apache License, version 2.0 (https://www.apache.org/licenses/LICENSE-2.0)"

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
  long_description = f.read()

with open(path.join(here, 'requirements.txt'), encoding='utf-8') as f:
    required = f.read().splitlines()

setup(
  name = 'rocrate',
  packages = find_packages(exclude=['contrib', 'docs', 'tests']), # Required
  version = '0.0.1.dev0',
  description = 'RO-Crate metadata generator/parser',
  long_description=long_description,
  author = 'Stian Soiland-Reyes',
  author_email = 'stain@apache.org',
  
  # https://www.apache.org/licenses/LICENSE-2.0
  license = "Apache-2.0", ## SPDX, pending https://github.com/pombredanne/spdx-pypi-pep/pull/2
  #url = 'http://ro-crate.readthedocs.io/',
  #download_url = 'https://github.com/researchobject/ro-crate-py/archive/0.1.0.tar.gz',
  keywords = "researchobject ro-crate ro metadata jsonld",
  # license_file= "LICENSE.txt", ## implied
  install_requires=[required],
  test_suite='test',
  classifiers=[
    # https://pypi.python.org/pypi?%3Aaction=list_classifiers
    'Development Status :: 1 - Planning',
    #'Development Status :: 2 - Pre-Alpha',  ## TODO

    'Intended Audience :: Developers',
    'Intended Audience :: Information Technology',
    'Topic :: Software Development :: Libraries',

     # 'License :: OSI Approved :: Apache Software License',
     # aboveis misleading, see https://github.com/pypa/pypi-legacy/issues/564
     # and https://github.com/pombredanne/spdx-pypi-pep/pull/2
     #'License :: OSI Approved',
     # 'License :: OSI Approved :: Apache License, Version 2.0 (Apache-2.0)',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Topic :: Internet',
    'Topic :: Internet :: WWW/HTTP',
    'Topic :: System :: Archiving',
    'Topic :: System :: Archiving :: Packaging',
],
  
)
