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

from .file import File


class TestDefinition(File):

    def _empty(self):
        return {
            "@id": self.id,
            "@type": ['File', 'TestDefinition']
        }

    @property
    def _default_type(self):
        return "TestDefinition"

    @property
    def engineVersion(self):
        return self.get("engineVersion")

    @engineVersion.setter
    def engineVersion(self, engineVersion):
        self["engineVersion"] = engineVersion

    @property
    def conformsTo(self):
        return self.get("conformsTo")

    @conformsTo.setter
    def conformsTo(self, conformsTo):
        self["conformsTo"] = conformsTo

    engine = conformsTo
