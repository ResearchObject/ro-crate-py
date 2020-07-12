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

import os

from shutil import copy
import pathlib
import requests
import urllib

from .data_entity import DataEntity

class File(DataEntity):

    def __init__(self, crate, source=None, dest_path=None, fetch_remote=False, properties=None):
        #...process source
        self.fetch_remote = fetch_remote
        self.source = source
        if dest_path:
            # the entity is refrencing a path relative to the ro-crate root
            identifier = dest_path  # relative path?
        else:
            # if there is no dest_path there must be a source 
            if os.path.isfile(source):
                # local source -> becomes local reference = reference relative to ro-crate root
                identifier = os.path.basename(source)
            else:
                # entity is refering an external object and the id should be a valid absolute URI
                # check that it is a valid URI, doesn't need to be accessible
                try:
                    # if response.status_code == 200:
                    response = requests.get(source)
                except requests.ConnectionError as exception:
                    print("Source is not a valid URI")
                if fetch_remote: # the entity will be referencing a local file, independently of the source being external
                    # should I check the source is accessible?
                    identifier = os.path.basename(source)
                    #TODO: should add isBasedOn property?
                else:
                    identifier = source
        super(File, self).__init__(crate, identifier, properties)

    def _empty(self):
        val = {
            "@id": self.id,
            "@type": 'File'
        }
        return val

    def write(self, base_path):
        # check if its local or remote URI
        if os.path.isfile(self.source):
            out_file_path = os.path.join(base_path, self.id)
            out_dir = pathlib.Path(os.path.dirname(out_file_path))
            if not out_dir.exists():
                os.mkdir(out_dir)
            copy(self.source, out_file_path)
        else:
            if self.fetch_remote:
                print('')
                out_file_path = os.path.join(base_path, self.id)
                out_dir = pathlib.Path(os.path.dirname(out_file_path))
                if not out_dir.exists():
                    os.mkdir(out_dir)
                try:
                    urllib.request.urlretrieve(self.source, out_file_path)
                except requests.ConnectionError as exception:
                    print("URI does not exists or can't be accessed")

    def write_zip(self, zip_out):
        zip_out.write(self.source, self.id)
