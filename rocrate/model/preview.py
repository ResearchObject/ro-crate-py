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

import os

from string import Template
from typing import Dict
from ..utils import *

from .file import File

"""
RO-Crate preview file

This object holds a preview of an RO Crate in HTML format_

.. _rocrate: https://w3id.org/ro/crate/1.0
"""
class Preview(File):
    def __init__(self, crate):
        super().__init__(crate, None, "ro-crate-preview.html", None)

    def _empty(self):
        # default properties of the metadata entry
        val = {
                    "@id": "ro-crate-preview.html",
                    "@type": "CreativeWork",
                    "about": {"@id": "./"}
                }
        return val

    def generate_html(sef):
        info_dict = self.crate.get_info()
        base_path = path.abspath(path.dirname(__file__))
        template = open(os.path.join(base_path,'..' ,'templates', 'preview_template.html'))
        template = Template(template.read())
        out_html = src.substitute(info_dict)
        return out_html

    def write(self, dest_base):
        write_path = self.filepath()
        out_html = self.generate_html()
        with open(write_path, 'w') as outfile:
            outfile.write(out_html)

    def write_zip(self, zip_out):
        write_path = self.filepath()
        out_html = self.generate_html()
        tmpfile_path = tempfile.NamedTemporaryFile()
        tmpfile = open(tmpfile_path.name, 'w')
        tmpfile.write(out_html)
        tmpfile.close()
        zip_out.write(tmpfile_path.name,write_path)

