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
