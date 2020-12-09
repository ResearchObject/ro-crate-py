# Copyright 2019-2020 The University of Manchester, UK
# Copyright 2020 Vlaams Instituut voor Biotechnologie (VIB), BE
# Copyright 2020 Barcelona Supercomputing Center (BSC), ES
# Copyright 2020 Center for Advanced Studies, Research and Development in Sardinia (CRS4), IT
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from rocrate.rocrate import ROCrate
from rocrate.model.testservice import TestService
from rocrate.model.testinstance import TestInstance
from rocrate.model.testdefinition import TestDefinition
from rocrate.model.testsuite import TestSuite
from rocrate.model.softwareapplication import SoftwareApplication

# Tell pytest these are not test classes (so it doesn't try to collect them)
TestService.__test__ = False
TestInstance.__test__ = False
TestDefinition.__test__ = False
TestSuite.__test__ = False


def test_read(test_data_dir, helpers):
    crate_dir = test_data_dir / 'ro-crate-galaxy-sortchangecase'
    crate = ROCrate(crate_dir)

    wf_id = 'sort-and-change-case.ga'
    main_wf = crate.dereference(wf_id)
    wf_prop = main_wf.properties()
    assert wf_prop['@id'] == wf_id
    assert wf_prop['@id'] == main_wf.id
    assert set(wf_prop['@type']) == helpers.WORKFLOW_TYPES

    test_service = crate.dereference("#jenkins")
    assert test_service.id == "#jenkins"
    assert test_service.type == "TestService"
    assert test_service.name == "Jenkins"
    assert test_service.url == "https://www.jenkins.io"

    test_instance = crate.dereference("#test1_1")
    assert test_instance.id == "#test1_1"
    assert test_instance.type == "TestInstance"
    assert test_instance.name == "test1_1"
    assert test_instance.url == "http://example.org/jenkins"
    assert test_instance.resource == "job/tests/"
    assert test_instance.runsOn is test_service
    assert test_instance.service is test_service

    test_engine = crate.dereference("#planemo")
    assert test_engine.id == "#planemo"
    assert test_engine.type == "SoftwareApplication"
    assert test_engine.name == "Planemo"
    assert test_engine.url == "https://github.com/galaxyproject/planemo"
    assert test_engine.version == ">=0.70"

    def_id = "test/test1/sort-and-change-case-test.yml"
    test_definition = crate.dereference(def_id)
    assert test_definition.id == def_id
    assert set(test_definition.type) == {"File", "TestDefinition"}
    assert test_definition.conformsTo is test_engine
    assert test_definition.engine is test_engine

    test_suite = crate.dereference("#test1")
    assert test_suite.id == "#test1"
    assert test_suite.type == "TestSuite"
    assert test_suite.name == "test1"
    assert len(test_suite.instance) == 1
    assert test_suite.instance[0] is test_instance
    assert test_suite.definition is test_definition
    assert test_suite["mainEntity"] is main_wf

    test_dataset = crate.dereference('test/')
    test_dataset_prop = test_dataset.properties()
    assert test_dataset_prop['@id'] == 'test/'
    assert test_dataset_prop['@id'] == test_dataset.id
    assert crate.test_dir is test_dataset
    assert set(crate.test_dir["hasPart"]) == {test_suite}


def test_create():
    crate = ROCrate()

    test_service = TestService(crate, identifier="#jenkins")
    crate._add_context_entity(test_service)
    test_service.name = "Jenkins"
    test_service.url = {"@id": "https://www.jenkins.io"}
    assert test_service.name == "Jenkins"
    assert test_service.url == "https://www.jenkins.io"

    test_instance = TestInstance(crate, identifier="#foo_instance_1")
    crate._add_context_entity(test_instance)
    test_instance.name = "Foo Instance 1"
    test_instance.url = {"@id": "http://example.org/foo"}
    test_instance.resource = "job/foobar"
    test_instance.runsOn = test_service
    assert test_instance.name == "Foo Instance 1"
    assert test_instance.url == "http://example.org/foo"
    assert test_instance.resource == "job/foobar"
    assert test_instance.runsOn is test_service
    test_instance.runsOn = None
    test_instance.service = test_service
    assert test_instance.service is test_service

    test_engine = SoftwareApplication(crate, identifier="#planemo")
    crate._add_context_entity(test_engine)
    test_engine.name = "Planemo"
    test_engine.url = {"@id": "https://github.com/galaxyproject/planemo"}
    test_engine.version = ">=0.70"
    assert test_engine.name == "Planemo"
    assert test_engine.url == "https://github.com/galaxyproject/planemo"
    assert test_engine.version == ">=0.70"

    test_definition = TestDefinition(crate, dest_path="test/foo/bar.yml")
    crate._add_context_entity(test_definition)
    test_definition.conformsTo = test_service
    assert test_definition.conformsTo is test_service
    test_definition.conformsTo = None
    test_definition.engine = test_engine
    assert test_definition.engine is test_engine

    test_suite = TestSuite(crate, "#foosuite")
    crate._add_data_entity(test_suite)
    assert test_suite.id == "#foosuite"
    assert test_suite.type == "TestSuite"
    test_suite.name = "Foo Suite"
    test_suite.instance = [test_instance]
    test_suite.definition = test_definition
    assert test_suite.name == "Foo Suite"
    assert len(test_suite.instance) == 1
    assert test_suite.instance[0] is test_instance
    assert test_suite.definition is test_definition
