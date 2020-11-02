import pytest
import shutil
from pathlib import Path

from rocrate.rocrate import ROCrate, TEST_METADATA_BASENAME

_URL = ('https://raw.githubusercontent.com/ResearchObject/ro-crate-py/master/'
        'test/test-data/sample_file.txt')


@pytest.mark.parametrize("load_preview,from_zip", [(False, False), (True, False), (True, True)])
def test_crate_dir_loading(test_data_dir, tmpdir, helpers, load_preview, from_zip):
    # load crate
    crate_dir = test_data_dir / 'read_crate'
    if from_zip:
        zip_source = shutil.make_archive(tmpdir / "read_crate.crate", "zip", crate_dir)
        crate = ROCrate(zip_source, load_preview=load_preview)
    else:
        crate = ROCrate(crate_dir, load_preview=load_preview)

    # check loaded entities and properties
    root = crate.dereference('./')
    assert crate.root_dataset is root
    root_prop = root.properties()
    assert root_prop['@id'] == root.id
    assert root_prop['@id'] == './'
    assert root_prop['@type'] == 'Dataset'

    metadata = crate.dereference(helpers.METADATA_FILE_NAME)
    assert crate.metadata is metadata
    md_prop = metadata.properties()
    assert md_prop['@id'] == metadata.id
    assert md_prop['@id'] == helpers.METADATA_FILE_NAME
    assert md_prop['@type'] == 'CreativeWork'
    assert md_prop['about'] == {'@id': './'}
    # conformsTo is currently hardcoded in the Metadata class, not read from the crate
    assert md_prop['conformsTo'] == {'@id': 'https://w3id.org/ro/crate/1.1'}
    assert metadata.root is root

    preview = crate.dereference('ro-crate-preview.html')
    assert preview == crate.preview
    preview_prop = preview.properties()
    assert preview_prop['@id'] == 'ro-crate-preview.html'
    assert preview_prop['@id'] == preview.id
    assert preview_prop['@type'] == 'CreativeWork'
    assert preview_prop['about'] == {'@id': './'}
    if load_preview:
        assert Path(preview.source).name == 'ro-crate-preview.html'
    else:
        assert not preview.source

    main_wf = crate.dereference('test_galaxy_wf.ga')
    wf_prop = main_wf.properties()
    assert wf_prop['@id'] == 'test_galaxy_wf.ga'
    assert wf_prop['@id'] == main_wf.id
    assert set(wf_prop['@type']) == helpers.LEGACY_WORKFLOW_TYPES
    assert wf_prop['programmingLanguage'] == {'@id': 'https://galaxyproject.org'}
    assert wf_prop['subjectOf'] == {'@id': 'abstract_wf.cwl'}

    abs_wf = crate.dereference('abstract_wf.cwl')
    abs_wf_prop = abs_wf.properties()
    assert abs_wf_prop['@id'] == 'abstract_wf.cwl'
    assert abs_wf_prop['@id'] == abs_wf.id
    assert set(abs_wf_prop['@type']) == helpers.LEGACY_WORKFLOW_TYPES

    wf_author = crate.dereference('#joe')
    author_prop = wf_author.properties()
    assert author_prop['@id'] == '#joe'
    assert author_prop['@id'] == wf_author.id
    assert author_prop['@type'] == 'Person'
    assert author_prop['name'] == 'Joe Bloggs'

    test_file = crate.dereference('test_file_galaxy.txt')
    test_file_prop = test_file.properties()
    assert test_file_prop['@id'] == 'test_file_galaxy.txt'
    assert test_file_prop['@id'] == test_file.id

    remote_file = crate.dereference(_URL)
    remote_file_prop = remote_file.properties()
    assert remote_file_prop['@id'] == _URL
    assert remote_file_prop['@id'] == remote_file.id

    examples_dataset = crate.dereference('examples/')
    examples_dataset_prop = examples_dataset.properties()
    assert examples_dataset_prop['@id'] == 'examples/'
    assert examples_dataset_prop['@id'] == examples_dataset.id
    assert crate.examples_dir is examples_dataset

    test_dataset = crate.dereference('test/')
    test_dataset_prop = test_dataset.properties()
    assert test_dataset_prop['@id'] == 'test/'
    assert test_dataset_prop['@id'] == test_dataset.id
    assert crate.test_dir is test_dataset
    assert crate.test_metadata_path == Path("test") / TEST_METADATA_BASENAME

    # write the crate in a different directory
    out_path = tmpdir / 'crate_read_out'
    out_path.mkdir()
    crate.write_crate(out_path)

    metadata_path = out_path / helpers.METADATA_FILE_NAME
    assert metadata_path.exists()
    legacy_metadata_path = out_path / helpers.LEGACY_METADATA_FILE_NAME
    assert not legacy_metadata_path.exists()

    if load_preview:
        preview_out_path = out_path / 'ro-crate-preview.html'
        with open(preview_out_path, "rb") as f:
            preview_out_content = f.read()
        with open(preview.source, "rb") as f:
            preview_content = f.read()
        assert preview_out_content == preview_content
