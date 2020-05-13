import rocrate.rocrate as roc
from galaxy2cwl import get_cwl_interface

# Exposed functions

def make_workflow_rocrate(workflow_path,wf_type,include_files=[],cwl=None,diagram=None):

    #returns a complete ROCrate object corresponding to a Workflow template file
    # wf_type: Galaxy, CWL , Nextflow..
    # cwl: CWL/CWL-Abstract representation of the workflow. If the 
    # diagram: an image/graphical workflow representation. 
    #         If a CWL/CWLAbstract file is provided then this is generated using cwltool

    wf_crate = roc.ROCrateWorkflow(workflow_path,wf_type)

    if wf_type != 'CWL':
        if cwl:
            #add cwl file to crate
            print('add cwl file')
        elif wf_type == 'Galaxy':
            #create cwl_abstract
            cwl_abstract = get_cwl_interface.main(['1',workflow_file])
            cwl_abstract_path = tempfile.TemporaryFile(mode="w")
            json.dump(cwl_abstract, cwl_abstract_path)
            # fix the dest_path of this
            self.add_file(cwl_abstract_path)
    return wf_crate


