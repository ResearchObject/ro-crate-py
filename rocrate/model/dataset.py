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

from .data_entity import DataEntity


class Dataset(DataEntity):

    def __init__(self, crate, source=None, dest_path=None, properties=None):
        identifier = None
        self.source = source
        if not dest_path:
            identifier = Path(source).name
        else:
            identifier = Path(dest_path).as_posix()
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
        out_path = self.filepath(base_path)
        Path(out_path).mkdir(parents=True, exist_ok=True)
        if not self.crate.source_path and self.source and os.path.exists(self.source):
            self.crate._copy_unlisted(self.source, out_path)
