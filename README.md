[![Python package](https://github.com/ResearchObject/ro-crate-py/workflows/Python%20package/badge.svg)](https://github.com/ResearchObject/ro-crate-py/actions?query=workflow%3A%22Python+package%22) [![Upload Python Package](https://github.com/ResearchObject/ro-crate-py/workflows/Upload%20Python%20Package/badge.svg)](https://github.com/ResearchObject/ro-crate-py/actions?query=workflow%3A%22Upload+Python+Package%22) [![PyPI version](https://badge.fury.io/py/rocrate.svg)](https://pypi.org/project/rocrate/) [![DOI](https://zenodo.org/badge/216605684.svg)](https://zenodo.org/badge/latestdoi/216605684)


# ro-crate-py

Python library to create/parse [RO-Crate](https://w3id.org/ro/crate) (Research Object Crate) metadata.

Supports specification: [RO-Crate 1.1](https://w3id.org/ro/crate/1.1)

Status: **Alpha**

## Contribute

Source code: <https://github.com/researchobject/ro-crate-py>

Feel free to raise a pull request at <https://github.com/researchobject/ro-crate-py/pulls>
or an issue at <https://github.com/researchobject/ro-crate-py/issues>.

Submitted contributions are assumed to be covered by section 5 of the Apache License 2.0.

For development, you can build a [Docker](https://www.docker.com/) image with:

```
docker build -t ro-crate-py .
```

And then run it interactively with:

```
docker run --rm -it --name ro-crate-py ro-crate-py bash
```


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
crate.write_crate(out_path)
```


## License

 * © 2019-2020 The University of Manchester, UK 
 * © 2020 Vlaams Instituut voor Biotechnologie (VIB), BE 
 * © 2020 Barcelona Supercomputing Center (BSC), ES 
 * © 2020 Center for Advanced Studies, Research and Development in Sardinia (CRS4), IT

Licensed under the 
Apache License, version 2.0 <https://www.apache.org/licenses/LICENSE-2.0>, 
see the file `LICENSE.txt` for details.

## Cite as

[![DOI](https://zenodo.org/badge/216605684.svg)](https://zenodo.org/badge/latestdoi/216605684)

The above DOI corresponds to the latest versioned release as [published to Zenodo](https://zenodo.org/record/3956493), where you will find all earlier releases. 
To cite `ro-crate-py` independent of version, use <https://doi.org/10.5281/zenodo.3956493>, which will always redirect to the latest release.
