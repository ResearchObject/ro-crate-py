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

from dateutil.parser import isoparse
from .. import vocabs


_NOT_SPECIFIED = object()


class Entity(dict):

    def __init__(self, crate, identifier=None, properties=None):
        self.crate = crate
        if identifier:
            self.id = self.format_id(identifier)
        else:
            self.id = "#%s" % uuid.uuid4()
        if properties:
            empty = self._empty()
            empty.update(properties)
            super().__init__(empty)
        else:
            super().__init__(self._empty())

    def format_id(self, identifier):
        """\
        Format the given identifier with rules appropriate for this type.
        For instance, Dataset identifiers SHOULD end with '/'.
        """
        return str(identifier)

    def __repr__(self):
        return "<%s %s>" % (self.id, self.type)

    def properties(self):
        rval = {}
        for k, v in self.items():
            values = v if isinstance(v, list) else [v]
            ref_values = [{"@id": _.id} if isinstance(_, Entity) else _ for _ in values]
            rval[k] = ref_values if isinstance(v, list) else ref_values[0]
        return rval

    def as_jsonld(self):
        return self.properties()

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

    def __setitem__(self, key: str, value):
        if key.startswith("@"):
            raise KeyError(f"cannot set '{key}'")
        super().__setitem__(key, value)

    def __delitem__(self, key: str):
        if key.startswith("@"):
            raise KeyError(f"cannot delete '{key}'")
        super().__delitem__(key)

    def pop(self, key: str, default=_NOT_SPECIFIED):
        if key.startswith("@"):
            raise KeyError(f"cannot delete '{key}'")
        if default is _NOT_SPECIFIED:
            return super().pop(key)
        return super().pop(key, default)

    def popitem(self):
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError

    def __eq__(self, other):
        if not isinstance(other, Entity):
            return NotImplemented
        if self.id != other.id:
            return False
        return super().__eq__(other)

    @property
    def type(self):
        return self["@type"]

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
