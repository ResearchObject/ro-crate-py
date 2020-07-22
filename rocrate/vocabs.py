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

import json
import pkg_resources

# FIXME: Avoid eager loading?
RO_CRATE = json.load(pkg_resources.resource_stream(__name__, "data/ro-crate.jsonld").decode('utf-8'))
SCHEMA = json.load(pkg_resources.resource_stream(__name__, "data/schema.jsonld").decode('utf-8'))
SCHEMA_MAP = dict( (e["@id"],e) for e in SCHEMA["@graph"])

def term_to_uri(name):
    # NOTE: Assumes RO-Crate's flat-style context
    return RO_CRATE["@context"][name]

def schema_doc(uri):
    ## NOTE: Ensure rdfs:comment still appears in newer schema.org downloads
    # TODO: Support terms outside schema.org?
    return SCHEMA_MAP[uri].get("rdfs:comment", "")
