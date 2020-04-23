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

from .entity import Entity
from shutil import copy


class File(Entity):

    def __init__(self, source, dest_path = None , properties = None, metadata = None):
        #...process source

        #this first case was aimed at handling File objects but dont think its necessary, only allowing a path is ok.
        # if isinstance(source, io.IOBase):
            # # define destination path
            # if not dest_path:  #no name for path within the crate
                # dest = source.toString()
            # else:
                # dest = dest_path
            # #copy to dest by chunks
        if os.path.isfile(source):
            self.source = source
            if not dest_path:
                self.id = source
            else:
                self.id = dest_path
        else:
            print('The source is not a File not a correct path')
            return None

        super.__init__(self,metadata)
        if properties:
            # merge default and
            self._jsonld.update(properties)

    def _empty(self):
        val = {
            "@id": self.id,
            "@type": 'File'
        }
        return val

    def write(self, base_path):
        out_path = os.path.join(base_path, self.id)
        copy(self.source,out_path)
