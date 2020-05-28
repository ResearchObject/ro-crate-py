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

import json
import os
import pkg_resources
import warnings

from typing import Dict

from ..utils import *

from .file import File
from .dataset import Dataset
from .contextentity import ContextEntity

"""
RO-Crate metadata file

This object holds the data of an RO Crate Metadata File rocrate_

.. _rocrate: https://w3id.org/ro/crate/1.0
"""
class Metadata(File):
    CONTEXT = "https://w3id.org/ro/crate/1.0/context"
    def __init__(self, crate):
        #self._jsonld = self._empty()  ## bootstrap needed by the below!
        #self.dest_path = 'ro-crate-metadata.jsonld'
        super().__init__(crate, None, "ro-crate-metadata.jsonld", None)

    def _empty(self):
        # default properties of the metadata entry
        val = {
                    "@id": "ro-crate-metadata.jsonld",
                    "@type": "CreativeWork",
                    "about": {"@id": "./"}
                }
        return val

    # def _find_entity(self, identifier: str) -> Entity:
        # print(self._jsonld.keys())
        # for item in self._jsonld['@graph']:
            # if item.get("@id", None) == identifier:
                # return item

    # def _add_entity(self, entity: Entity) -> Entity:
        # ## TODO: Check/merge duplicates? Valid by JSON-LD, but 
        # # we won't find the second entry again above
        # self._jsonld["@graph"].append(entity)
        # print('@graph keys are ', self._jsonld.keys())
        # return entity # TODO: If we merged, return that instead here


    # Generate the crate's `ro-crate-metadata.jsonld`.
    # @return [String] The rendered JSON-LD as a "prettified" string.
    def generate(self):
        graph = []
        for entity in self.crate.get_entities():
            graph.append(entity.properties())
        return {'@context': self.CONTEXT, '@graph': graph}

    def write(self, dest_base):
        #writes itself in
        write_path = self.filepath(dest_base)
        as_jsonld = self.generate()
        with open(write_path, 'w') as outfile:
            json.dump(as_jsonld, outfile, indent=4, sort_keys=True, default=str)

    """The dataset this is really about"""
    about = ContextEntity(Dataset)

    @property
    def root(self) -> Dataset:
        return self.about

    #def as_jsonld(self) -> Dict:
    #    return self._jsonld
