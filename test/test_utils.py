# Copyright 2019-2023 The University of Manchester, UK
# Copyright 2020-2023 Vlaams Instituut voor Biotechnologie (VIB), BE
# Copyright 2020-2023 Barcelona Supercomputing Center (BSC), ES
# Copyright 2020-2023 Center for Advanced Studies, Research and Development in Sardinia (CRS4), IT
# Copyright 2022-2023 École Polytechnique Fédérale de Lausanne, CH
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

from rocrate.utils import subclasses, get_norm_value, is_url


class Pet:
    pass


class Cat(Pet):
    pass


class Dog(Pet):
    pass


class Beagle(Dog):
    pass


def test_subclasses():
    pet_subclasses = list(subclasses(Pet))
    assert set(pet_subclasses) == {Cat, Dog, Beagle}
    assert pet_subclasses.index(Beagle) < pet_subclasses.index(Dog)


def test_get_norm_value():
    for value in {"@id": "foo"}, "foo", ["foo"], [{"@id": "foo"}]:
        entity = {"@id": "#xyz", "name": value}
        assert get_norm_value(entity, "name") == ["foo"]
    for value in [{"@id": "foo"}, "bar"], ["foo", {"@id": "bar"}]:
        entity = {"@id": "#xyz", "name": value}
        assert get_norm_value(entity, "name") == ["foo", "bar"]
    assert get_norm_value({"@id": "#xyz"}, "name") == []
    with pytest.raises(ValueError):
        get_norm_value({"@id": "#xyz", "name": [["foo"]]}, "name")


def test_is_url():
    assert is_url("http://example.com/index.html")
    assert is_url("http://example.com/")
    assert is_url("http://example.com")
    assert not is_url("/etc/")
    assert not is_url("/etc")
    assert not is_url("/")
