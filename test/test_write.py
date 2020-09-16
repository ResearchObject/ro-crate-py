import io
from rocrate.model.dataset import Dataset
from rocrate.rocrate import ROCrate
import zipfile


def test_file_writing(test_data_dir, tmpdir):
    crate = ROCrate()
    # dereference added files
    sample_file = test_data_dir / 'sample_file.txt'
    file_returned = crate.add_file(sample_file)
    assert file_returned.id == 'sample_file.txt'
    file_returned_subdir = crate.add_file(sample_file, 'subdir/sample_file2.csv')
    assert file_returned_subdir.id == 'subdir/sample_file2.csv'
    test_dir_path = test_data_dir / 'test_add_dir'
    test_dir_entity = crate.add_directory(test_dir_path, 'test_add_dir')
    assert isinstance(test_dir_entity, Dataset)
    out_path = tmpdir / 'ro_crate_out'
    out_path.mkdir()

    crate.name = 'Test crate'

    new_person = crate.add_person('001', {'name': 'Lee Ritenour'})
    crate.creator = new_person

    crate.write_crate(out_path)

    metadata_path = out_path / 'ro-crate-metadata.jsonld'
    assert metadata_path.exists()

    preview_path = out_path / 'ro-crate-preview.html'
    assert preview_path.exists()
    file1 = out_path / 'sample_file.txt'
    file2 = out_path / 'subdir' / 'sample_file2.csv'
    file_subdir = out_path / 'test_add_dir' / 'sample_file_subdir.txt'
    assert file1.exists()
    assert file2.exists()
    assert file_subdir.exists()


def test_file_stringio(tmpdir):
    crate = ROCrate()
    # dereference added files
    file_content = 'This will be the content of the file'
    file_stringio = io.StringIO(file_content)
    file_returned = crate.add_file(file_stringio, 'test_file.txt')
    assert file_returned.id == 'test_file.txt'
    out_path = tmpdir / 'ro_crate_out'
    out_path.mkdir()

    crate.name = 'Test crate'
    crate.write_crate(out_path)

    metadata_path = out_path / 'ro-crate-metadata.jsonld'
    assert metadata_path.exists()

    preview_path = out_path / 'ro-crate-preview.html'
    assert preview_path.exists()
    file1 = out_path / 'test_file.txt'
    assert file1.exists()
    # assert file1.stat().st_size == 36
    stat = file1.stat()
    assert stat.st_size == 36


def test_remote_uri(tmpdir):
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

    metadata_path = out_path / 'ro-crate-metadata.jsonld'
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
