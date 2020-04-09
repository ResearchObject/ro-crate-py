#!/usr/bin/env python

## Copyright 2019-2020 The University of Manchester, UK
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

from typing import List

from .. import vocabs
from ..utils import *

class Entity(object):
    def __init__(self, identifier: str, metadata):
        self.id = identifier
        self._metadata = metadata
        self._entity = metadata._find_entity(identifier)
        if self._entity is None:
            self._entity = metadata._add_entity(self._empty())

    def __repr__(self):
        return "<%s %s>" % (self.id, self.type)

    @property
    def _default_type(self):
        clsName = self.__class__.__name__
        if clsName in vocabs.RO_CRATE["@context"]:
            return clsName
        return "Thing"

    def _empty(self):
        val = {     
            "@id": self.id,
            "@type": self._default_type
        }        
        return val

    def __getitem__(self, key: str):
        return self._entity[key]

    def __setitem__(self, key: str, value):
        # TODO: Disallow setting non-JSON values
        self._entity[key] = value

    def __delitem__(self, key: str):
        del self._entity[key]

    def get(self, key: str, default=None):
        return self._entity.get(key, default)

    @property
    def type(self) -> str:
        return first(self.types)

    @property
    def types(self)-> List[str]:
        return tuple(as_list(self.get("@type", "Thing")))

class Thing(Entity):
    pass
