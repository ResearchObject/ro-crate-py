#!/usr/bin/env python

# Copyright 2019-2022 The University of Manchester, UK
# Copyright 2020-2022 Vlaams Instituut voor Biotechnologie (VIB), BE
# Copyright 2020-2022 Barcelona Supercomputing Center (BSC), ES
# Copyright 2020-2022 Center for Advanced Studies, Research and Development in Sardinia (CRS4), IT
# Copyright 2022 École Polytechnique Fédérale de Lausanne, CH
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

import os
from datetime import datetime, timezone
from urllib.parse import urlsplit


def is_url(string):
    parts = urlsplit(string)
    if os.name == "nt" and len(parts.scheme) == 1:
        return False
    return all((parts.scheme, parts.path))


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


def get_norm_value(json_entity, prop):
    """\
    Get a normalized value for a property (always as a list of strings).
    """
    value = json_entity.get(prop, [])
    if not isinstance(value, list):
        value = [value]
    try:
        return [_ if isinstance(_, str) else _["@id"] for _ in value]
    except (TypeError, KeyError):
        raise ValueError(f"Malformed value for {prop!r}: {json_entity.get(prop)!r}")


def walk(top, topdown=True, onerror=None, followlinks=False, exclude=None):
    exclude = frozenset(exclude or [])
    for root, dirs, files in os.walk(top):
        if exclude:
            dirs[:] = [_ for _ in dirs if _ not in exclude]
            files[:] = [_ for _ in files if _ not in exclude]
        yield root, dirs, files
