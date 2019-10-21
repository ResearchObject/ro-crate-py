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

import datetime

from .utils import *

"""
RO-Crate metadata file

This object holds the data of an RO Crate Metadata File rocrate_

.. _rocrate: https://w3id.org/ro/crate/0.2
"""


class _Entity(object):
    def __init__(self, identifier, metadata):
        self.id = identifier
        self._metadata = metadata
        self._entity = metadata._find_entity(identifier)
        if self._entity is None:            
            self._entity = metadata._add_entity(self._empty())

    def __repr__(self):
        return "<%s %s>" % (self.id, self.type)

    def _empty(self):        
        return {     
                    "@id": self.id,
                    "@type": self.type ## Assumes just one type
               }

    @property
    def type(self):
        return first(self.types)

    @property
    def types(self):
        return (self._entity.get("@type", "Thing"),) ## TODO: Avoid double-list!

class Metadata(_Entity):    
    def __init__(self):
        self._jsonld = self._template()  ## bootstrap needed by the below!
        super().__init__("ro-crate-metadata.jsonld", self)

    def _template(self):
        # Hard-coded bootstrap for now
        return {
            "@context": "https://w3id.org/ro/crate/0.2/context",
            "@graph": [
                {
                    "@id": "ro-crate-metadata.jsonld",
                    "@type": "CreativeWork",
                    "identifier": "ro-crate-metadata.jsonld",
                    "about": {"@id": "./"}
                },
                {
                    "@id": "./",
                    "@type": "Dataset"
                }
            ]
        }

    def _find_entity(self, identifier):
        for item in self._jsonld["@graph"]:
            if item.get("@id", None) == identifier:
                return item

    def _add_entity(self, entity):
        ## TODO: Check/merge duplicates? Valid by JSON-LD, but 
        # we won't find the second entry again above
        self._jsonld["@graph"].add(entity)
        return entity # TODO: If we merged, return that instead here

    @property
    def about(self):
        return Dataset("./", self)

    @property
    def root(self):
        return self.about

    def as_jsonld(self):
        return self._jsonld
    
class Dataset(_Entity):
    def __init__(self, identifier, metadata):
        super().__init__(identifier, metadata)
        self.datePublished = datetime.datetime.now() ## TODO: pick it up from _metadata

    @property
    def types(self):
        return ("Dataset",) ## Hardcoded for now

    @property
    def datePublished(self, date=None):
        return datetime.datetime.fromisoformat(self._entity["datePublished"])
    
    @datePublished.setter
    def datePublished(self, date):
        self._entity["datePublished"] = date.isoformat()
