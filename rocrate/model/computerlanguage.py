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


class ComputerLanguage(ContextEntity):

    def _empty(self):
        return {
            "@id": self.id,
            "@type": 'ComputerLanguage'
        }

    @property
    def name(self):
        return self["name"]

    @name.setter
    def name(self, name):
        self["name"] = name

    @property
    def alternateName(self):
        return self["alternateName"]

    @alternateName.setter
    def alternateName(self, alternateName):
        self["alternateName"] = alternateName

    @property
    def identifier(self):
        return self["identifier"]

    @identifier.setter
    def identifier(self, identifier):
        self["identifier"] = identifier

    @property
    def url(self):
        return self["url"]

    @url.setter
    def url(self, url):
        self["url"] = url

    # Not listed as a property in "https://schema.org/ComputerLanguage"
    @property
    def version(self):
        return self["version"]

    @version.setter
    def version(self, version):
        self["version"] = version


# For workflow ro-crates. Note that
# https://about.workflowhub.eu/Workflow-RO-Crate/ does not specify versions.

CWL_DEFAULT_VERSION = "1.2"
# https://github.com/galaxyproject/gxformat2 has some info on gxformat2 versions
# version can probably be simply ignored for "native" *.ga workflows
GALAXY_DEFAULT_VERSION = "v19_09"


def cwl(crate, version=CWL_DEFAULT_VERSION):
    return ComputerLanguage(crate, identifier="#cwl", properties={
        "name": "Common Workflow Language",
        "alternateName": "CWL",
        "identifier": {
            "@id": f"https://w3id.org/cwl/{version}/"
        },
        "url": {
            "@id": "https://www.commonwl.org/"
        },
        "version": version
    })


def galaxy(crate, version=GALAXY_DEFAULT_VERSION):
    return ComputerLanguage(crate, identifier="#galaxy", properties={
        "name": "Galaxy",
        "identifier": {
            "@id": "https://galaxyproject.org/"
        },
        "url": {
            "@id": "https://galaxyproject.org/"
        },
        "version": version
    })


LANG_MAP = {
    "cwl": cwl,
    "galaxy": galaxy,
}


def get_lang(crate, name, version=None):
    try:
        func = LANG_MAP[name.lower()]
    except KeyError:
        raise ValueError(f"Unknown language: {name}")
    return func(crate, version=version) if version else func(crate)
