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

from .contextentity import ContextEntity
from .creativework import CreativeWork


class SoftwareApplication(ContextEntity, CreativeWork):

    def _empty(self):
        return {
            "@id": self.id,
            "@type": 'SoftwareApplication'
        }

    @property
    def name(self):
        return self["name"]

    @name.setter
    def name(self, name):
        self["name"] = name

    @property
    def url(self):
        return self["url"]

    @url.setter
    def url(self, url):
        self["url"] = url

    @property
    def version(self):
        return self["version"]

    @version.setter
    def version(self, version):
        self["version"] = version


PLANEMO_ID = "https://w3id.org/ro/terms/test#PlanemoEngine"
PLANEMO_DEFAULT_VERSION = "0.74"


def planemo(crate):
    return SoftwareApplication(crate, identifier=PLANEMO_ID, properties={
        "name": "Planemo",
        "url": {
            "@id": "https://github.com/galaxyproject/planemo"
        }
    })


APP_MAP = {
    "planemo": planemo,
}


def get_app(crate, name):
    try:
        func = APP_MAP[name.lower()]
    except KeyError:
        raise ValueError(f"Unknown application: {name}")
    return func(crate)
