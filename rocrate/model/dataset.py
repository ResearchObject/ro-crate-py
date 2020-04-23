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

import datetime

from .entity import Entity
from .contextentity import ContextEntity
from .creativework import CreativeWork
from .file import File
from .person import Person
from . import metadata

class Dataset(Entity):

    def __init__(self,source, dest_path = None , properties = None,  metadata: 'metadata.Metadata'= None):
        if os.path.exists(source):
            self.source = source
            if not dest_path:
                self.id = source
            else:
                self.id = dest_path
            #create Dataset entity
            super().__init__(identifier, metadata)
            self.directory_entries = []
            # iterate over the dir contents to create entities with each file
            for subfile in os.listdir(directory):
                subfile_entity = File(subfile)
                directory_entries.append(subfile_entity)
                self.add_subfile(subfile)
            self._jsonld["datePublished"] = datetime.datetime.now() ## TODO: pick it up from _metadata
        else:
            print('Not a directory or not accessible')
            return None
    #author = ContextEntity(Person)
    #license = ContextEntity(CreativeWork)

    def _empty(self):
        val = {
            "@id": self.id,
            "@type": 'Dataset',
            "@hasPart": []
            #name contentSize dateModified encodingFormat identifier sameAs
        }
        return val

    def add_subfile(file_entity):
        self._jsonld['@hasPart'].append({"@id": subfile_entity.get_id()})

    @property
    def datePublished(self):
        date = self.get("datePublished")
        return date and datetime.datetime.fromisoformat(date)

    @datePublished.setter
    def datePublished(self, date):
        if hasattr(date, "isoformat"): # datetime object
            self["datePublished"] = date.isoformat()
        else:
            self["datePublished"] = str(date)

    def write(self, base_path):
        out_path = os.path.join(base_path, self.dest)
        for file in self.directory_entries:
            out_path.write()

