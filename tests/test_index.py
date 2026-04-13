import requests
from pathlib import Path

from conda_pypi.index import store_pypi_metadata
from conda_index.index import ChannelIndex
from conda_index.utils import CONDA_PACKAGE_EXTENSIONS


def test_store_pypi_metadata(tmp_path: Path):
    channel_index = ChannelIndex(
        tmp_path,
        "haswheels",  # channel name if different than last segment of tmp_path
        repodata_v3=True,
        update_only=True,
        save_fs_state=False,
        write_current_repodata=False,
        cache_kwargs={"package_extensions": CONDA_PACKAGE_EXTENSIONS + (".whl",)},
    )
    cache = channel_index.cache_for_subdir("noarch")

    pypi_endpoint = "https://pypi.org/pypi/fastapi/0.116.1/json"
    pypi_data = requests.get(pypi_endpoint)
    store_pypi_metadata(cache, pypi_data.json())

    # packages from database
    packages = cache.indexed_packages()

    assert len(packages.packages_whl) == 1
    assert "fastapi" in [pkg.get("name") for pkg in packages.packages_whl.values()]
