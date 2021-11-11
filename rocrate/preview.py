#!/usr/bin/env python

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

import os

from jinja2 import Template


BASENAME = "ro-crate-preview.html"


def generate(crate):
    base_path = os.path.abspath(os.path.dirname(__file__))
    template = open(os.path.join(base_path, 'templates', 'preview_template.html.j2'))
    src = Template(template.read())

    def template_function(func):
        src.globals[func.__name__] = func
        return func

    @template_function
    def stringify(a):
        if type(a) is list:
            return ', '.join(a)
        elif type(a) is str:
            return a
        else:
            if a._jsonld and a._jsonld['name']:
                return a._jsonld['name']
            else:
                return a

    @template_function
    def is_object_list(a):
        if type(a) is list:
            for obj in a:
                if obj is not str:
                    return True
        else:
            return False

    template.close()
    context_entities = []
    data_entities = []
    for entity in crate.contextual_entities:
        context_entities.append(entity._jsonld)
    for entity in crate.data_entities:
        data_entities.append(entity._jsonld)
    return src.render(crate=crate, context=context_entities, data=data_entities)
