# Copyright 2019-2026 The University of Manchester, UK
# Copyright 2020-2026 Vlaams Instituut voor Biotechnologie (VIB), BE
# Copyright 2020-2026 Barcelona Supercomputing Center (BSC), ES
# Copyright 2020-2026 Center for Advanced Studies, Research and Development in Sardinia (CRS4), IT
# Copyright 2022-2026 École Polytechnique Fédérale de Lausanne, CH
# Copyright 2024-2026 Data Centre, SciLifeLab, SE
# Copyright 2024-2026 National Institute of Informatics (NII), JP
# Copyright 2025-2026 Senckenberg Society for Nature Research (SGN), DE
# Copyright 2025-2026 European Molecular Biology Laboratory (EMBL), Heidelberg, DE
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

"""
Streaming RO-Crates from a web server

This example demonstrates how to create an RO-Crate on-the-fly
and stream the result to the client.
By using `stream_zip`, the RO-Crate is not written to disk and remote
data is only fetched on the fly.

To run: `fastapi dev main.py`, then visit http://localhost:8000/crate
"""

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from rocrate.rocrate import ROCrate
from io import StringIO

app = FastAPI()


@app.get("/crate")
async def get():
    crate = ROCrate()

    # Add a remote file
    crate.add_file(
        "https://raw.githubusercontent.com/ResearchObject/ro-crate-py/refs/heads/master/test/test-data/sample_file.txt",
        fetch_remote=True
    )

    # Add a file containing a string to the crate
    crate.add_file(
        source=StringIO("Hello, World!"),
        dest_path="test-data/hello.txt"
    )

    # Stream crate to client as a zip file
    return StreamingResponse(
        crate.stream_zip(),
        media_type="application/rocrate+zip",
        headers={
            "Content-Disposition": "attachment; filename=crate.zip",
        }
    )
