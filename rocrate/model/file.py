#!/usr/bin/env python

# Copyright 2019-2022 The University of Manchester, UK
# Copyright 2020-2022 Vlaams Instituut voor Biotechnologie (VIB), BE
# Copyright 2020-2022 Barcelona Supercomputing Center (BSC), ES
# Copyright 2020-2022 Center for Advanced Studies, Research and Development in Sardinia (CRS4), IT
# Copyright 2022 École Polytechnique Fédérale de Lausanne, CH
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
from http.client import HTTPResponse
from io import BytesIO, StringIO

from .file_or_dir import FileOrDir
from ..utils import is_url, iso_now


class File(FileOrDir):

    def _empty(self):
        val = {
            "@id": self.id,
            "@type": 'File'
        }
        return val

    def write(self, base_path):
        out_file_path = Path(base_path) / self.id
        if isinstance(self.source, (BytesIO, StringIO)):
            out_file_path.parent.mkdir(parents=True, exist_ok=True)
            mode = 'w' + ('b' if isinstance(self.source, BytesIO) else 't')
            with open(out_file_path, mode) as out_file:
                out_file.write(self.source.getvalue())
        elif is_url(str(self.source)):
            if self.fetch_remote or self.validate_url:
                with urllib.request.urlopen(self.source) as response:
                    if self.validate_url:
                        if isinstance(response, HTTPResponse):
                            self._jsonld.update({
                                'contentSize': response.getheader('Content-Length'),
                                'encodingFormat': response.getheader('Content-Type')
                            })
                        if not self.fetch_remote:
                            self._jsonld['sdDatePublished'] = iso_now()
                    if self.fetch_remote:
                        out_file_path.parent.mkdir(parents=True, exist_ok=True)
                        urllib.request.urlretrieve(response.url, out_file_path)
        elif os.path.isfile(self.source):
            out_file_path.parent.mkdir(parents=True, exist_ok=True)
            if not out_file_path.exists() or not out_file_path.samefile(self.source):
                shutil.copy(self.source, out_file_path)
