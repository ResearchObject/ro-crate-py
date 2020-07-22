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

from typing import Dict
from ..utils import *
import tempfile

from jinja2 import Template

from .file import File

"""
RO-Crate preview file

This object holds a preview of an RO Crate in HTML format_

.. _rocrate: https://w3id.org/ro/crate/1.0
"""
class Preview(File):
    def __init__(self, crate, source = None):
        super().__init__(crate, source, "ro-crate-preview.html", None)

    def _empty(self):
        # default properties of the metadata entry
        val = {
                    "@id": "ro-crate-preview.html",
                    "@type": "CreativeWork",
                    "about": {"@id": "./"}
                }
        return val

    def generate_html(self):
        info_dict = self.crate.get_info()
        # print(info_dict['name'])
        # print(info_dict['creator'])
        base_path = os.path.abspath(os.path.dirname(__file__))
        template = open(os.path.join(base_path,'..' ,'templates', 'preview_template.html.j2'))
        src = Template(template.read())
        template.close()
        out_html = src.render(crate=info_dict)
        return out_html
    
    # TODO:should take into account the case if a readed preview file. in this case there is a source of it:
    # no need to generate it, just copy the html and any files present in ro-crate-preview_files/ (if this dir exists)
    def write(self, dest_base):
        write_path = self.filepath(dest_base)
        out_html = self.generate_html()
        with open(write_path, 'w') as outfile:
            outfile.write(out_html)

    def write_zip(self, zip_out):
        write_path = self.filepath()
        out_html = self.generate_html()

        tmpfile = tempfile.NamedTemporaryFile(mode='w', delete=False)
        tmpfile_path = tmpfile.name
        tmpfile.write(out_html)
        tmpfile.close()
        zip_out.write(tmpfile_path, write_path)
        os.remove(tmpfile_path)
        


