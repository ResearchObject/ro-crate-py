#!/usr/bin/env python

## Copyright 2019 The University of Manchester, UK
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

"""
RO-Crate metadata file

This object holds the data of an RO Crate Metadata File rocrate_

.. _rocrate: https://w3id.org/ro/crate/0.2
"""
class Metadata(object):
    
    def as_jsonld(self):
        # Hard-coded for now!
        return {
            "@context": "https://w3id.org/ro/crate/0.2/context",
            "@graph": [
                {
                    "@id": "ro-crate-metadata.jsonld",
                    "@type": "CreativeWork",
                    "identifier": "ro-crate-metadata.jsonld",
                    "about": {"@id": "./"}
                },
                {
                    "@id": "./",
                    "@type": "Dataset"
                }
            ]
        }
    
