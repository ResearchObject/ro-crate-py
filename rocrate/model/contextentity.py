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

from urllib.parse import urlparse
import warnings

from .. import vocabs
from ..utils import *

from .entity import Entity
from arcp import is_arcp_uri

"""
A property class that can be used during class declaration
to make getter/setter properties.

The class name under construction is assumed to be a valid class name
in schema.org as referenced from the RO-Crate JSON-LD context, 
and likewise the class properties defined using this 
are assumed to be valid schema.org properties.

The setters handle any Entity by picking up their @id instead
of nesting their objects.

Likewise the getter will construct the typed Entity subclass 
instead of returning only the identifiers.

The name of the property is provided by the class under construction, 
which will call our __set_name__.

The singular getter will always return the first value set (or None), 
while the plural versions of the getter return a generator that yields all values.

So for instance:

    class Dataset(Entity):
        author = ContextEntity(Person)

    dataset = Dataset()

will have both dataset.author that return Person instance,
and dataset.authors, which return generator of Person instances.

The corresponding plural setter supports any iterable (e.g. list):

    person1 = Person("#person1", metadata)
    person2 = Person("#person2", metadata)
    dataset.creators = [person1, person2]
"""
class ContextEntity(Entity):

    def __init__(self, crate, identifier, properties=None):
        super(ContextEntity, self).__init__(crate, identifier, properties)

    def format_id(self, identifier):
        if is_arcp_uri(identifier):
            return identifier
        else:
            # check if it's an absolute URL
            url = urlparse(identifier)
            if all([url.scheme, url.netloc, url.path]):
                return identifier
            elif identifier.startswith('#'):
                return identifier
            else:
                return '#' + identifier

    def getmany(self, instance):
        for json in as_list(instance.get(self.property)):
            # TODO: Support more advanced dispatching
            yield self.entity_constructor(json["@id"], instance._metadata)

    # def setmany(self, instance, values):
        # json = []
        # for value in values:
            # ## TODO: Check it has compatible @type?
            # if value._metadata != instance._metadata:
                # # Oh no, it might have different base URIs, 
                # # will need to be added to @graph, reference
                # # other objects we don't have etc.
                # # TODO: Support setting entities from other RO-Crates
                # raise ValueError("Adding entity from other RO-Crate not (yet) supported")
            # json.append({"@id": value.id})
        # instance[self.property] = flatten(json)

    # def __get__(self, instance, owner=None):
        # if instance is None:
            # return self
        # result = None
        # for val in self.getmany(instance):
            # if result is not None:
                # warnings.warn("More than one value in %s.%s, returning first" % (self.owner, self.property))
                # break
            # result = val
        # return result

    # def __set__(self, instance, value):
        # # TODO: Check if arrays are permitted
        # self.setmany(instance, as_list(value))

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
            property(self.getmany, # self.setmany, 
                     doc="Multiple contextual entities %s\n%s" % (uri,doc)))
        # TODO: Register _ids variants?

"""
Set class documentation from schema.org definitions
"""
def _set_class_doc(Class):
    # set the class documentation
    try:
        # FIXME: avoid this hack here!
        uri = vocabs.term_to_uri(Class.__name__)
        doc = vocabs.schema_doc(uri)
        Class.__doc__ = "Entity %s\n%s" % (uri,doc)
    except KeyError:
        pass ## Non-matching class name, ignore
