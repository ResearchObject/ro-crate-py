import rocrate.rocrate as roc


# Exposed functions

def make_workflow_rocrate(workflow_path,wf_type,incl_files=[],cwl_abstract=None,diagram=None):
    #returns a complete ROCrate object
    wf_crate = roc.ROCrateWorkflow(main_workflow_path,wf_type)
    return wf_crate

