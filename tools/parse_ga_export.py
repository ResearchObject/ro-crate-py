import json
import os
import re

def ga_history_export(export_dir):
    fn_list = os.listdir(export_dir)

    export_metadata = {}
    for f in fn_list :
        export_dir_path = os.path.join(export_dir,f)
        if os.path.isfile(export_dir_path):
            with open(export_dir_path,"r") as fh:
                # create keys for metadata files, removes '.' and 'txt' from fn
                key = '_'.join(list(filter(None, re.split('\.|txt',f))))
                export_metadata[key] = json.loads(fh.read())


    return export_metadata