"""
Utility for generating test-specific local channel repodata.

Run this script to regenerate ``tests/conda_local_channel/noarch/repodata.json``
from the packages listed in ``wheel_packages.txt``. Not intended for production use.
"""

import requests
from concurrent.futures import ThreadPoolExecutor

from conda_pypi.index import store_pypi_metadata
from conda_index.index import ChannelIndex, BaseCondaIndexCache


def cache_repodata_entry(cache: BaseCondaIndexCache, name: str, version: str):
    pypi_endpoint = f"https://pypi.org/pypi/{name}/{version}/json"
    pypi_data = requests.get(pypi_endpoint)
    if pypi_data.json() is None:
        raise Exception(f"unable to process {name} {version}")
    store_pypi_metadata(cache, pypi_data.json())


if __name__ == "__main__":
    from pathlib import Path

    HERE = Path(__file__).parent
    wheel_repodata = HERE / "noarch/repodata.json"

    repodata_packages = []
    requested_wheel_packages_file = HERE / "wheel_packages.txt"
    with open(requested_wheel_packages_file) as f:
        pkgs_data = f.read()
        for pkg in pkgs_data.splitlines():
            repodata_packages.append(tuple(pkg.split("==")))

    channel_index = ChannelIndex(
        HERE,
        None,
        threads=1,
        debug=False,
        write_bz2=False,
        write_zst=True,
        write_run_exports=True,
        compact_json=True,
        write_current_repodata=False,
        repodata_v3=True,
        update_only=True,
    )
    cache = channel_index.cache_for_subdir("noarch")

    # Run in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=25) as executor:
        # Map each package to its repodata entry
        futures = {
            executor.submit(cache_repodata_entry, cache, pkg_tuple[0], pkg_tuple[1]): pkg_tuple
            for pkg_tuple in repodata_packages
        }

    channel_index.index(patch_generator=None)
