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

from pathlib import Path

from .data_entity import DataEntity


class Dataset(DataEntity):

    def __init__(self, crate, source=None, dest_path=None, properties=None):
        if not source and not dest_path:
            raise ValueError("dest_path must be provided if source is not")
        self.source = source if not source else Path(source)
        if dest_path:
            dest_path = Path(dest_path)
            if dest_path.is_absolute():
                raise ValueError("if provided, dest_path must be relative")
            identifier = dest_path.as_posix()
        else:
            identifier = self.source.name
        super().__init__(crate, identifier, properties)

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
        out_path.mkdir(parents=True, exist_ok=True)
        if not self.crate.source_path and self.source and self.source.exists():
            self.crate._copy_unlisted(self.source, out_path)
