import datetime
import uuid

from rocrate.rocrate import ROCrate
from rocrate.model.file import File
from rocrate.model.person import Person


def test_dereferencing(test_data_dir, helpers):
    crate = ROCrate()

    # verify default entities
    root_dataset = crate.dereference('./')
    assert crate.root_dataset is root_dataset
    metadata_entity = crate.dereference(helpers.METADATA_FILE_NAME)
    assert crate.metadata is metadata_entity
    preview_entity = crate.dereference(helpers.PREVIEW_FILE_NAME)
    assert preview_entity is crate.preview

    # dereference added files
    sample_file = test_data_dir / 'sample_file.txt'
    file_returned = crate.add_file(sample_file)
    assert isinstance(file_returned, File)
    dereference_file = crate.dereference("sample_file.txt")
    assert file_returned is dereference_file


def test_dereferencing_equivalent_id(helpers):
    crate = ROCrate()

    root_dataset = crate.dereference('./')
    assert crate.root_dataset is root_dataset
    root_dataset = crate.dereference('')
    assert crate.root_dataset is root_dataset

    metadata_entity = crate.dereference(helpers.METADATA_FILE_NAME)
    assert crate.metadata is metadata_entity
    metadata_entity = crate.dereference(f'./{helpers.METADATA_FILE_NAME}')
    assert crate.metadata is metadata_entity


def test_contextual_entities():
    crate = ROCrate()
    new_person = crate.add_person('#joe', {'name': 'Joe Pesci'})
    person_dereference = crate.dereference('#joe')
    assert person_dereference is new_person
    assert person_dereference.type == 'Person'
    person_prop = person_dereference.properties()
    assert person_prop['@type'] == 'Person'
    assert person_prop['name'] == 'Joe Pesci'


def test_properties():
    crate = ROCrate()

    crate_name = "new crate"
    crate.name = crate_name
    assert crate.name == crate_name

    crate_description = "this is a new crate"
    crate.description = crate_description
    assert crate.description == crate_description

    crate_datePublished = datetime.datetime.now()
    crate.datePublished = crate_datePublished
    assert crate.datePublished == crate_datePublished

    new_person = crate.add_person('#001', {'name': 'Lee Ritenour'})
    crate.creator = new_person
    assert crate.creator is new_person
    assert isinstance(crate.creator, Person)
    assert crate.creator['name'] == 'Lee Ritenour'
    assert crate.creator.type == 'Person'

    new_person2 = crate.add_person('#002', {'name': 'Lee Ritenour'})
    crate.creator = [new_person, new_person2]
    assert isinstance(crate.creator, list)
    assert crate.creator[0] is new_person
    assert crate.creator[1] is new_person2


def test_uuid():
    crate = ROCrate()
    new_person = crate.add_person(name="No Identifier")
    jsonld = new_person.as_jsonld()
    assert "Person" == jsonld["@type"]
    assert jsonld["@id"].startswith("#")
    # Check it made a valid UUIDv4
    u = uuid.UUID(jsonld["@id"][1:])
    assert 4 == u.version
