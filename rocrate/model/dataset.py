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

import errno
import os
import warnings
from pathlib import Path
from typing import Generator
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

    def _write_from_url(self, base_path):
        if self.validate_url and not self.fetch_remote:
            with urlopen(self.source) as _:
                self._jsonld['sdDatePublished'] = iso_now()
        if self.fetch_remote:
            out_file_path, out_file = None, None
            for rel_path, chunk in self._stream_folder_from_url():
                path = base_path / rel_path
                if path != out_file_path:
                    if out_file:
                        out_file.close()
                    out_file_path = Path(path)
                    out_file_path.parent.mkdir(parents=True, exist_ok=True)
                    out_file = open(out_file_path, 'wb')
                out_file.write(chunk)
            if out_file:
                out_file.close()

    def _copy_folder(self, base_path):
        abs_out_path = base_path / self.id
        if self.source is None:
            abs_out_path.mkdir(parents=True, exist_ok=True)
        else:
            if not Path(self.source).exists():
                raise FileNotFoundError(
                    errno.ENOENT, os.strerror(errno.ENOENT), str(self.source)
                )
            abs_out_path.mkdir(parents=True, exist_ok=True)
            if not self.crate.source:
                self.crate._copy_unlisted(self.source, abs_out_path)

    def write(self, base_path):
        base_path = Path(base_path)
        if is_url(str(self.source)):
            self._write_from_url(base_path)
        else:
            self._copy_folder(base_path)

    def stream(self) -> Generator[tuple[str, bytes], None, None]:
        if is_url(str(self.source)):
            yield from self._stream_folder_from_url()
        else:
            yield from self._stream_folder_from_path()

    def _stream_folder_from_path(self) -> Generator[tuple[str, bytes], None, None]:
        if not Path(self.source).exists():
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), str(self.source)
            )
        if not self.crate.source:
            for root, _, files in os.walk(self.source):
                root = Path(root)
                for name in files:
                    source = root / name
                    dest = source.relative_to(self.source.parent)
                    with open(source, 'rb') as f:
                        yield dest, f.read()

    def _stream_folder_from_url(self) -> Generator[tuple[str, bytes], None, None]:
        if not self.fetch_remote:
            if self.validate_url:
                with urlopen(self.source) as _:
                    self._jsonld['sdDatePublished'] = iso_now()
        else:
            base = self.source.rstrip("/")
            for entry in self._jsonld.get("hasPart", []):
                try:
                    part = entry["@id"]
                    if is_url(part) or part.startswith("/"):
                        raise RuntimeError(f"'{self.source}': part '{part}' is not a relative path")
                    part_uri = f"{base}/{part}"
                    rel_out_path = Path(self.id) / part

                    with urlopen(part_uri) as response:
                        chunk_size = 8192
                        while chunk := response.read(chunk_size):
                            yield rel_out_path, chunk
                except KeyError:
                    warnings.warn(f"'hasPart' entry in {self.id} is missing '@id'. Skipping.")
