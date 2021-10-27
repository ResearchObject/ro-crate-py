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
                 validate_url=False, properties=None):
        if properties is None:
            properties = {}
        self.fetch_remote = fetch_remote
        self.validate_url = validate_url
        self.source = source
        if dest_path:
            dest_path = Path(dest_path)
            if dest_path.is_absolute():
                raise ValueError("if provided, dest_path must be relative")
            identifier = dest_path.as_posix()
        else:
            if not isinstance(source, (str, Path)):
                raise ValueError("dest_path must be provided if source is not a path or URI")
            if not is_url(str(source)):
                identifier = os.path.basename(source)
            else:
                if fetch_remote:
                    # the entity will be referencing a local file (so it has a
                    # local relative id), independently of the source being
                    # external
                    identifier = os.path.basename(source)
                else:
                    identifier = source
                properties.update({'url': source})
        super(File, self).__init__(crate, identifier, properties)

    def _empty(self):
        val = {
            "@id": self.id,
            "@type": 'File'
        }
        return val

    def write(self, base_path):
        out_file_path = Path(base_path) / self.id
        if isinstance(self.source, IOBase):
            out_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_file_path, 'w') as out_file:
                out_file.write(self.source.getvalue())
        elif is_url(str(self.source)) and (self.fetch_remote or self.validate_url):
            with urllib.request.urlopen(self.source) as response:
                if self.validate_url:
                    self._jsonld.update({
                        'contentSize': response.getheader('Content-Length'),
                        'encodingFormat': response.getheader('Content-Type')
                    })
                if self.fetch_remote:
                    out_file_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(out_file_path, 'wb') as out_file:
                        shutil.copyfileobj(response, out_file)
        elif os.path.isfile(self.source):
            out_file_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(self.source, out_file_path)
