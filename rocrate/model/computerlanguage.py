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

from .contextentity import ContextEntity


class ComputerLanguage(ContextEntity):

    def _empty(self):
        return {
            "@id": self.id,
            "@type": 'ComputerLanguage'
        }

    @property
    def name(self):
        return self.get("name")

    @name.setter
    def name(self, name):
        self["name"] = name

    @property
    def alternateName(self):
        return self.get("alternateName")

    @alternateName.setter
    def alternateName(self, alternateName):
        self["alternateName"] = alternateName

    @property
    def identifier(self):
        return self.get("identifier")

    @identifier.setter
    def identifier(self, identifier):
        self["identifier"] = identifier

    @property
    def url(self):
        return self.get("url")

    @url.setter
    def url(self, url):
        self["url"] = url

    # Not listed as a property in "https://schema.org/ComputerLanguage"
    @property
    def version(self):
        return self.get("version")

    @version.setter
    def version(self, version):
        self["version"] = version


# For workflow ro-crates. Note that
# https://about.workflowhub.eu/Workflow-RO-Crate/ does not specify versions.

CWL_DEFAULT_VERSION = "1.2"
# https://github.com/galaxyproject/gxformat2 has some info on gxformat2 versions
# version can probably be simply ignored for "native" *.ga workflows
GALAXY_DEFAULT_VERSION = "21.09"
KNIME_DEFAULT_VERSION = "4.5.0"
NEXTFLOW_DEFAULT_VERSION = "21.10"
SNAKEMAKE_DEFAULT_VERSION = "6.13"
COMPSS_DEFAULT_VERSION = "2.10"
AUTOSUBMIT_DEFAULT_VERSION = "3.14"


def cwl(crate, version=CWL_DEFAULT_VERSION):
    id_ = "https://w3id.org/workflowhub/workflow-ro-crate#cwl"
    return ComputerLanguage(crate, identifier=id_, properties={
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
    id_ = "https://w3id.org/workflowhub/workflow-ro-crate#galaxy"
    return ComputerLanguage(crate, identifier=id_, properties={
        "name": "Galaxy",
        "identifier": {
            "@id": "https://galaxyproject.org/"
        },
        "url": {
            "@id": "https://galaxyproject.org/"
        },
        "version": version
    })


def knime(crate, version=KNIME_DEFAULT_VERSION):
    id_ = "https://w3id.org/workflowhub/workflow-ro-crate#knime"
    return ComputerLanguage(crate, identifier=id_, properties={
        "name": "KNIME",
        "identifier": {
            "@id": "https://www.knime.com/"
        },
        "url": {
            "@id": "https://www.knime.com/"
        },
        "version": version
    })


def nextflow(crate, version=NEXTFLOW_DEFAULT_VERSION):
    id_ = "https://w3id.org/workflowhub/workflow-ro-crate#nextflow"
    return ComputerLanguage(crate, identifier=id_, properties={
        "name": "Nextflow",
        "identifier": {
            "@id": "https://www.nextflow.io/"
        },
        "url": {
            "@id": "https://www.nextflow.io/"
        },
        "version": version
    })


def snakemake(crate, version=SNAKEMAKE_DEFAULT_VERSION):
    id_ = "https://w3id.org/workflowhub/workflow-ro-crate#snakemake"
    return ComputerLanguage(crate, identifier=id_, properties={
        "name": "Snakemake",
        "identifier": {
            "@id": "https://doi.org/10.1093/bioinformatics/bts480"
        },
        "url": {
            "@id": "https://snakemake.readthedocs.io"
        },
        "version": version
    })


def compss(crate, version=COMPSS_DEFAULT_VERSION):
    return ComputerLanguage(crate, identifier="#compss", properties={
        "name": "COMPSs Programming Model",
        "alternateName": "COMPSs",
        "url": "http://compss.bsc.es/",
        "citation": "https://doi.org/10.1007/s10723-013-9272-5",
        "version": version
    })


def autosubmit(crate, version=AUTOSUBMIT_DEFAULT_VERSION):
    return ComputerLanguage(crate, identifier="#autosubmit", properties={
        "name": "Autosubmit",
        "alternateName": "AS",
        "url": "https://autosubmit.readthedocs.io/",
        "citation": "https://doi.org/10.1109/HPCSim.2016.7568429",
        "version": version
    })


LANG_MAP = {
    "cwl": cwl,
    "galaxy": galaxy,
    "knime": knime,
    "nextflow": nextflow,
    "snakemake": snakemake,
    "compss": compss,
    "autosubmit": autosubmit,
}


def get_lang(crate, name, version=None):
    try:
        func = LANG_MAP[name.lower()]
    except KeyError:
        raise ValueError(f"Unknown language: {name}")
    return func(crate, version=version) if version else func(crate)
