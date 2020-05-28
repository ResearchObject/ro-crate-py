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
import uuid
from .. import vocabs
from ..utils import *

class Entity(object):

    # identifier: String
    # properties: dict. Properties of this Entity entry.
    def __init__(self, crate, identifier = None, properties = None):
        self.crate = crate
        if identifier:
            self.id = identifier
        else:
            self.id = uuid.uuid1()
        if properties:
            empty = self._empty()
            empty.update(properties)
            self._jsonld = empty
            # print('properties are ' + self.as_jsonld())
        else:
            # this would only occur when calling from a sublcass that calls super() with no properties, or initializing from Entity class directly.
            self._jsonld = self._empty()
        # if metadata:
            # #self._metadata = metadata
            # print('adding to metadata of item:', self.id)
            # self._jsonld = metadata._find_entity(identifier)  # ******IF THE ENTITY IS THE METADATA ENTITY THEN JSONLD shouldnt be assigned because it contains all the elements

            # print("jsonld is now ",self._jsonld)
            # print("metadata is ", metadata._jsonld)
            # if self._jsonld is None:
                # self._jsonld = metadata._add_entity(self._empty())

    def __repr__(self):
        return "<%s %s>" % (self.id, self.type)

    def properties(self):
        #print('entity properties')
        #print(self.id)
        return self._jsonld

    def as_jsonld(self):
        return self._jsonld

    @property
    def _default_type(self):
        clsName = self.__class__.__name__
        if clsName in vocabs.RO_CRATE["@context"]:
            return clsName
        return "Thing"

    def reference(self):
        return {'@id': self.id }

    def _empty(self):
        val = {
            "@id": self.id,
            "@type": self._default_type
        }
        return val

    # def __getitem__(self, key: str):
        # return self._jsonld[key]

    # def __setitem__(self, key: str, value):
        # # TODO: Disallow setting non-JSON values
        # self._jsonld[key] = value

    # def __delitem__(self, key: str):
        # del self._jsonld[key]

    def getitem(self, key: str, default=None):
        return self._jsonld[key]

    def setitem(self, key: str, value):
        if isinstance(object, list):
            for item in value:
                self.setitem(self,key,item)
        if isinstance(value, Entity): 
            # add reference to an Entity
            self._jsonld[key] = value.reference()  # I assume it is already in the crate...
        else:
            self._jsonld[key] = value.reference()

    @property
    def type(self) -> str:
        return first(self.types)

    @property
    def types(self)-> List[str]:
        return tuple(as_list(self.get("@type", "Thing")))

    def filepath():
        return self.id   # should I parse it? remove initial / and decode %20 etc.
