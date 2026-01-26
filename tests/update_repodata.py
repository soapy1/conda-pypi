import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional


def pypi_to_repodata_whl_entry(pypi_info: Dict[str, Any], url_index: int = 0) -> Optional[Dict[str, Any]]:
    """
    Convert PyPI JSON endpoint data to a repodata.json packages.whl entry.
    
    Args:
        pypi_info: Dictionary containing the complete info section from PyPI JSON endpoint
        url_index: Index of the wheel URL to use (typically the first one is the wheel)
    
    Returns:
        Dictionary representing the entry for packages.whl, or None if wheel not found
    """
    # Find the wheel URL (bdist_wheel package type)
    wheel_url = None
    
    for url_entry in pypi_info.get("urls", []):
        if url_entry.get("packagetype") == "bdist_wheel":
            wheel_url = url_entry
            break
    
    if not wheel_url:
        return None
    
    # Build the repodata entry
    entry = {
        "url": wheel_url.get("url", ""),
        "sha256": wheel_url.get("digests", {}).get("sha256", ""),
        "size": wheel_url.get("size", 0),
    }
    
    return entry


def get_updated_repodata_entry(name: str, version: str):
    pypi_endpoint = f"https://pypi.org/pypi/{name}/{version}/json"
    pypi_data = requests.get(pypi_endpoint)
    return pypi_to_repodata_whl_entry(pypi_data.json())
    

if __name__ == "__main__":
    from pathlib import Path

    HERE = Path(__file__).parent
    wheel_repodata = HERE / "conda_local_channel/noarch/repodata.json"
    
    repodata = {}
    with open(wheel_repodata, "r", encoding='utf-8') as file:
        repodata = json.load(file)

        for name, data in repodata["packages.whl"].items():
            updated_data = get_updated_repodata_entry(data["name"], data["version"])
            data["url"] = updated_data["url"]
            data["sha256"] = updated_data["sha256"]
            data["size"] = updated_data["size"]
    
    with open(wheel_repodata, "w") as f:
        json.dump(repodata, f, indent=4)