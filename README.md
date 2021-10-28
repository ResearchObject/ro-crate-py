[![Python package](https://github.com/ResearchObject/ro-crate-py/workflows/Python%20package/badge.svg)](https://github.com/ResearchObject/ro-crate-py/actions?query=workflow%3A%22Python+package%22) [![Upload Python Package](https://github.com/ResearchObject/ro-crate-py/workflows/Upload%20Python%20Package/badge.svg)](https://github.com/ResearchObject/ro-crate-py/actions?query=workflow%3A%22Upload+Python+Package%22) [![PyPI version](https://badge.fury.io/py/rocrate.svg)](https://pypi.org/project/rocrate/) [![DOI](https://zenodo.org/badge/216605684.svg)](https://zenodo.org/badge/latestdoi/216605684)


# ro-crate-py

Python library to create/parse [RO-Crate](https://w3id.org/ro/crate) (Research Object Crate) metadata.

Supports specification: [RO-Crate 1.1](https://w3id.org/ro/crate/1.1)

Status: **Alpha**


## Installing

You will need Python 3.6 or later (Recommended: 3.7).

This library is easiest to install using [pip](https://docs.python.org/3/installing/):

```
pip install rocrate
```

If you want to install manually from this code base, then try:

```
pip install .
```

..or if you use don't use `pip`:
```
python setup.py install
```

## General usage

### The RO-crate object

In general you will want to start by instantiating the `ROCrate` object. This can be a new one: 

```python
from rocrate.rocrate import ROCrate

crate = ROCrate() 
```

or an existing RO-Crate package can be loaded from a directory or zip file:
```python
crate = ROCrate('/path/to/crate/')
```

```python
crate = ROCrate('/path/to/crate/file.zip')
```

In addition, there is a set of higher level functions in the form of an interface to help users create some predefined types of crates. 
As an example here is the code to create a [workflow RO-Crate](https://about.workflowhub.eu/Workflow-RO-Crate/), containing a workflow template.
This is a good starting point if you want to wrap up a workflow template to register at [workflowhub.eu](https://about.workflowhub.eu/):


```python
from rocrate import rocrate_api

wf_path = "test/test-data/test_galaxy_wf.ga"
files_list = ["test/test-data/test_file_galaxy.txt"]

# Create base package
wf_crate = rocrate_api.make_workflow_rocrate(workflow_path=wf_path,wf_type="Galaxy",include_files=files_list)
```

Independently of the initialization method, once an instance of `ROCrate` is created it can be manipulated to extend the content and metadata.

### Data entities

[Data entities](https://www.researchobject.org/ro-crate/1.1/data-entities.html) can be added with:

```python
## adding a File entity:
sample_file = '/path/to/sample_file.txt'
file_entity = crate.add_file(sample_file)

# Adding a File entity with a reference to an external (absolute) URI
remote_file = crate.add_file('https://github.com/ResearchObject/ro-crate-py/blob/master/test/test-data/test_galaxy_wf.ga', fetch_remote = False)

# adding a Dataset
sample_dir = '/path/to/dir'
dataset_entity = crate.add_directory(sample_dir, 'relative/rocrate/path')
```

### Contextual entities

[Contextual entities](https://www.researchobject.org/ro-crate/1.1/contextual-entities.html) are used in an RO-Crate to adequately describe a Data Entity. The following example shows how to add the person contextual entity to the RO-Crate root:

```python
from rocrate.model.person import Person

# Add authors info
crate.add(Person(crate, '#joe', {'name': 'Joe Bloggs'}))

# wf_crate example
publisher = Person(crate, '001', {'name': 'Bert Verlinden'})
creator = Person(crate, '002', {'name': 'Lee Ritenour'})
wf_crate.add(publisher, creator)

# These contextual entities can be assigned to other metadata properties:

wf_crate.publisher = publisher
wf_crate.creator = [ creator, publisher ]

```

### Other metadata

Several metadata fields on root level are supported for the workflow RO-crate:

```
wf_crate.license = 'MIT'
wf_crate.isBasedOn = "https://climate.usegalaxy.eu/u/annefou/w/workflow-constructed-from-history-climate-101"
wf_crate.name = 'Climate 101'
wf_crate.keywords = ['GTN', 'climate']
wf_crate.image = "climate_101_workflow.svg"
wf_crate.description = "The tutorial for this workflow can be found on Galaxy Training Network"
wf_crate.CreativeWorkStatus = "Stable"
```

### Writing the RO-crate file

In order to write the crate object contents to a zip file package or a decompressed directory, there are 2 write methods that can be used:

```python
# Write to zip file
out_path = "/home/test_user/crate"
crate.write_zip(out_path)

# write crate to disk
out_path = "/home/test_user/crate_base"
crate.write(out_path)
```


## Command Line Interface

`ro-crate-py` includes a hierarchical command line interface: the `rocrate` tool. `rocrate` is the top-level command, while specific functionalities are provided via sub-commands. Currently, the tool allows to initialize a directory tree as an RO-Crate (`rocrate init`) and to modify the metadata of an existing RO-Crate (`rocrate add`).

```
$ rocrate --help
Usage: rocrate [OPTIONS] COMMAND [ARGS]...

Options:
  -c, --crate-dir PATH
  --help                Show this message and exit.

Commands:
  add
  init
```

Commands act on the current directory, unless the `-c` option is specified.

The `rocrate init` command explores a directory tree and generates an RO-Crate metadata file (`ro-crate-metadata.json`) listing all files and directories as `File` and `Dataset` entities, respectively. The metadata file is added (overwritten if present) to the directory at the top-level, turning it into an RO-Crate.

The `rocrate add` command allows to add workflows and other entity types (currently [testing-related metadata](https://github.com/crs4/life_monitor/wiki/Workflow-Testing-RO-Crate)) to an RO-Crate. The entity type is specified via another sub-command level:

```
# rocrate add --help
Usage: rocrate add [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  test-definition
  test-instance
  test-suite
  workflow
```

Note that data entities (e.g., workflows) must already be present in the directory tree: the effect of the command is to register them in the metadata file.

### Example

```
# From the ro-crate-py repository root
cd test/test-data/ro-crate-galaxy-sortchangecase
```

This directory is already an ro-crate. Delete the metadata file to get a plain directory tree:

```
rm ro-crate-metadata.json
```

Now the directory tree contains several files and directories, including a Galaxy workflow and a Planemo test file, but it's not an RO-Crate since there is no metadata file. Initialize the crate:

```
rocrate init
```

This creates an `ro-crate-metadata.json` file that lists files and directories rooted at the current directory. Note that the Galaxy workflow is listed as a plain `File`:

```json
        {
            "@id": "sort-and-change-case.ga",
            "@type": "File"
        }
```

To register the workflow as a `ComputationalWorkflow`:

```
rocrate add workflow -l galaxy sort-and-change-case.ga
```

Now the workflow has a type of `["File", "SoftwareSourceCode", "ComputationalWorkflow"]` and points to a `ComputerLanguage` entity that represents the Galaxy workflow language. Also, the workflow is listed as the crate's `mainEntity` (see https://about.workflowhub.eu/Workflow-RO-Crate).

To add [workflow testing metadata](https://github.com/crs4/life_monitor/wiki/Workflow-Testing-RO-Crate) to the crate:

```
rocrate add test-suite -i \#test1
rocrate add test-instance \#test1 http://example.com -r jobs -i \#test1_1
rocrate add test-definition \#test1 test/test1/sort-and-change-case-test.yml  -e planemo -v '>=0.70'
```


## License

 * Copyright 2019-2021 The University of Manchester, UK
 * Copyright 2021 Vlaams Instituut voor Biotechnologie (VIB), BE
 * Copyright 2021 Barcelona Supercomputing Center (BSC), ES
 * Copyright 2021 Center for Advanced Studies, Research and Development in Sardinia (CRS4), IT

Licensed under the 
Apache License, version 2.0 <https://www.apache.org/licenses/LICENSE-2.0>, 
see the file `LICENSE.txt` for details.

## Cite as

[![DOI](https://zenodo.org/badge/216605684.svg)](https://zenodo.org/badge/latestdoi/216605684)

The above DOI corresponds to the latest versioned release as [published to Zenodo](https://zenodo.org/record/3956493), where you will find all earlier releases. 
To cite `ro-crate-py` independent of version, use <https://doi.org/10.5281/zenodo.3956493>, which will always redirect to the latest release.
