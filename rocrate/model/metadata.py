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

import warnings
import json
import pkg_resources

from typing import Dict

from ..utils import *

from .entity import Entity
from .dataset import Dataset
from .contextentity import ContextEntity

"""
RO-Crate metadata file

This object holds the data of an RO Crate Metadata File rocrate_

.. _rocrate: https://w3id.org/ro/crate/1.0
"""
class Metadata(Entity):
    def __init__(self):
        self._jsonld = self._template()  ## bootstrap needed by the below!
        self.dest_path = 'ro-crate-metadata.jsonld' 
        super().__init__("ro-crate-metadata.jsonld", self)

    def _template(self):
        # Hard-coded bootstrap for now
        return {
            "@context": "https://w3id.org/ro/crate/1.0/context",
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

    def _find_entity(self, identifier: str) -> Entity:
        for item in self._jsonld["@graph"]:
            if item.get("@id", None) == identifier:
                return item

    def _add_entity(self, entity: Entity) -> Entity:
        ## TODO: Check/merge duplicates? Valid by JSON-LD, but 
        # we won't find the second entry again above
        self._jsonld["@graph"].append(entity)
        return entity # TODO: If we merged, return that instead here

    def write(dest_base):
        #writes itself 
        dest_path = os.path.join(dest_base, self.dest_path)
        with open(dest_path, 'w') as outfile:
            json.dump(as_jsonld, outfile)

    """The dataset this is really about"""
    about = ContextEntity(Dataset)

    @property
    def root(self) -> Dataset:
        return self.about

    def as_jsonld(self) -> Dict:
        return self._jsonld
