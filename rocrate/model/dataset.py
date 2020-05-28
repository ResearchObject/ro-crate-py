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
import os

from .data_entity import DataEntity
from .contextentity import ContextEntity
from .creativework import CreativeWork
from .file import File
from .person import Person
from . import metadata

class Dataset(DataEntity):

    def __init__(self, crate, source = None, dest_path = None , properties = None):
        identifier = None
        self.source = source
        if not dest_path:
            identifier = os.path.dirname(source)
        else:
            identifier = dest_path
        if source and os.path.exists(source):
            self.directory_entries = []
            # iterate over the dir contents to create entries for each file
            # TODO: for the moment I just save a tuple (source, relative_dest)
            # source: full origin path
            # relative_desth: file path relative to directory entity path (id)
            for base,subd,f in os.walk(source):
                for filename in f:
                    file_source = os.path.join(base,filename)
                    rel_path = os.path.relpath(source, file_source)
                    file_entry = (file_source,rel_path)
                    directory_entries.append(file_entry)
        super().__init__(crate, identifier, properties)

    def _empty(self):
        val = {
            "@id": self.id,
            "@type": 'Dataset'
        }
        return val

    def properties(self):
        super().properties()

    #name contentSize dateModified encodingFormat identifier sameAs
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
        if self.source:
            out_path = os.path.join(base_path, self.dest)
            # iterate over the entries
            for file in self.directory_entries:
                out_path.write()

