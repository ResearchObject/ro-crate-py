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
                if not value or len(value) == 0:
                    continue
                else:
                    if "input" in key:
                        self.attributes["inputs"].update(job_attrs[key])
                    if "output" in key:
                        self.attributes["outputs"].update(job_attrs[key])
                    if "params" in key:
                        tmp_dict = {}
                        for k, v in job_attrs[key].items():
                            if not v or len(v) == 0:
                                continue
                            try:
                                v = int(v)
                            except (TypeError, ValueError):
                                pass  # it was a string, not an int.
                            # print(k, v)
                            # print(type(v))

                            if "json" in k:
                                v = json.loads(v)
                            if isinstance(v, dict) or isinstance(v, list):
                                v = str(v)
                            tmp_dict[k] = v

                        self.attributes["parameters"].update(tmp_dict)


class GalaxyDataset(Dict):

    def __init__(self):
        """
        Initialize the GalaxyDataset object.
        """
        self.attributes = {}
        self.attributes["metadata"] = {}
        self.attributes["class"] = "File"

    def parse_ga_dataset_attrs(self, dataset_attrs):

        for key, value in dataset_attrs.items():
            if not isinstance(value, dict):
                self.attributes[key] = value
            else:
                if len(value) == 0:
                    pass
                else:
                    if "metadata" in key:
                        self.attributes["metadata"].update(dataset_attrs[key])
        # self.attributes["used_encoded_id"] = \
        #     next(
        #         iter(self.attributes["copied_from_history_dataset_association_id_chain"]),
        #         self.attributes["encoded_id"]
        #         )
