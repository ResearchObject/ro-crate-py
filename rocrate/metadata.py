# Copyright 2019-2026 The University of Manchester, UK
# Copyright 2020-2026 Vlaams Instituut voor Biotechnologie (VIB), BE
# Copyright 2020-2026 Barcelona Supercomputing Center (BSC), ES
# Copyright 2020-2026 Center for Advanced Studies, Research and Development in Sardinia (CRS4), IT
# Copyright 2022-2026 École Polytechnique Fédérale de Lausanne, CH
# Copyright 2024-2026 Data Centre, SciLifeLab, SE
# Copyright 2024-2026 National Institute of Informatics (NII), JP
# Copyright 2025-2026 Senckenberg Society for Nature Research (SGN), DE
# Copyright 2025-2026 European Molecular Biology Laboratory (EMBL), Heidelberg, DE
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

import json

from .model.metadata import BASENAME, LEGACY_BASENAME


def read_metadata(metadata_path):
    """\
    Read an RO-Crate metadata file.

    Return a tuple of two elements: the context; a dictionary that maps entity
    ids to the entities themselves.
    """
    if isinstance(metadata_path, dict):
        metadata = metadata_path
    else:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    try:
        context = metadata['@context']
        graph = metadata['@graph']
    except KeyError:
        raise ValueError(f"{metadata_path} must have a @context and a @graph")
    return context, {_["@id"]: _ for _ in graph}


def _check_descriptor(descriptor, entities):
    if descriptor["@type"] != "CreativeWork":
        raise ValueError('metadata descriptor must be of type "CreativeWork"')
    try:
        root = entities[descriptor["about"]["@id"]]
    except (KeyError, TypeError):
        raise ValueError("metadata descriptor does not reference the root entity")
    if ("Dataset" not in root["@type"] if isinstance(root["@type"], list) else root["@type"] != "Dataset"):
        raise ValueError('root entity must have "Dataset" among its types')
    return descriptor["@id"], root["@id"]


def find_root_entity_id(entities):
    """\
    Find metadata file descriptor and root data entity.

    Expects as input a dictionary that maps JSON entity IDs to the entities
    themselves (like the second element returned by read_metadata).

    Return a tuple of the corresponding identifiers (descriptor, root).
    If the entities are not found, raise KeyError. If they are found,
    but they don't satisfy the required constraints, raise ValueError.
    """
    descriptor = entities.get(BASENAME, entities.get(LEGACY_BASENAME))
    if not descriptor:
        raise KeyError("Metadata file descriptor not found")
    return _check_descriptor(descriptor, entities)
