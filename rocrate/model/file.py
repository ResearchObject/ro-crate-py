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
import pathlib
import shutil
import urllib

from io import IOBase
from shutil import copy
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse

from .data_entity import DataEntity

class File(DataEntity):

    def __init__(self, crate, source=None, dest_path=None, fetch_remote=False, validate_url=True,properties={}):
        #...process source
        self.fetch_remote = fetch_remote
        self.source = source
        if dest_path:
            # the entity is refrencing a path relative to the ro-crate root
            identifier = dest_path  # relative path?
        else:
            # if there is no dest_path there must be a URI/local path as source
            if os.path.isfile(source):
                # local source -> becomes local reference = reference relative to ro-crate root
                identifier = os.path.basename(source)
            else:
                # entity is refering an external object (absolute URI)
                # first chec that it is a valid remote URI
                url = urlparse(source)
                if not all([url.scheme, url.netloc, url.path]):
                    # throw exception
                    raise Exception("Source is not a path to a local file or a valid remote URI")
                if validate_url:
                    # specification says remote URI should always be accessible but added this as optional to give the possibility of building off line (or behind a different landing page?)
                    # the fetching of the remote file/dataset itself (if enable) is only done during ro-crate writing
                    # but here we can fetch some properties of the remote file if possible
                    try:
                        response = urllib.request.urlopen(source)
                    except HTTPError as e:
                        # do something
                        print('Remote URI not accessible', e.code)
                    else:
                        properties.update({'contentSize': response.getheader('Content-Length'), 'encodingFormat':response.getheader('Content-Type')})
                if fetch_remote:
                    # the entity will be referencing a local file (so it has a local relative id), independently of the source being external
                    identifier = os.path.basename(source)
                else:
                    identifier = source
                if not properties:
                    properties = {}
                # set url to the source
                # when creating through workflowhub this is auto set to URL Workflow Hub page
                properties.update({'url':source})
        super(File, self).__init__(crate, identifier, properties)

    def _empty(self):
        val = {
            "@id": self.id,
            "@type": 'File'
        }
        return val

    def write(self, base_path):
        out_file_path = os.path.join(base_path, self.id)
        out_dir = pathlib.Path(os.path.dirname(out_file_path))
        # check if its local or remote URI
        if isinstance(self.source,IOBase):
            if not out_dir.exists():
                os.mkdir(out_dir)
            with open(out_file_path, 'w') as out_file:
                out_file.write(self.source.getvalue())
        else:
            if os.path.isfile(self.source):
                if not out_dir.exists():
                    os.mkdir(out_dir)
                copy(self.source, out_file_path)
            else:
                if self.fetch_remote:
                    try:
                        #Legacy version
                        # urllib.request.urlretrieve(self.source, out_file_path)
                        # can check that the encodingFormat and contentSize matches the request data? i.e response.getheader('Content-Length') == self._jsonld['contentSize']
                        # this would help check if the dataset to be retrieved is in fact what was registered in the first place. 
                        with urllib.request.urlopen(self.source) as response, open(out_file_path, 'wb') as out_file:
                            shutil.copyfileobj(response, out_file)
                    except: # requests.ConnectionError as exception:
                        print("URI does not exists or can't be accessed")

    def write_zip(self, zip_out):
        zip_out.write(self.source, self.id)
