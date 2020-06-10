import io
import json
import os
import tempfile
from contextlib import redirect_stdout

import rocrate.rocrate as roc
from galaxy2cwl import get_cwl_interface

# Exposed functions

def make_workflow_rocrate(workflow_path,wf_type,include_files=[],cwl=None,diagram=None):

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
    #print(wf_file.id)
    if wf_type != 'CWL':
        if cwl:
            #add cwl file to crate
            cwl_abstract = wf_crate.add_file(cwl)  # should add it in a special path within the crate?
        elif wf_type == 'Galaxy':
            #create cwl_abstract
            cwl_abstract_path = tempfile.NamedTemporaryFile()
            with open(cwl_abstract_path.name, 'w') as cwl_abstract_out:
                with redirect_stdout(cwl_abstract_out):
                    get_cwl_interface.main(['1',workflow_path])
            wf_file_entity = wf_crate.add_file(cwl_abstract_path.name, )
    return wf_crate


