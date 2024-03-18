[![Python package](https://github.com/ResearchObject/ro-crate-py/workflows/Python%20package/badge.svg)](https://github.com/ResearchObject/ro-crate-py/actions?query=workflow%3A%22Python+package%22) [![Upload Python Package](https://github.com/ResearchObject/ro-crate-py/workflows/Upload%20Python%20Package/badge.svg)](https://github.com/ResearchObject/ro-crate-py/actions?query=workflow%3A%22Upload+Python+Package%22) [![PyPI version](https://badge.fury.io/py/rocrate.svg)](https://pypi.org/project/rocrate/) [![DOI](https://zenodo.org/badge/216605684.svg)](https://zenodo.org/badge/latestdoi/216605684)

ro-crate-py is a Python library to create and consume [Research Object Crates](https://w3id.org/ro/crate). It currently supports the [RO-Crate 1.1](https://w3id.org/ro/crate/1.1) specification.


## Installation

ro-crate-py requires Python 3.7 or later. The easiest way to install is via [pip](https://docs.python.org/3/installing/):

```
pip install rocrate
```

To install manually from this code base (e.g., to try the latest development revision):

```
git clone https://github.com/ResearchObject/ro-crate-py
cd ro-crate-py
pip install .
```


## Usage

### Creating an RO-Crate

In its simplest form, an RO-Crate is a directory tree with an `ro-crate-metadata.json` file at the top level that contains metadata about the other files and directories, represented by [data entities](https://www.researchobject.org/ro-crate/1.1/data-entities.html). These metadata consist both of properties of the data entities themselves and of other, non-digital entities called [contextual entities](https://www.researchobject.org/ro-crate/1.1/contextual-entities.html) (representing, e.g., a person or an organization).

Suppose Alice and Bob worked on a research task together, which resulted in a manuscript written by both; additionally, Alice prepared a spreadsheet containing the experimental data, which Bob used to generate a diagram. Let's make an RO-Crate to package all this:

```python
from rocrate.rocrate import ROCrate

crate = ROCrate()
paper = crate.add_file("exp/paper.pdf", properties={
    "name": "manuscript",
    "encodingFormat": "application/pdf"
})
table = crate.add_file("exp/results.csv", properties={
    "name": "experimental data",
    "encodingFormat": "text/csv"
})
diagram = crate.add_file("exp/diagram.svg", dest_path="images/figure.svg", properties={
    "name": "bar chart",
    "encodingFormat": "image/svg+xml"
})
```

We've started by adding the data entities. Now we need contextual entities to represent Alice and Bob:

```python
from rocrate.model.person import Person

alice_id = "https://orcid.org/0000-0000-0000-0000"
bob_id = "https://orcid.org/0000-0000-0000-0001"
alice = crate.add(Person(crate, alice_id, properties={
    "name": "Alice Doe",
    "affiliation": "University of Flatland"
}))
bob = crate.add(Person(crate, bob_id, properties={
    "name": "Bob Doe",
    "affiliation": "University of Flatland"
}))
```

Next, we express authorship of the various files:

```python
paper["author"] = [alice, bob]
table["author"] = alice
diagram["author"] = bob
```

Finally, we serialize the crate to disk:

```python
crate.write("exp_crate")
```

Now the `exp_crate` directory should contain copies of the three files and an `ro-crate-metadata.json` file with a JSON-LD serialization of the entities and relationships we created, according to the RO-Crate profile. Note that we have chosen a different destination path for the diagram, while the other two files have been placed at the top level with their names unchanged (the default).

Some applications and services support RO-Crates stored as archives. To save the crate in zip format, use `write_zip`:

```python
crate.write_zip("exp_crate.zip")
```

You can also add whole directories. A directory in RO-Crate is represented by the `Dataset` entity:

```python
logs = crate.add_dataset("exp/logs")
```

Note that the above adds all files and directories contained in `"exp/logs"` recursively to the crate, but only the top-level `"exp/logs"` dataset itself is listed in the metadata file (there is no requirement to represent every file and folder in the JSON-LD). To also add files and directory recursively to the metadata, use `add_tree` (but note that it only works on local directory trees).


#### Appending elements to property values

What ro-crate-py entities actually store is their JSON representation:

```python
paper.properties()
```

```json
{
  "@id": "paper.pdf",
  "@type": "File",
  "name": "manuscript",
  "encodingFormat": "application/pdf",
  "author": [
    {"@id": "https://orcid.org/0000-0000-0000-0000"},
    {"@id": "https://orcid.org/0000-0000-0000-0001"},
  ]
}
```

When `paper["author"]` is accessed, a new list containing the `alice` and `bob` entities is generated on the fly. For this reason, calling `append` on `paper["author"]` won't actually modify the `paper` entity in any way. To add an author, use the `append_to` method instead:

```python
donald = crate.add(Person(crate, "https://en.wikipedia.org/wiki/Donald_Duck"))
paper.append_to("author", donald)
```

Note that `append_to` also works if the property to be updated is missing or has only one value:

```python
for n in "Mickey_Mouse", "Scrooge_McDuck":
    p = crate.add(Person(crate, f"https://en.wikipedia.org/wiki/{n}"))
    donald.append_to("follows", p)
```

#### Adding remote entities

Data entities can also be remote:

```python
input_data = crate.add_file("http://example.org/exp_data.zip")
```

By default the file won't be downloaded, and will be referenced by its URI in the serialized crate:

```json
{
  "@id": "http://example.org/exp_data.zip",
  "@type": "File"
},
```

If you add `fetch_remote=True` to the `add_file` call, however, the library (when `crate.write` is called) will try to download the file and include it in the output crate.

Another option that influences the behavior when dealing with remote entities is `validate_url`, also `False` by default: if it's set to `True`, when the crate is serialized, the library will try to open the URL to add / update metadata bits such as the content's length and format (but it won't try to download the file unless `fetch_remote` is also set).


#### Adding entities with an arbitrary type

An entity can be of any type listed in the [RO-Crate context](https://www.researchobject.org/ro-crate/1.1/context.jsonld). However, only a few of them have a counterpart (e.g., `File`) in the library's class hierarchy (either because they are very common or because they are associated with specific functionality that can be conveniently embedded in the class implementation). In other cases, you can explicitly pass the type via the `properties` argument:

```python
from rocrate.model.contextentity import ContextEntity

hackathon = crate.add(ContextEntity(crate, "#bh2021", properties={
    "@type": "Hackathon",
    "name": "Biohackathon 2021",
    "location": "Barcelona, Spain",
    "startDate": "2021-11-08",
    "endDate": "2021-11-12"
}))
```

Note that entities can have multiple types, e.g.:

```python
    "@type" = ["File", "SoftwareSourceCode"]
```

#### Modifying the crate from JSON-LD dictionaries

The `add_jsonld` method allows to add a contextual entity directly from a
JSON-LD dictionary containing at least the `@id` and `@type` keys:

```python
crate.add_jsonld({
    "@id": "https://orcid.org/0000-0000-0000-0000",
    "@type": "Person",
    "name": "Alice Doe"
})
```

Existing entities can be updated from JSON-LD dictionaries via `update_jsonld`:

```python
crate.update_jsonld({
    "@id": "https://orcid.org/0000-0000-0000-0000",
    "name": "Alice K. Doe"
})
```

There is also an `add_or_update_jsonld` method that adds the entity if it's
not already in the crate and updates it if it already exists (note that, when
updating, the `@type` key is ignored). This allows to "patch" an RO-Crate from
a JSON-LD file. For instance, suppose you have the following `patch.json` file:

```json
{
    "@graph": [
        {
            "@id": "./",
            "author": {"@id": "https://orcid.org/0000-0000-0000-0001"}
        },
        {
            "@id": "https://orcid.org/0000-0000-0000-0001",
            "@type": "Person",
            "name": "Bob Doe"
        }
    ]
}
```

Then the following sets Bob as the author of the crate according to the above
file:

```python
crate = ROCrate("temp-crate")
with open("patch.json") as f:
    json_data = json.load(f)
for d in json_data.get("@graph", []):
    crate.add_or_update_jsonld(d)
```

### Consuming an RO-Crate

An existing RO-Crate package can be loaded from a directory or zip file:

```python
crate = ROCrate('exp_crate')  # or ROCrate('exp_crate.zip')
for e in crate.get_entities():
    print(e.id, e.type)
```

```
ro-crate-metadata.json CreativeWork
./ Dataset
paper.pdf File
results.csv File
images/figure.svg File
https://orcid.org/0000-0000-0000-0000 Person
https://orcid.org/0000-0000-0000-0001 Person
```

The first two entities shown in the output are the [metadata file descriptor](https://www.researchobject.org/ro-crate/1.1/metadata.html) and the [root data entity](https://www.researchobject.org/ro-crate/1.1/root-data-entity.html), respectively. These are special entities managed by the `ROCrate` object, and are always present. The other entities are the ones we added in the [section on RO-Crate creation](#creating-an-ro-crate). You can access data entities with `crate.data_entities` and contextual entities with `crate.contextual_entities`. For instance:

```python
for e in crate.data_entities:
    author = e.get("author")
    if not author:
        continue
    elif isinstance(author, list):
        print(e.id, [p["name"] for p in author])
    else:
        print(e.id, repr(author["name"]))
```

```
paper.pdf ['Alice Doe', 'Bob Doe']
results.csv 'Alice Doe'
images/figure.svg 'Bob Doe'
```

You can fetch an entity by its `@id` as follows:

```python
article = crate.dereference("paper.pdf")
```


## Command Line Interface

`ro-crate-py` includes a hierarchical command line interface: the `rocrate` tool. `rocrate` is the top-level command, while specific functionalities are provided via sub-commands. Currently, the tool allows to initialize a directory tree as an RO-Crate (`rocrate init`) and to modify the metadata of an existing RO-Crate (`rocrate add`).

```console
$ rocrate --help
Usage: rocrate [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  add
  init
  write-zip
```

### Crate initialization

The `rocrate init` command explores a directory tree and generates an RO-Crate metadata file (`ro-crate-metadata.json`) listing all files and directories as `File` and `Dataset` entities, respectively.

```console
$ rocrate init --help
Usage: rocrate init [OPTIONS]

Options:
  --gen-preview
  -e, --exclude CSV
  -c, --crate-dir PATH
  --help                Show this message and exit.
```

The command acts on the current directory, unless the `-c` option is specified. The metadata file is added (overwritten if present) to the directory at the top level, turning it into an RO-Crate.

### Adding items to the crate

The `rocrate add` command allows to add file, datasets (directories), workflows and other entity types (currently [testing-related metadata](https://crs4.github.io/life_monitor/workflow_testing_ro_crate)) to an RO-Crate:

```console
$ rocrate add --help
Usage: rocrate add [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  dataset
  file
  test-definition
  test-instance
  test-suite
  workflow
```

Note that data entities (e.g., workflows) must already be present in the directory tree: the effect of the command is to register them in the metadata file.

### Example

```bash
# From the ro-crate-py repository root
cd test/test-data/ro-crate-galaxy-sortchangecase
```

This directory is already an RO-Crate. Delete the metadata file to get a plain directory tree:

```bash
rm ro-crate-metadata.json
```

Now the directory tree contains several files and directories, including a Galaxy workflow and a Planemo test file, but it's not an RO-Crate since there is no metadata file. Initialize the crate:

```bash
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

```bash
rocrate add workflow -l galaxy sort-and-change-case.ga
```

Now the workflow has a type of `["File", "SoftwareSourceCode", "ComputationalWorkflow"]` and points to a `ComputerLanguage` entity that represents the Galaxy workflow language. Also, the workflow is listed as the crate's `mainEntity` (see the [Workflow RO-Crate profile](https://w3id.org/workflowhub/workflow-ro-crate/1.0)).

To add [workflow testing metadata](https://crs4.github.io/life_monitor/workflow_testing_ro_crate) to the crate:

```bash
rocrate add test-suite -i test1
rocrate add test-instance test1 http://example.com -r jobs -i test1_1
rocrate add test-definition test1 test/test1/sort-and-change-case-test.yml -e planemo -v '>=0.70'
```

To add files or directories after crate initialization:

```bash
cp ../sample_file.txt .
rocrate add file sample_file.txt -P name=sample -P description="Sample file"
cp -r ../test_add_dir .
rocrate add dataset test_add_dir
```

The above example also shows how to set arbitrary properties for the entity with `-P`. This is supported by most `rocrate add` subcommands.

```console
$ rocrate add workflow --help
Usage: rocrate add workflow [OPTIONS] PATH

Options:
  -l, --language [cwl|galaxy|knime|nextflow|snakemake|compss|autosubmit]
  -c, --crate-dir PATH
  -P, --property KEY=VALUE
  --help                          Show this message and exit.
```


## License

 * Copyright 2019-2024 The University of Manchester, UK
 * Copyright 2020-2024 Vlaams Instituut voor Biotechnologie (VIB), BE
 * Copyright 2020-2024 Barcelona Supercomputing Center (BSC), ES
 * Copyright 2020-2024 Center for Advanced Studies, Research and Development in Sardinia (CRS4), IT
 * Copyright 2022-2024 École Polytechnique Fédérale de Lausanne, CH
 * Copyright 2024 Data Centre, SciLifeLab, SE

Licensed under the 
Apache License, version 2.0 <https://www.apache.org/licenses/LICENSE-2.0>, 
see the file `LICENSE.txt` for details.

## Cite as

[![DOI](https://zenodo.org/badge/216605684.svg)](https://zenodo.org/badge/latestdoi/216605684)

The above DOI corresponds to the latest versioned release as [published to Zenodo](https://zenodo.org/record/3956493), where you will find all earlier releases. 
To cite `ro-crate-py` independent of version, use <https://doi.org/10.5281/zenodo.3956493>, which will always redirect to the latest release.

You may also be interested in the paper [Packaging research artefacts with RO-Crate](https://doi.org/10.3233/DS-210053).
