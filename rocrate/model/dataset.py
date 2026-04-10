#!/usr/bin/env python

# Copyright 2019-2026 The University of Manchester, UK
# Copyright 2020-2026 Vlaams Instituut voor Biotechnologie (VIB), BE
# Copyright 2020-2026 Barcelona Supercomputing Center (BSC), ES
# Copyright 2020-2026 Center for Advanced Studies, Research and Development in Sardinia (CRS4), IT
# Copyright 2022-2026 École Polytechnique Fédérale de Lausanne, CH
# Copyright 2024-2026 Data Centre, SciLifeLab, SE
# Copyright 2024-2026 National Institute of Informatics (NII), JP
# Copyright 2025-2026 Senckenberg Society for Nature Research (SGN), DE
# Copyright 2025-2026 European Molecular Biology Laboratory (EMBL), Heidelberg, DE
# Copyright 2026 Spanish National Research Council (CSIC), ES
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
from urllib.request import urlopen
from urllib.parse import unquote

from .file_or_dir import FileOrDir
from ..utils import as_list, is_url, iso_now, Mode


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
        abs_out_path = base_path / unquote(self.id)
        if self.source is None:
            abs_out_path.mkdir(parents=True, exist_ok=True)
        else:
            path = self.source
            if not Path(path).exists():
                raise FileNotFoundError(
                    errno.ENOENT, os.strerror(errno.ENOENT), path
                )
            abs_out_path.mkdir(parents=True, exist_ok=True)
            if self.crate.mode == Mode.CREATE:
                self.crate._copy_unlisted(path, abs_out_path)

    def write(self, base_path):
        base_path = Path(base_path)
        if is_url(str(self.source)):
            self._write_from_url(base_path)
        else:
            self._copy_folder(base_path)

    def stream(self, chunk_size=8192):
        if self.source is None:
            return
        elif is_url(str(self.source)):
            yield from self._stream_folder_from_url(chunk_size)
        else:
            yield from self._stream_folder_from_path(chunk_size)

    def _stream_folder_from_path(self, chunk_size=8192):
        path = self.source
        if not Path(path).exists():
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), str(path)
            )
        if self.crate.mode == Mode.CREATE:
            for root, _, files in os.walk(path):
                root = Path(root)
                for name in files:
                    source = root / name
                    dest = Path(unquote(self.id)) / source.relative_to(path)
                    is_empty = True
                    with open(source, 'rb') as f:
                        while chunk := f.read(chunk_size):
                            is_empty = False
                            yield str(dest), chunk

                    # yield once for an empty file
                    if is_empty:
                        yield str(dest), b""

    def _stream_folder_from_url(self, chunk_size=8192):
        if not self.fetch_remote:
            if self.validate_url:
                with urlopen(self.source) as _:
                    self._jsonld['sdDatePublished'] = iso_now()
        else:
            if is_url(self.id):
                relative_dest_uri = self.get("localPath") or self.id
            else:
                relative_dest_uri = self.id
            if is_url(relative_dest_uri):
                if relative_dest_uri.startswith(self.crate.root_dataset.id):
                    relative_dest_uri = relative_dest_uri[len(self.crate.root_dataset.id):]
                else:
                    relative_dest_uri = relative_dest_uri.rsplit("/", 1)[-1]
            out_dir_path = Path(unquote(relative_dest_uri))

            for entry in self._jsonld.get("hasPart", []):
                try:
                    part = entry["@id"]
                    if not is_url(part):
                        raise RuntimeError(f"'{self.source}' is a URL, but part '{part}' is not a URL")
                    rel_out_path = out_dir_path / part.rsplit("/", 1)[-1]
                    if part_entity := self.crate.get(part):
                        if "Dataset" in as_list(part_entity.type):
                            continue
                        # override with file localPath if set
                        if "File" in as_list(part_entity.type):
                            if file_local_path := part_entity.get("localPath"):
                                rel_out_path = file_local_path
                    is_empty = True
                    with urlopen(part) as response:
                        while chunk := response.read(chunk_size):
                            is_empty = False
                            yield str(rel_out_path), chunk

                    # yield once for an empty file
                    if is_empty:
                        yield str(rel_out_path), b""
                except KeyError:
                    warnings.warn(f"'hasPart' entry in {self.id} is missing '@id'. Skipping.")
