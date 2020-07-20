[![Python package](https://github.com/ResearchObject/ro-crate-py/workflows/Python%20package/badge.svg)](https://github.com/ResearchObject/ro-crate-py/actions?query=workflow%3A%22Python+package%22)

# ro-crate-py

Create/parse rocrate_ (Research Object Crate) metadata.

Note: **Under development**

## Contribute


Source code: <https://github.com/researchobject/ro-crate-py>

Feel free to raise a pull request at <https://github.com/researchobject/ro-crate-py/pulls>
or an issue at <https://github.com/researchobject/ro-crate-py/issues>.

Submitted contributions are assumed to be covered by section 5 of the Apache License 2.0.

## Installing

You will need Python 3.6 or later (Recommended: 3.7).

If you want to install manually from this code base, then try:
```
pip install .
```

..or if you use don't use `pip`:
```
python setup.py install
```

.. _rocrate: https://w3id.org/ro/crate
.. _pip: https://docs.python.org/3/installing/

## General usage
The package contains a 
The standard use case is by instantiating ROCrate class. This can be a new one: 
crate = ROCrate() 
or an existing RO-crate package can be load from a directory or zip file:
```python
crate = ROCrate('/path/to/crate/')
```

```python
crate = ROCrate('/path/to/crate/file.zip')
```

In addition, there is a set of higher level functions in the form of an interface to help users create some predefined types of crates. 
As an example here is the code to create a workflow RO-Crate, containing a workflow template.
This is a good starting point if you want to wrap up a workflow template to register at workflowhub.eu


```python
from rocrate import rocrate_api

wf_path = "test/test-data/test_galaxy_wf.ga"
files_list = ["test/test-data/test_file_galaxy.txt"]


# Create base package
wf_crate = rocrate_api.make_workflow_rocrate(workflow_path=wf_path,wf_type="Galaxy",include_files=files_list)

# Write to zip file
out_path = "/home/test_user/wf_crate"
wf_crate.write_zip(out_path)

```

Independently of the initialization method, once an instance of ROCrate is created it can be manipulated to extend the content and metadata.

Data entities can be added with:

```python
## adding a File entity:
sample_file = '/path/to/sample_file.txt'
file_entity = crate.add_file(sample_file)

# Adding a File entity with a reference to an external 
remote_file = crate.add_file('https://github.com/ResearchObject/ro-crate-py/blob/master/test/test-data/test_galaxy_wf.ga', fetch_remote = False)

# adding a Dataset
sample_dir = '/path/to/dir'
dataset_entity = crate.add_directory(sample_dir, 'relative/rocrate/path')
```

Contextual entities are used in a ro-crate to adequately describe a Data Entity. The following example shows how to add them to the RO-Crate root:
```python
# Add authors info
joe_metadata = {'name': 'Joe Bloggs'}
crate.add_person('#joe', joe_metadata)
```

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

© 2019 Stian Soiland-Reyes <http://orcid.org/0000-0001-9842-9718>, The University of Manchester, UK

Licensed under the 
Apache License, version 2.0 <https://www.apache.org/licenses/LICENSE-2.0>, 
see the file LICENSE.txt for details.
