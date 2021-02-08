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

import pytest

from rocrate.rocrate import ROCrate
from rocrate.model.testservice import TestService
from rocrate.model.testinstance import TestInstance
from rocrate.model.testdefinition import TestDefinition
from rocrate.model.testsuite import TestSuite
from rocrate.model.softwareapplication import SoftwareApplication
from rocrate.model.computationalworkflow import ComputationalWorkflow

# Tell pytest these are not test classes (so it doesn't try to collect them)
TestService.__test__ = False
TestInstance.__test__ = False
TestDefinition.__test__ = False
TestSuite.__test__ = False


JENKINS = "https://w3id.org/ro/terms/test#JenkinsService"
PLANEMO = "https://w3id.org/ro/terms/test#PlanemoEngine"


def test_read(test_data_dir, helpers):
    crate_dir = test_data_dir / 'ro-crate-galaxy-sortchangecase'
    crate = ROCrate(crate_dir)

    wf_id = 'sort-and-change-case.ga'
    main_wf = crate.dereference(wf_id)
    wf_prop = main_wf.properties()
    assert wf_prop['@id'] == wf_id
    assert wf_prop['@id'] == main_wf.id
    assert set(wf_prop['@type']) == helpers.WORKFLOW_TYPES

    test_service = crate.dereference(JENKINS)
    assert test_service.id == JENKINS
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

    test_engine = crate.dereference(PLANEMO)
    assert test_engine.id == PLANEMO
    assert test_engine.type == "SoftwareApplication"
    assert test_engine.name == "Planemo"
    assert test_engine.url == "https://github.com/galaxyproject/planemo"

    def_id = "test/test1/sort-and-change-case-test.yml"
    test_definition = crate.dereference(def_id)
    assert test_definition.id == def_id
    assert set(test_definition.type) == {"File", "TestDefinition"}
    assert test_definition.conformsTo is test_engine
    assert test_definition.engine is test_engine
    assert test_definition.engineVersion == ">=0.70"

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
    assert set(crate.test_dir["about"]) == {test_suite}


def test_create():
    crate = ROCrate()

    test_service = TestService(crate, identifier=JENKINS)
    crate.add(test_service)
    test_service.name = "Jenkins"
    test_service.url = {"@id": "https://www.jenkins.io"}
    assert test_service.name == "Jenkins"
    assert test_service.url == "https://www.jenkins.io"

    test_instance = TestInstance(crate, identifier="#foo_instance_1")
    crate.add(test_instance)
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

    test_engine = SoftwareApplication(crate, identifier=PLANEMO)
    crate.add(test_engine)
    test_engine.name = "Planemo"
    test_engine.url = {"@id": "https://github.com/galaxyproject/planemo"}
    assert test_engine.name == "Planemo"
    assert test_engine.url == "https://github.com/galaxyproject/planemo"

    test_definition = TestDefinition(crate, dest_path="test/foo/bar.yml")
    crate.add(test_definition)
    test_definition.conformsTo = test_engine
    assert test_definition.conformsTo is test_engine
    test_definition.conformsTo = None
    test_definition.engine = test_engine
    test_definition.engineVersion = ">=0.70"
    assert test_definition.engine is test_engine
    assert test_definition.engineVersion == ">=0.70"

    test_suite = TestSuite(crate, "#foosuite")
    crate.add(test_suite)
    assert test_suite.id == "#foosuite"
    assert test_suite.type == "TestSuite"
    test_suite.name = "Foo Suite"
    test_suite.instance = [test_instance]
    test_suite.definition = test_definition
    assert test_suite.name == "Foo Suite"
    assert len(test_suite.instance) == 1
    assert test_suite.instance[0] is test_instance
    assert test_suite.definition is test_definition


def test_add_test_suite(test_data_dir, helpers):
    top_dir = test_data_dir / "ro-crate-galaxy-sortchangecase"
    wf_path = top_dir / "sort-and-change-case.ga"
    crate = ROCrate()
    with pytest.raises(ValueError):  # no main entity
        crate.add_test_suite()
    wf = crate.add(ComputationalWorkflow(crate, str(wf_path), wf_path.name))
    crate.mainEntity = wf
    suites = set()
    assert crate.test_dir is None
    s1 = crate.add_test_suite()
    assert crate.test_dir is not None
    assert s1["mainEntity"] is wf
    suites.add(s1)
    assert suites == set(crate.test_dir["about"])
    s2 = crate.add_test_suite(identifier="test1")
    assert s2["mainEntity"] is wf
    assert s2.id == "#test1"
    suites.add(s2)
    assert suites == set(crate.test_dir["about"])
    s3 = crate.add_test_suite(identifier="test2", name="Test 2")
    assert s3["mainEntity"] is wf
    assert s3.id == "#test2"
    assert s3.name == "Test 2"
    suites.add(s3)
    assert suites == set(crate.test_dir["about"])
    wf2_path = top_dir / "README.md"
    wf2 = crate.add(ComputationalWorkflow(crate, wf2_path, wf2_path.name))
    s4 = crate.add_test_suite(identifier="test3", name="Foo", main_entity=wf2)
    assert s4["mainEntity"] is wf2
    assert s4.id == "#test3"
    assert s4.name == "Foo"
    suites.add(s4)
    assert suites == set(crate.test_dir["about"])
