#!/usr/bin/env python

# Copyright 2019-2021 The University of Manchester, UK
# Copyright 2020-2021 Vlaams Instituut voor Biotechnologie (VIB), BE
# Copyright 2020-2021 Barcelona Supercomputing Center (BSC), ES
# Copyright 2020-2021 Center for Advanced Studies, Research and Development in Sardinia (CRS4), IT
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from setuptools import setup, find_packages
from codecs import open
from os import path
import re

# https://www.python.org/dev/peps/pep-0440/#appendix-b-parsing-version-strings-with-regular-expressions  # noqa
PEP440_PATTERN = r"([1-9][0-9]*!)?(0|[1-9][0-9]*)(\.(0|[1-9][0-9]*))*((a|b|rc)(0|[1-9][0-9]*))?(\.post(0|[1-9][0-9]*))?(\.dev(0|[1-9][0-9]*))?"  # noqa


here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

with open(path.join(here, 'requirements.txt'), encoding='utf-8') as f:
    required = f.read().splitlines()

with open(path.join(here, 'rocrate', '_version.py'), encoding='utf-8') as f:
    # "parse" rocrate/_version.py which MUST have this pattern
    # __version__ = "0.1.1"
    # see https://www.python.org/dev/peps/pep-0440
    v = f.read().strip()
    m = re.match(r'^__version__ = "(' + PEP440_PATTERN + ')"$', v)
    if not m:
        msg = ('rocrate/_version.py did not match pattern '
               '__version__ = "0.1.2"  (see PEP440):\n') + v
        raise Exception(msg)
    __version__ = m.group(1)


setup(
    name='rocrate',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    version=__version__,  # update in rocrate/_version.py
    description='RO-Crate metadata generator/parser',
    long_description_content_type='text/markdown',
    long_description=long_description,
    author=", ".join((
        'Bert Droesbeke',
        'Ignacio Eguinoa',
        'Alban Gaignard',
        'Simone Leo',
        'Luca Pireddu',
        'Laura Rodríguez-Navas',
        'Stian Soiland-Reyes'
    )),
    python_requires='>=3.6',
    author_email='stain@apache.org',
    package_data={'': ['data/*.jsonld', 'templates/*.j2']},
    # SPDX, pending https://github.com/pombredanne/spdx-pypi-pep/pull/2
    license="Apache-2.0",
    url='https://github.com/ResearchObject/ro-crate-py/',
    download_url=('https://github.com/researchobject/ro-crate-py/archive/'
                  f'{__version__}.tar.gz'),
    keywords="researchobject ro-crate ro metadata jsonld",
    install_requires=[required],
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
    entry_points={
        "console_scripts": ["rocrate=rocrate.cli:cli"],
    },
)
