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

from .data_entity import DataEntity
from ..utils import is_url


class FileOrDir(DataEntity):

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
            if is_url(str(source)):
                identifier = os.path.basename(source) if fetch_remote else source
            else:
                identifier = "./" if source == "./" else os.path.basename(source)
        super().__init__(crate, identifier, properties)
