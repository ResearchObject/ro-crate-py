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

import uuid
from collections.abc import MutableMapping

from dateutil.parser import isoparse
from .. import vocabs


class Entity(MutableMapping):

    def __init__(self, crate, identifier=None, properties=None):
        self.crate = crate
        if identifier:
            self.id = self.format_id(identifier)
        else:
            self.id = "#%s" % uuid.uuid4()
        if properties:
            empty = self._empty()
            empty.update(properties)
            self._jsonld = empty
        else:
            self._jsonld = self._empty()

    # Format the given ID with rules appropriate for this type.
    # For example, Dataset (directory) data entities SHOULD end with /
    def format_id(self, identifier):
        return str(identifier)

    def __repr__(self):
        return "<%s %s>" % (self.id, self.type)

    def properties(self):
        return self._jsonld

    def as_jsonld(self):
        return self._jsonld

    @property
    def _default_type(self):
        clsName = self.__class__.__name__
        if clsName in vocabs.RO_CRATE["@context"]:
            return clsName
        return "Thing"

    def canonical_id(self):
        return self.crate.resolve_id(self.id)

    def __hash__(self):
        return hash(self.canonical_id())

    def _empty(self):
        val = {
            "@id": self.id,
            "@type": self._default_type
        }
        return val

    def __getitem__(self, key):
        v = self._jsonld[key]
        if v is None or isinstance(v, str) or key.startswith("@"):
            return v
        values = v if isinstance(v, list) else [v]
        deref_values = [self.crate.dereference(_["@id"], _["@id"]) for _ in values]
        return deref_values if isinstance(v, list) else deref_values[0]

    def __setitem__(self, key: str, value):
        if key.startswith("@"):
            raise KeyError(f"cannot set '{key}'")
        values = value if isinstance(value, list) else [value]
        ref_values = [{"@id": _.id} if isinstance(_, Entity) else _ for _ in values]
        self._jsonld[key] = ref_values if isinstance(value, list) else ref_values[0]

    def __delitem__(self, key: str):
        if key.startswith("@"):
            raise KeyError(f"cannot delete '{key}'")
        del self._jsonld[key]

    def popitem(self):
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError

    def update(self):
        raise NotImplementedError

    def __iter__(self):
        return iter(self._jsonld)

    def __len__(self):
        return len(self._jsonld)

    def __contains__(self, key):
        return key in self._jsonld

    def __eq__(self, other):
        if not isinstance(other, Entity):
            return NotImplemented
        return self.id == other.id and self._jsonld == other._jsonld

    @property
    def type(self):
        return self._jsonld['@type']

    # @property
    # def types(self)-> List[str]:
        # return tuple(as_list(self.get("@type", "Thing")))

    @property
    def datePublished(self):
        d = self.get('datePublished')
        return d if not d else isoparse(d)

    @datePublished.setter
    def datePublished(self, value):
        try:
            value = value.isoformat()
        except AttributeError:
            pass
        self['datePublished'] = value

    def delete(self):
        self.crate.delete(self)
