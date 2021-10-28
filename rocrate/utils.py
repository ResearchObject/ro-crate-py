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

import collections
from datetime import datetime, timezone
from urllib.parse import urlsplit


def first(iterable):
    for e in iterable:
        return e
    return None


def flatten(single_or_multiple):
    if len(single_or_multiple) == 1:
        return single_or_multiple[0]
    return single_or_multiple  # might be empty!


def as_list(list_or_other):
    if list_or_other is None:
        return []
    if (isinstance(list_or_other, collections.Sequence)
        and not isinstance(list_or_other, str)):  # FIXME: bytes?
        return list_or_other
    return [list_or_other]


def is_url(string):
    parts = urlsplit(string)
    return all((parts.scheme, parts.netloc, parts.path))


def iso_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def subclasses(cls):
    """\
    Recursively iterate through all subclasses (direct and indirect) of cls.

    Subclasses appear before their parent classes, but ordering is otherwise
    undefined. For instance, if Cat and Dog are subclasses of Pet and Beagle
    is a subclass of Dog, then Beagle will appear before Dog.
    """
    direct = cls.__subclasses__()
    for d in direct:
        for c in subclasses(d):
            yield c
        yield d
