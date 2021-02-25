# Copyright 2019-2021 The University of Manchester, UK
# Copyright 2020-2021 Vlaams Instituut voor Biotechnologie (VIB), BE
# Copyright 2020-2021 Barcelona Supercomputing Center (BSC), ES
# Copyright 2020-2021 Center for Advanced Studies, Research and Development in Sardinia (CRS4), IT
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

from .contextentity import ContextEntity


class TestInstance(ContextEntity):

    def _empty(self):
        return {
            "@id": self.id,
            "@type": 'TestInstance'
        }

    @property
    def _default_type(self):
        return "TestInstance"

    @property
    def name(self):
        return self["name"]

    @name.setter
    def name(self, name):
        self["name"] = name

    @property
    def resource(self):
        return self["resource"]

    @resource.setter
    def resource(self, resource):
        self["resource"] = resource

    @property
    def runsOn(self):
        return self["runsOn"]

    @runsOn.setter
    def runsOn(self, runsOn):
        self["runsOn"] = runsOn

    @property
    def url(self):
        return self["url"]

    @url.setter
    def url(self, url):
        self["url"] = url

    service = runsOn
