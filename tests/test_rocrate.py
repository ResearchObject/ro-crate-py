#!/usr/bin/env python

## Copyright 2018 Stian Soiland-Reyes, The University of Manchester, UK
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

import unittest
import datetime
import time

import rocrate

"""Test minimal RO Crate"""
class ROCrateMinimal(unittest.TestCase):
    """Verify JSON-LD output"""
    def testJsonLd(self):
        ro = rocrate.Metadata()
        jsonld = ro.as_jsonld()

        self.assertEqual("https://w3id.org/ro/crate/0.2/context",
            jsonld["@context"])        

        graph = jsonld["@graph"]
        
        # Ensure all entries have @id
        by_id = dict((e["@id"], e) for e in graph)

        # Check Core Metadata for the Root Data Entity
        # https://w3id.org/ro/crate/0.2#core-metadata-for-the-root-data-entity
        metadata = by_id["ro-crate-metadata.jsonld"]
        self.assertEqual("CreativeWork", metadata["@type"])
        self.assertEqual("ro-crate-metadata.jsonld", metadata["identifier"]) # WHY?
        self.assertEqual("./", metadata["about"]["@id"]) 

        root = by_id["./"]
        self.assertEquals("Dataset", root["@type"])
        self.assertTrue(root["datePublished"])
        self.assertNotEmpty(root["name"])
        self.assertNotEmpty(root["author"])

    def testProperties(self):
        before = datetime.datetime.now()
        time.sleep(0.5)
        metadata = rocrate.Metadata()
        time.sleep(0.5); 
        after = datetime.datetime.now()
        self.assertEquals("CreativeWork", metadata.type)
        self.assertEquals(("CreativeWork",), metadata.types)
        
        ro = metadata.about
        
        self.assertIsInstance(ro.datePublished, datetime.datetime)
        self.assertLess(before, ro.datePublished)
        self.assertGreater(after, ro.datePublished)
