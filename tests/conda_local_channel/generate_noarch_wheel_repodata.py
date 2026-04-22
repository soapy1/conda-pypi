"""
Utility for generating test-specific local channel repodata.

Run this script to regenerate ``tests/conda_local_channel/noarch/repodata.json``
from the packages listed in ``wheel_packages.txt``. Not intended for production use.
"""

import logging

import requests
from conda_index.index import BaseCondaIndexCache, ChannelIndex
from conda_index.utils import CONDA_PACKAGE_EXTENSIONS

from conda_pypi.exceptions import UnableToConvertToRepodataEntry
from conda_pypi.index import store_pypi_metadata

log = logging.getLogger(__name__)


def cache_repodata_entry(cache: BaseCondaIndexCache, name: str, version: str):
    pypi_endpoint = f"https://pypi.org/pypi/{name}/{version}/json"
    pypi_data = requests.get(pypi_endpoint)
    if pypi_data.json() is None:
        log.error(f"unable to process {name} {version}, no data found at {pypi_endpoint}")
    try:
        store_pypi_metadata(cache, pypi_data.json())
    except UnableToConvertToRepodataEntry:
        log.error(
            f"unable to process {name} {version}, unable to convert pypi metadata to a repodata entry"
        )


def get_last_n_releases(name: str, n: int = 20) -> list[str]:
    "Returns a list of the last n versions of a package on pypi"
    pypi_endpoint = f"https://pypi.org/pypi/{name}/json"
    pypi_data = requests.get(pypi_endpoint)
    if pypi_data.json() is None:
        log.error(f"unable to get last {n} versions of {name} no data found at {pypi_endpoint}")
    versions = []
    for version, info in reversed(pypi_data.json().get("releases").items()):
        if len(info) > 0:
            versions.append(version)
        if len(versions) == n:
            break
    return versions

if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)

    from pathlib import Path

    HERE = Path(__file__).parent

    repodata_packages = []
    requested_wheel_packages_file = HERE / "wheel_packages.txt"
    with open(requested_wheel_packages_file) as f:
        pkgs_data = f.read()
        for pkg in pkgs_data.splitlines():
            if "==" in pkg:
                repodata_packages.append(tuple(pkg.split("==")))
            else:
                # if no specific version is selected, grab the last 20 versions of the package
                versions = get_last_n_releases(pkg, 20)
                for version in versions:
                    repodata_packages.append((pkg, version,))

    channel_index = ChannelIndex(
        HERE,
        None,
        threads=1,
        debug=False,
        write_bz2=False,
        write_zst=False,
        compact_json=False,
        write_current_repodata=False,
        repodata_v3=True,
        update_only=True,
        save_fs_state=False,
        cache_kwargs={"package_extensions": CONDA_PACKAGE_EXTENSIONS + (".whl",)},
    )
    cache = channel_index.cache_for_subdir("noarch")

    for pkg_tuple in repodata_packages:
        cache_repodata_entry(cache, pkg_tuple[0], pkg_tuple[1])

    channel_index.index(patch_generator=None)
