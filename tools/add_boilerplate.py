# Copyright 2019-2025 The University of Manchester, UK
# Copyright 2020-2025 Vlaams Instituut voor Biotechnologie (VIB), BE
# Copyright 2020-2025 Barcelona Supercomputing Center (BSC), ES
# Copyright 2020-2025 Center for Advanced Studies, Research and Development in Sardinia (CRS4), IT
# Copyright 2022-2025 École Polytechnique Fédérale de Lausanne, CH
# Copyright 2024-2025 Data Centre, SciLifeLab, SE
# Copyright 2024-2025 National Institute of Informatics (NII), JP
# Copyright 2025 Senckenberg Society for Nature Research (SGN), DE
# Copyright 2025 European Molecular Biology Laboratory (EMBL), Heidelberg, DE
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

"""\
Add or update Apache 2.0 boilerplate notice.
"""

import io
import datetime
import os
import re

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
TOP_DIR = os.path.dirname(THIS_DIR)
LICENSE = os.path.join(TOP_DIR, "LICENSE")

START_YEAR_MAP = {
    "The University of Manchester, UK": "2019",
    "Vlaams Instituut voor Biotechnologie (VIB), BE": "2020",
    "Barcelona Supercomputing Center (BSC), ES": "2020",
    "Center for Advanced Studies, Research and Development in Sardinia (CRS4), IT": "2020",
    "École Polytechnique Fédérale de Lausanne, CH": "2022",
    "Data Centre, SciLifeLab, SE": "2024",
    "National Institute of Informatics (NII), JP": "2024",
    "Senckenberg Society for Nature Research (SGN), DE": "2025",
    "European Molecular Biology Laboratory (EMBL), Heidelberg, DE": "2025",
}
THIS_YEAR = str(datetime.date.today().year)
BOILERPLATE_START = "Copyright [yyyy] [name of copyright owner]"
COPYRIGHT_PATTERN = re.compile(r"#\s*Copyright\s+(\d+)(-\d+)?\s+(.*)")
EXCLUDE_DIRS = {"build", "dist", "venv"}
EXCLUDE_FILES = {"_version.py"}


def copyright_lines():
    lines = []
    for owner, start_year in START_YEAR_MAP.items():
        span = start_year if start_year == THIS_YEAR else f"{start_year}-{THIS_YEAR}"
        lines.append(f"Copyright {span} {owner}")
    return lines


def get_boilerplate():
    with io.open(LICENSE, "rt") as f:
        license = f.read()
    template = license[license.find(BOILERPLATE_START):]
    return template.replace(BOILERPLATE_START, "\n".join(copyright_lines()))


def comment(text, char="#"):
    out_lines = []
    for line in text.splitlines():
        line = line.strip()
        out_lines.append(char if not line else f"{char} {line}")
    return "\n".join(out_lines) + "\n"


def _updated_stream(stream):
    updated = False
    for line in stream:
        if COPYRIGHT_PATTERN.match(line):
            if not updated:
                for l in copyright_lines():
                    yield f"# {l}\n"
                updated = True
        else:
            yield line


def add_boilerplate(fn):
    with io.open(fn, "rt") as f:
        text = f.read()
    if not text:
        return
    if COPYRIGHT_PATTERN.search(text):
        # update existing
        with io.open(fn, "wt") as f:
            for line in _updated_stream(text.splitlines(True)):
                f.write(line)
        return
    # add new
    if text.startswith("#!"):
        head, tail = text.split("\n", 1)
        if "python" not in head:
            return
        head += "\n\n"
    else:
        head, tail = "", text
    boilerplate = comment(get_boilerplate())
    if not tail.startswith("\n"):
        boilerplate += "\n"
    with io.open(fn, "wt") as f:
        f.write(f"{head}{boilerplate}{tail}")


def main():
    join = os.path.join
    for root, dirs, files in os.walk(TOP_DIR):
        dirs[:] = [_ for _ in dirs if not _.startswith(".") and _ not in EXCLUDE_DIRS]
        for name in files:
            if not name.endswith(".py"):
                continue
            if name in EXCLUDE_FILES:
                continue
            path = join(root, name)
            print(path)
            add_boilerplate(path)


if __name__ == "__main__":
    main()
