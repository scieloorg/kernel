from typing import Union
from copy import deepcopy

__all__ = ["new", "add_version", "add_asset_version"]


def new(doc_id: str) -> dict:
    return {"id": str(doc_id), "versions": []}


def _new_version(data_uri: str, assets: Union[dict, list]) -> dict:
    _assets = {str(aid): [] for aid in assets}
    return {"data": data_uri, "assets": _assets}


def add_version(manifest: dict, data_uri: str, assets: Union[dict, list]) -> dict:
    _manifest = deepcopy(manifest)
    version = _new_version(data_uri, assets)
    for asset_id in assets:
        try:
            asset_uri = assets[asset_id]
        except TypeError:
            break
        else:
            version = _new_asset_version(version, asset_id, asset_uri)
    _manifest["versions"].append(version)
    return _manifest


def _new_asset_version(version: dict, asset_id: str, asset_uri: str) -> dict:
    _version = deepcopy(version)
    _version["assets"][asset_id].append(asset_uri)
    return _version


def add_asset_version(manifest: dict, asset_id: str, asset_uri: str) -> dict:
    _manifest = deepcopy(manifest)
    _manifest["versions"][-1] = _new_asset_version(
        _manifest["versions"][-1], asset_id, asset_uri
    )
    return _manifest
