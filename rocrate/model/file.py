#!/usr/bin/env python

# Copyright 2019-2024 The University of Manchester, UK
# Copyright 2020-2024 Vlaams Instituut voor Biotechnologie (VIB), BE
# Copyright 2020-2024 Barcelona Supercomputing Center (BSC), ES
# Copyright 2020-2024 Center for Advanced Studies, Research and Development in Sardinia (CRS4), IT
# Copyright 2022-2024 École Polytechnique Fédérale de Lausanne, CH
# Copyright 2024 Data Centre, SciLifeLab, SE
# Copyright 2024 National Institute of Informatics (NII), JP
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

from pathlib import Path
import requests
import shutil
import urllib.request
import warnings
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
            kw = {} if isinstance(self.source, BytesIO) else {'encoding': 'utf-8'}
            with open(out_file_path, mode, **kw) as out_file:
                content = self.source.getvalue()
                out_file.write(content)
                if self.record_size:
                    self._jsonld['contentSize'] = str(len(content))
        elif is_url(str(self.source)):
            if self.fetch_remote or self.validate_url:
                if self.validate_url:
                    if self.source.startswith("http"):
                        with requests.head(self.source) as response:
                            self._jsonld.update({
                                'contentSize': response.headers.get('Content-Length'),
                                'encodingFormat': response.headers.get('Content-Type')
                            })
                        if not self.fetch_remote:
                            date_published = response.headers.get("Last-Modified", iso_now())
                            self._jsonld['sdDatePublished'] = date_published
                if self.fetch_remote:
                    out_file_path.parent.mkdir(parents=True, exist_ok=True)
                    urllib.request.urlretrieve(self.source, out_file_path)
                    self._jsonld['contentUrl'] = str(self.source)
                    if self.record_size:
                        self._jsonld['contentSize'] = str(out_file_path.stat().st_size)
        elif self.source is None:
            # Allows to record a File entity whose @id does not exist, see #73
            warnings.warn(f"No source for {self.id}")
        else:
            out_file_path.parent.mkdir(parents=True, exist_ok=True)
            if not out_file_path.exists() or not out_file_path.samefile(self.source):
                shutil.copy(self.source, out_file_path)
            if self.record_size:
                self._jsonld['contentSize'] = str(out_file_path.stat().st_size)
