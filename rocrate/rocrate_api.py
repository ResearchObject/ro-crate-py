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

import io
import json
import os
import tempfile
from contextlib import redirect_stdout

import rocrate.rocrate as roc

from rocrate.model import entity
from galaxy2cwl import get_cwl_interface

def make_workflow_rocrate(workflow_path,wf_type,include_files=[],fetch_remote=False,cwl=None,diagram=None):

    # Properties 
    # missing? 
    # input
    # output
    # programmingLanguage
    # url
    #version
    # sdPublisher - current set to the person that provided the metadata, decision to change to the Workflow Hub itself - Done

    # publisher - where it came came from, e.g. Galaxy,  github, or WF Hub if uploaded - Done

    # producer - to describe the Project or Team Done

    # creator - the creators/ authors Done

    # maintainer - new recommended property to describe the uploader + additional people with manage rights Done

    # funder - example of cordis reference - https://cordis.europa.eu/project/id/730976
    # https://schema.org/FundingScheme linked to funder
    # Examples at the bottom of https://schema.org/Grant - funding looks ideal but not currently legal
    # Is needed to fulfill the OpenAire “Funding Reference” property

    # datePublished - becomes an optional property, and we use the date a DOI was minted (this property is needed for dataCite) Done

    # creativeWorkStatus - Maturity level, to be added to BioSchemas Done

    # Identifier - can be DOI if this function is enabled in WorkflowHub Done

    #returns a complete ROCrate object corresponding to a Workflow template file
    # wf_type: Galaxy, CWL , Nextflow..
    # cwl: CWL/CWL-Abstract representation of the workflow. If the
    # diagram: an image/graphical workflow representation.
    #         If a CWL/CWLAbstract file is provided then this is generated using cwltool
    #abs_path = os.path.abspath(workflow_path)
    wf_crate = roc.ROCrate()
    # add main workflow file
    file_name = os.path.basename(workflow_path)
    wf_file = wf_crate.add_file(workflow_path,file_name)  # should I add it in a special path within the crate?
    wf_crate.set_main_entity(wf_file)
    if wf_type == 'CWL':
            programming_language_entity = entity.Entity(wf_crate,'https://www.commonwl.org/v1.1/', properties={"@type": ["ComputerLanguage", "SoftwareApplication"], 'name':'CWL', 'url':'https://www.commonwl.org/v1.1/', 'version':'1.1'})
    if wf_type == 'Galaxy':
        if not cwl:
            #create cwl_abstract
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as cwl_abstract_out:
                with redirect_stdout(cwl_abstract_out):
                    get_cwl_interface.main(['1',workflow_path])
            wf_file = wf_crate.add_file(cwl_abstract_out.name, 'abstract_wf.cwl', properties={"@type": ["ComputerLanguage", "SoftwareApplication"]})
        programming_language_entity = entity.Entity(wf_crate,'https://galaxyproject.org/')

    ### SET PROPERTIES
    # A contextual entity representing a SoftwareApplication or ComputerLanguage MUST have a name, url and version,
    # which should indicate a known version the workflow/script was developed or tested with
    if programming_language_entity:
        wf_file['programmingLanguage'] = programming_language_entity

    # based on ro-crate specification. for workflows: @type is an array with at least File and Workflow as values.
    wf_type = wf_file['@type']
    if not isinstance(wf_type, list):
        wf_type = [wf_type]
    if 'Workflow' not in wf_type:
        wf_type.append('Workflow')
    if 'SoftwareSourceCode' not in wf_type:
        wf_type.append('SoftwareSourceCode')
    wf_file['@type'] = wf_type


    # if the source is a remote URL then add https://schema.org/codeRepository property to it
    # this can be checked by checking if the source is a URL instead of a local path
    if 'url' in wf_file.properties().keys():
        wf_file['codeRepository'] = wf_file['url']

    # add extra files    
    for file_entry in include_files:
        wf_crate.add_file(file_entry)
        
    return wf_crate

