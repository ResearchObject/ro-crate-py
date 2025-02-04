# Copyright 2019-2024 The University of Manchester, UK
# Copyright 2020-2024 Vlaams Instituut voor Biotechnologie (VIB), BE
# Copyright 2020-2024 Barcelona Supercomputing Center (BSC), ES
# Copyright 2020-2024 Center for Advanced Studies, Research and Development in Sardinia (CRS4), IT
# Copyright 2022-2024 École Polytechnique Fédérale de Lausanne, CH
# Copyright 2024 Data Centre, SciLifeLab, SE
# Copyright 2024 National Institute of Informatics (NII), JP
# Copyright 2025 Senckenberg Society for Nature Research (SGN), DE
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
from rocrate.model import ContextEntity, SoftwareApplication


def test_add_action(tmpdir):
    crate = ROCrate()
    instrument = SoftwareApplication(crate)
    crate.add(instrument)
    f_in_name = "f_in"
    f_in_path = tmpdir / f_in_name
    with open(f_in_path, "wt") as f:
        f.write("IN\n")
    f_in = crate.add_file(f_in_path)
    f_out_name = "f_out"
    f_out_path = tmpdir / f_out_name
    with open(f_out_path, "wt") as f:
        f.write("OUT\n")
    f_out = crate.add_file(f_out_path)
    param = crate.add(ContextEntity(crate, "#param", properties={
        "@type": "PropertyValue",
        "name": "param_name",
        "value": "param_value",
    }))
    create_action = crate.add_action(
        instrument,
        object=[f_in, param],
        result=[f_out],
        properties={
            "name": f"Run 1 of {instrument.id}",
            "startTime": "2018-10-25T15:46:35.211153",
            "endTime": "2018-10-25T15:46:43.020168",
        }
    )
    assert create_action.type == "CreateAction"
    create_actions = crate.get_by_type("CreateAction")
    assert crate.root_dataset.get("mentions") == create_actions
    assert create_actions == [create_action]
    assert create_action.get("instrument") is instrument
    assert create_action.get("object") == [f_in, param]
    assert create_action.get("result") == [f_out]
    assert create_action.get("name") == f"Run 1 of {instrument.id}"
    assert create_action.get("startTime") == "2018-10-25T15:46:35.211153"
    assert create_action.get("endTime") == "2018-10-25T15:46:43.020168"

    activate_action = crate.add_action(
        instrument,
        object=[f_out],
        properties={
            "@type": "ActivateAction",
            "name": f"Run 2 of {instrument.id}",
            "endTime": "2018-10-25T16:48:41.021563",
        }
    )
    assert activate_action.type == "ActivateAction"
    assert crate.root_dataset.get("mentions") == [create_action, activate_action]
    assert activate_action.get("instrument") is instrument
    assert activate_action.get("object") == [f_out]
    assert "result" not in activate_action
    assert activate_action.get("name") == f"Run 2 of {instrument.id}"
    assert activate_action.get("endTime") == "2018-10-25T16:48:41.021563"
