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

import atexit
import os
import tempfile
from contextlib import redirect_stdout
from galaxy2cwl import get_cwl_interface

from .file import File


class ComputationalWorkflow(File):
    """\
    A scientific workflow that was used (or can be used) to analyze or
    generate files in the RO-Crate.
    """
    TYPES = ["File", "SoftwareSourceCode", "ComputationalWorkflow"]

    def _empty(self):
        return {
            "@id": self.id,
            "@type": self.TYPES,
            "name": os.path.splitext(self.id)[0],
        }

    @property
    def programmingLanguage(self):
        return self["programmingLanguage"]

    @programmingLanguage.setter
    def programmingLanguage(self, programmingLanguage):
        self["programmingLanguage"] = programmingLanguage

    language = lang = programmingLanguage

    @property
    def subjectOf(self):
        return self["subjectOf"]

    @subjectOf.setter
    def subjectOf(self, subjectOf):
        self["subjectOf"] = subjectOf


class Workflow(ComputationalWorkflow):

    TYPES = ["File", "SoftwareSourceCode", "Workflow"]


def galaxy_to_abstract_cwl(workflow_path, delete=True):
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".cwl") as f:
        with redirect_stdout(f):
            get_cwl_interface.main(['1', str(workflow_path)])
    if delete:
        atexit.register(os.unlink, f.name)
    return f.name
