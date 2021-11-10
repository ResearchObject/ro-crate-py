# Copyright 2019-2021 The University of Manchester, UK
# Copyright 2020-2021 Vlaams Instituut voor Biotechnologie (VIB), BE
# Copyright 2020-2021 Barcelona Supercomputing Center (BSC), ES
# Copyright 2020-2021 Center for Advanced Studies, Research and Development in Sardinia (CRS4), IT
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from rocrate.rocrate import ROCrate


def test_file_rewriting(test_data_dir, helpers):
    # load crate
    crate_dir = test_data_dir / 'read_crate'
    crate = ROCrate(crate_dir)

    crate.write(crate_dir)

    metadata_path = crate_dir / helpers.METADATA_FILE_NAME
    assert metadata_path.exists()

    sample_file_id = "test_file_galaxy.txt"
    sample_file2_id = "test_galaxy_wf.ga"
    file1 = crate_dir / sample_file_id
    file2 = crate_dir / sample_file2_id
    assert file1.exists()
    assert file2.exists()
    