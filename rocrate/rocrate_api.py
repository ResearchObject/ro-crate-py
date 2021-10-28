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

from pathlib import Path

import rocrate.rocrate as roc


def make_workflow_rocrate(workflow_path, wf_type, include_files=[],
                          fetch_remote=False, cwl=None, diagram=None):

    # Properties
    # missing?
    # input
    # output
    # programmingLanguage
    # url
    # version
    # sdPublisher - current set to the person that provided the metadata,
    #   decision to change to the Workflow Hub itself - Done
    # publisher - where it came came from, e.g. Galaxy,  github, or WF Hub
    #   if uploaded - Done
    # producer - to describe the Project or Team - Done
    # creator - the creators / authors - Done
    # maintainer - new recommended property to describe the uploader +
    #  additional people with manage rights - Done
    # funder - example of cordis reference
    #   https://cordis.europa.eu/project/id/730976
    #   https://schema.org/FundingScheme linked to funder
    #   Examples at the bottom of https://schema.org/Grant - funding looks
    #   ideal but not currently legal
    #   Is needed to fulfill the OpenAire “Funding Reference” property
    # datePublished - becomes an optional property, and we use the date a
    #   DOI was minted (this property is needed for dataCite) - Done
    # creativeWorkStatus - Maturity level, to be added to BioSchemas - Done
    # Identifier - can be DOI if this function is enabled in WorkflowHub - Done

    # returns a complete ROCrate object corresponding to a Workflow template
    #   file
    # wf_type: Galaxy, CWL, Nextflow, ...
    # cwl: CWL/CWL-Abstract representation of the workflow.
    # diagram: an image/graphical workflow representation.
    # If a CWL/CWLAbstract file is provided, this is generated using cwltool

    wf_crate = roc.ROCrate()
    workflow_path = Path(workflow_path)
    wf_file = wf_crate.add_workflow(
        workflow_path, workflow_path.name, fetch_remote=fetch_remote,
        main=True, lang=wf_type, gen_cwl=(cwl is None)
    )

    # if the source is a remote URL then add https://schema.org/codeRepository
    # property to it this can be checked by checking if the source is a URL
    # instead of a local path
    if 'url' in wf_file.properties():
        wf_file['codeRepository'] = wf_file['url']

    # add extra files
    for file_entry in include_files:
        wf_crate.add_file(file_entry)

    return wf_crate
