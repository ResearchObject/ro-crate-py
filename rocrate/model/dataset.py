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

import shutil
from pathlib import Path
from urllib.request import urlopen

from .file_or_dir import FileOrDir
from ..utils import is_url, iso_now


class Dataset(FileOrDir):

    def _empty(self):
        val = {
            "@id": self.id,
            "@type": 'Dataset'
        }
        return val

    # SHOULD end with /
    def format_id(self, identifier):
        return identifier.rstrip("/") + "/"

    def write(self, base_path):
        out_path = Path(base_path) / self.id
        if is_url(str(self.source)):
            if self.validate_url and not self.fetch_remote:
                with urlopen(self.source) as _:
                    self._jsonld['sdDatePublished'] = iso_now()
            if self.fetch_remote:
                self.__get_parts(out_path)
        else:
            out_path.mkdir(parents=True, exist_ok=True)
            if not self.crate.source and self.source and self.source.exists():
                self.crate._copy_unlisted(self.source, out_path)

    def __get_parts(self, out_path):
        out_path.mkdir(parents=True, exist_ok=True)
        base = self.source.rstrip("/")
        for entry in self._jsonld.get("hasPart", []):
            try:
                part = entry["@id"]
            except KeyError:
                continue
            if is_url(part) or part.startswith("/"):
                raise RuntimeError(f"'{self.source}': part '{part}' is not a relative path")
            part_uri = f"{base}/{part}"
            part_out_path = out_path / part
            with urlopen(part_uri) as r, open(part_out_path, 'wb') as f:
                shutil.copyfileobj(r, f)
