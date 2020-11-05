import io
from rocrate.model.dataset import Dataset
from rocrate.rocrate import ROCrate
import zipfile


def test_file_writing(test_data_dir, tmpdir, helpers):
    crate = ROCrate()
    crate_name = 'Test crate'
    crate.name = crate_name
    creator_id = '001'
    creator_name = 'Lee Ritenour'
    new_person = crate.add_person(creator_id, {'name': creator_name})
    crate.creator = new_person

    sample_file_id = 'sample_file.txt'
    sample_file2_id = 'subdir/sample_file2.csv'
    test_dir_id = 'test_add_dir/'
    data_entity_ids = [sample_file_id, sample_file2_id, test_dir_id]
    file_subdir_id = 'sample_file_subdir.txt'

    sample_file = test_data_dir / sample_file_id
    file_returned = crate.add_file(sample_file)
    assert file_returned.id == sample_file_id
    file_returned_subdir = crate.add_file(sample_file, sample_file2_id)
    assert file_returned_subdir.id == sample_file2_id
    test_dir_path = test_data_dir / test_dir_id
    test_dir_entity = crate.add_directory(test_dir_path, test_dir_id)
    assert isinstance(test_dir_entity, Dataset)

    out_path = tmpdir / 'ro_crate_out'
    out_path.mkdir()
    crate.write_crate(out_path)

    metadata_path = out_path / helpers.METADATA_FILE_NAME
    assert metadata_path.exists()
    preview_path = out_path / helpers.PREVIEW_FILE_NAME
    assert preview_path.exists()
    file1 = out_path / sample_file_id
    file2 = out_path / sample_file2_id
    file_subdir = out_path / test_dir_id / file_subdir_id
    assert file1.exists()
    with open(sample_file) as f1, open(file1) as f2:
        sample_file_content = f1.read()
        assert sample_file_content == f2.read()
    assert file2.exists()
    with open(file2) as f:
        assert sample_file_content == f.read()
    assert file_subdir.exists()
    with open(test_dir_path / file_subdir_id) as f1, open(file_subdir) as f2:
        assert f1.read() == f2.read()

    json_entities = helpers.read_json_entities(out_path)
    helpers.check_crate(json_entities, data_entity_ids=data_entity_ids)
    root = json_entities["./"]
    assert root["name"] == crate_name
    assert "datePublished" in root
    formatted_creator_id = f"#{creator_id}"
    assert root["creator"] == {"@id": formatted_creator_id}
    assert formatted_creator_id in json_entities
    assert json_entities[formatted_creator_id]["name"] == creator_name
    assert helpers.PREVIEW_FILE_NAME in json_entities
    preview = json_entities[helpers.PREVIEW_FILE_NAME]
    assert preview["@type"] == "CreativeWork"
    assert preview["about"] == {"@id": "./"}


def test_file_stringio(tmpdir, helpers):
    crate = ROCrate()

    test_file_id = 'test_file.txt'
    file_content = 'This will be the content of the file'
    file_stringio = io.StringIO(file_content)
    file_returned = crate.add_file(file_stringio, test_file_id)
    assert file_returned.id == test_file_id

    out_path = tmpdir / 'ro_crate_out'
    out_path.mkdir()
    crate.write_crate(out_path)

    metadata_path = out_path / helpers.METADATA_FILE_NAME
    assert metadata_path.exists()
    preview_path = out_path / helpers.PREVIEW_FILE_NAME
    assert preview_path.exists()
    file1 = out_path / test_file_id
    assert file1.exists()
    with open(file1) as f:
        assert f.read() == file_content


def test_remote_uri(tmpdir, helpers):
    crate = ROCrate()
    url = ('https://raw.githubusercontent.com/ResearchObject/ro-crate-py/'
           'master/test/test-data/sample_file.txt')
    file_returned = crate.add_file(source=url, fetch_remote=True)
    assert file_returned.id == 'sample_file.txt'
    file_returned = crate.add_file(source=url, fetch_remote=False)
    assert file_returned.id == url
    out_path = tmpdir / 'ro_crate_out'
    out_path.mkdir()

    crate.write_crate(out_path)

    metadata_path = out_path / helpers.METADATA_FILE_NAME
    assert metadata_path.exists()

    file1 = out_path / 'sample_file.txt'
    assert file1.exists()


def test_write_zip(test_data_dir, tmpdir):
    crate = ROCrate()

    # dereference added files
    sample_file = test_data_dir / 'sample_file.txt'
    file_returned = crate.add_file(sample_file)
    assert file_returned.id == 'sample_file.txt'
    file_returned_subdir = crate.add_file(
        sample_file, 'subdir/sample_file2.csv'
    )
    assert file_returned_subdir.id == 'subdir/sample_file2.csv'
    test_dir_path = test_data_dir / 'test_add_dir'
    test_dir_entity = crate.add_directory(test_dir_path, 'test_add_dir')
    assert isinstance(test_dir_entity, Dataset)
    # write to zip
    zip_path = tmpdir / "crate.zip"
    crate.write_zip(zip_path)
    read_zip = zipfile.ZipFile(zip_path, mode='r')
    assert read_zip.getinfo('sample_file.txt').file_size == 12
    assert read_zip.getinfo('test_add_dir/sample_file_subdir.txt').file_size == 18
