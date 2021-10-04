#!/usr/bin/env python

# Copyright 2019-2021 The University of Manchester, UK
# Copyright 2020-2021 Vlaams Instituut voor Biotechnologie (VIB), BE
# Copyright 2020-2021 Barcelona Supercomputing Center (BSC), ES
# Copyright 2020-2021 Center for Advanced Studies, Research and Development in Sardinia (CRS4), IT
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
from pathlib import Path
import shutil
import urllib.request

from io import IOBase
from urllib.error import HTTPError

from .data_entity import DataEntity
from ..utils import is_url


class File(DataEntity):

    def __init__(self, crate, source=None, dest_path=None, fetch_remote=False,
                 validate_url=True, properties=None):
        if properties is None:
            properties = {}
        self.fetch_remote = fetch_remote
        self.source = source
        if not isinstance(source, (str, Path)) and dest_path is None:
            raise ValueError("dest_path must be provided if source is not a path or URI")
        if dest_path:
            # the entity is refrencing a path relative to the ro-crate root
            identifier = Path(dest_path).as_posix()  # relative path?
        else:
            # if there is no dest_path there must be a URI/local path as source
            if not is_url(str(source)):
                # local source -> becomes local reference = reference relative
                # to ro-crate root
                identifier = os.path.basename(source)
            else:
                # entity is refering an external object (absolute URI)
                if validate_url:

                    # specification says remote URI should always be
                    # accessible, but added this as optional to give the
                    # possibility of building off line (or behind a different
                    # landing page?). The fetching of the remote file/dataset
                    # itself (if enabled) is only done during ro-crate
                    # writing, but here we can fetch some properties of the
                    # remote file if possible
                    try:
                        response = urllib.request.urlopen(source)
                    except HTTPError as e:
                        # do something
                        print('Remote URI not accessible', e.code)
                    else:
                        properties.update({
                            'contentSize':
                            response.getheader('Content-Length'),
                            'encodingFormat':
                            response.getheader('Content-Type')
                        })
                if fetch_remote:
                    # the entity will be referencing a local file (so it has a
                    # local relative id), independently of the source being
                    # external
                    identifier = os.path.basename(source)
                else:
                    identifier = source
                # set url to the source. When creating through workflowhub
                # this is auto set to URL Workflow Hub page
                properties.update({'url': source})
        super(File, self).__init__(crate, identifier, properties)

    def _empty(self):
        val = {
            "@id": self.id,
            "@type": 'File'
        }
        return val

    def write(self, base_path):
        base_path = Path(base_path)
        out_file_path = base_path / self.id
        # check if its local or remote URI
        if isinstance(self.source, IOBase):
            out_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_file_path, 'w') as out_file:
                out_file.write(self.source.getvalue())
        elif is_url(str(self.source)) and self.fetch_remote:
            # Should we check that the resource hasn't changed? E.g., compare
            # response.getheader('Content-Length') to self._jsonld['contentSize'] or
            # response.getheader('Content-Type') to self._jsonld['encodingFormat']
            out_file_path.parent.mkdir(parents=True, exist_ok=True)
            with urllib.request.urlopen(self.source) as response, open(out_file_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
        elif os.path.isfile(self.source):
            out_file_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(self.source, out_file_path)

    def write_zip(self, zip_out):
        if self.id not in zip_out.namelist():
            zip_out.write(self.source, self.id)
