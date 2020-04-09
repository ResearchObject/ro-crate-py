
# exposed functions


def make_workflow_rocrate(main_workflow,wf_type,incl_files=[],cwl_abstract=None,diagram=None):
    #returns a complete ROCrateWorkflow object
    wf_crate = ROCrateWorkflow(main_workflow)
    return wf_crate

