from typing import Union, Callable
from copy import deepcopy
from datetime import datetime

__all__ = ["new", "add_version", "add_asset_version"]


def utcnow():
    return str(datetime.utcnow().isoformat() + "Z")


def new(doc_id: str) -> dict:
    return {"id": str(doc_id), "versions": []}


def _new_version(
    data_uri: str, assets: Union[dict, list], now: Callable[[], str]
) -> dict:
    _assets = {str(aid): [] for aid in assets}
    return {"data": data_uri, "assets": _assets, "timestamp": now()}


def add_version(
    manifest: dict,
    data_uri: str,
    assets: Union[dict, list],
    now: Callable[[], str] = utcnow,
) -> dict:
    _manifest = deepcopy(manifest)
    version = _new_version(data_uri, assets, now=now)
    for asset_id in assets:
        try:
            asset_uri = assets[asset_id]
        except TypeError:
            break
        else:
            if asset_uri:
                version = _new_asset_version(version, asset_id, asset_uri, now=now)
    _manifest["versions"].append(version)
    return _manifest


def _new_asset_version(
    version: dict, asset_id: str, asset_uri: str, now: Callable[[], str] = utcnow
) -> dict:
    _version = deepcopy(version)
    _version["assets"][asset_id].append((now(), asset_uri))
    return _version


def add_asset_version(
    manifest: dict, asset_id: str, asset_uri: str, now: Callable[[], str] = utcnow
) -> dict:
    _manifest = deepcopy(manifest)
    _manifest["versions"][-1] = _new_asset_version(
        _manifest["versions"][-1], asset_id, asset_uri, now=now
    )
    return _manifest
