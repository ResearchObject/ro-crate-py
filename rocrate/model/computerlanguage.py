# Copyright 2019-2023 The University of Manchester, UK
# Copyright 2020-2023 Vlaams Instituut voor Biotechnologie (VIB), BE
# Copyright 2020-2023 Barcelona Supercomputing Center (BSC), ES
# Copyright 2020-2023 Center for Advanced Studies, Research and Development in Sardinia (CRS4), IT
# Copyright 2022-2023 École Polytechnique Fédérale de Lausanne, CH
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


# See https://w3id.org/workflowhub/workflow-ro-crate/1.0

def cwl(crate):
    id_ = "https://w3id.org/workflowhub/workflow-ro-crate#cwl"
    return ComputerLanguage(crate, identifier=id_, properties={
        "name": "Common Workflow Language",
        "alternateName": "CWL",
        "identifier": {
            "@id": "https://w3id.org/cwl/"
        },
        "url": {
            "@id": "https://www.commonwl.org/"
        }
    })


def galaxy(crate):
    id_ = "https://w3id.org/workflowhub/workflow-ro-crate#galaxy"
    return ComputerLanguage(crate, identifier=id_, properties={
        "name": "Galaxy",
        "identifier": {
            "@id": "https://galaxyproject.org/"
        },
        "url": {
            "@id": "https://galaxyproject.org/"
        }
    })


def knime(crate):
    id_ = "https://w3id.org/workflowhub/workflow-ro-crate#knime"
    return ComputerLanguage(crate, identifier=id_, properties={
        "name": "KNIME",
        "identifier": {
            "@id": "https://www.knime.com/"
        },
        "url": {
            "@id": "https://www.knime.com/"
        }
    })


def nextflow(crate):
    id_ = "https://w3id.org/workflowhub/workflow-ro-crate#nextflow"
    return ComputerLanguage(crate, identifier=id_, properties={
        "name": "Nextflow",
        "identifier": {
            "@id": "https://www.nextflow.io/"
        },
        "url": {
            "@id": "https://www.nextflow.io/"
        }
    })


def snakemake(crate):
    id_ = "https://w3id.org/workflowhub/workflow-ro-crate#snakemake"
    return ComputerLanguage(crate, identifier=id_, properties={
        "name": "Snakemake",
        "identifier": {
            "@id": "https://doi.org/10.1093/bioinformatics/bts480"
        },
        "url": {
            "@id": "https://snakemake.readthedocs.io"
        }
    })


def compss(crate):
    return ComputerLanguage(crate, identifier="#compss", properties={
        "name": "COMPSs Programming Model",
        "alternateName": "COMPSs",
        "url": "http://compss.bsc.es/",
        "citation": "https://doi.org/10.1007/s10723-013-9272-5"
    })


def autosubmit(crate):
    return ComputerLanguage(crate, identifier="#autosubmit", properties={
        "name": "Autosubmit",
        "alternateName": "AS",
        "url": "https://autosubmit.readthedocs.io/",
        "citation": "https://doi.org/10.1109/HPCSim.2016.7568429"
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


def get_lang(crate, name):
    try:
        func = LANG_MAP[name.lower()]
    except KeyError:
        raise ValueError(f"Unknown language: {name}")
    return func(crate)
