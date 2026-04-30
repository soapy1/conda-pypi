#!/usr/bin/env python
"""
Script to add the v3 key from tests/conda_local_channel/noarch/repodata.json
to tests/conda-forge-local/noarch/repodata.json
"""
import json
from pathlib import Path
import zstandard

# Define the paths
source_file = Path(__file__).parent.parent / "conda_local_channel" / "noarch" / "repodata.json"
target_file = Path(__file__).parent / "noarch" / "repodata.json"
target_zst_file = Path(__file__).parent / "noarch" / "repodata.json.zst"

print(f"Reading source file: {source_file}")
with open(source_file, "r") as f:
    source_data = json.load(f)

print(f"Reading target file: {target_file}")
with open(target_file, "r") as f:
    target_data = json.load(f)

# Extract v3 key from source
if "v3" in source_data:
    print("Found 'v3' key in source file")
    target_data["v3"] = source_data["v3"]
else:
    print("WARNING: 'v3' key not found in source file")

# Write back to target file
print(f"Writing updated data to: {target_file}")
with open(target_file, "w") as f:
    json.dump(target_data, f, indent=2)

print("✓ Successfully added v3 key to target file")

print("Generating repodata.json.zst")
new_repodata = json.dumps(target_data, sort_keys=True, indent=2)
ZSTD_COMPRESS_LEVEL = 16
ZSTD_COMPRESS_THREADS = -1
repodata_zst_content = zstandard.ZstdCompressor(
    level=ZSTD_COMPRESS_LEVEL, threads=ZSTD_COMPRESS_THREADS
).compress(new_repodata.encode("utf-8"))

with open(target_zst_file, "wb", encoding=None, newline=None) as f:
    f.write(repodata_zst_content)
