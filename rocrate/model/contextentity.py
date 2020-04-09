#!/usr/bin/env python

## Copyright 2019-2020 The University of Manchester, UK
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##     http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.

import warnings

from .. import vocabs
from ..utils import *

from .entity import Thing

class ContextEntity(object):

    def __init__(self, entity_constructor=None):
        self.entity_constructor = entity_constructor or Thing

    def getmany(self, instance):
        for json in as_list(instance.get(self.property)):
            # TODO: Support more advanced dispatching
            yield self.entity_constructor(json["@id"], instance._metadata)

    def setmany(self, instance, values):
        json = []
        for value in values:
            ## TODO: Check it has compatible @type?
            if value._metadata != instance._metadata:
                # Oh no, it might have different base URIs, 
                # will need to be added to @graph, reference
                # other objects we don't have etc.
                # TODO: Support setting entities from other RO-Crates
                raise ValueError("Adding entity from other RO-Crate not (yet) supported")
            json.append({"@id": value.id})
        instance[self.property] = flatten(json)

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        result = None
        for val in self.getmany(instance):
            if result is not None:
                warnings.warn("More than one value in %s.%s, returning first" % (self.owner, self.property))
                break
            result = val
        return result

    def __set__(self, instance, value):
        # TODO: Check if arrays are permitted
        self.setmany(instance, as_list(value))
        
    def __delete__(self, instance):
        ## TODO: Check if permitted to delete?
        instance[self.property] = [] # known property, empty in JSON

    def __set_name__(self, owner, name): # requires Py 3.6+
        if not owner.__doc__:
            _set_class_doc(owner)
        self.owner = owner
        self.property = name
        uri = vocabs.term_to_uri(name)
        doc = vocabs.schema_doc(uri)
        self.__doc__ = "Single contextual entity %s\n%s" % (uri,doc)
        # Register plural _s variant 
        # TODO: Register plural _s variants
        setattr(owner, name+"s", 
            property(self.getmany, self.setmany, 
                     doc="Multiple contextual entities %s\n%s" % (uri,doc)))
        # TODO: Register _ids variants?

def _set_class_doc(Class):
    # set the class documentation
    try:
        # FIXME: avoid this hack here!
        uri = vocabs.term_to_uri(Class.__name__)
        doc = vocabs.schema_doc(uri)
        Class.__doc__ = "Entity %s\n%s" % (uri,doc)
    except KeyError:
        pass ## Non-matching class name, ignore
