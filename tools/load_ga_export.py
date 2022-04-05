import json
import os
import re
from typing import (
    Dict,
)


def load_ga_history_export(export_dir):
    fn_list = os.listdir(export_dir)
    export_metadata = {}
    for f in fn_list:
        export_dir_path = os.path.join(export_dir, f)
        if os.path.isfile(export_dir_path):
            with open(export_dir_path, "r") as fh:
                # create keys for metadata files, removes '.' and 'txt' from fn
                key = '_'.join(list(filter(None, re.split(r'\.|txt', f))))
                export_metadata[key] = json.loads(fh.read())
    return export_metadata


class GalaxyJob(Dict):
    def __init__(self):
        """
        Initialize the GalaxyJob object.
        """
        self.attributes = {}
        self.attributes["inputs"] = {}
        self.attributes["outputs"] = {}
        self.attributes["parameters"] = {}

    def parse_ga_jobs_attrs(self, job_attrs):

        for key, value in job_attrs.items():
            if not isinstance(value, dict):
                self.attributes[key] = value
            else:
                if len(value) == 0:
                    pass
                else:
                    if "input" in key:
                        self.attributes["inputs"].update(job_attrs[key])
                    if "output" in key:
                        self.attributes["outputs"].update(job_attrs[key])
                    if "params" in key:
                        self.attributes["parameters"].update(job_attrs[key])


class GalaxyDataset(Dict):

    def __init__(self, ga_export_dataset_attrs):
        """
        Initialize the GalaxyDataset object.
        """
        self.attributes = {}
        self.attributes["metadata"] = {}

    def parse_ga_dataset_attrs(self, job_attrs):

        for key, value in job_attrs.items():
            if not isinstance(value, dict):
                self.attributes[key] = value
            else:
                if len(value) == 0:
                    pass
                else:
                    if "metadata" in key:
                        self.attributes["metadata"].update(job_attrs[key])
