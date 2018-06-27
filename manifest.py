import unittest
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


class TestNewManifest(unittest.TestCase):
    def test_minimal_structure(self):
        expected = {"id": "0034-8910-rsp-48-2-0275", "versions": []}
        self.assertEqual(new("0034-8910-rsp-48-2-0275"), expected)

    def test_doc_ids_are_converted_to_str(self):
        expected = {"id": "275", "versions": []}
        self.assertEqual(new(275), expected)


class TestAddVersion(unittest.TestCase):
    def test_first_version(self):
        doc = {"id": "0034-8910-rsp-48-2-0275", "versions": []}
        expected = {
            "id": "0034-8910-rsp-48-2-0275",
            "versions": [
                {
                    "data": "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275.xml",
                    "assets": {"0034-8910-rsp-48-2-0275-gf01.gif": []},
                }
            ],
        }

        self.assertEqual(
            add_version(
                doc,
                "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275.xml",
                ["0034-8910-rsp-48-2-0275-gf01.gif"],
            ),
            expected,
        )

    def test_manifest_versions_are_immutable(self):
        doc = {"id": "0034-8910-rsp-48-2-0275", "versions": []}
        new_version = add_version(
            doc,
            "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275.xml",
            ["0034-8910-rsp-48-2-0275-gf01.gif"],
        )

        self.assertEqual(len(doc["versions"]), 0)
        self.assertEqual(len(new_version["versions"]), 1)

    def test_add_version_with_assets_mapping(self):
        doc = {"id": "0034-8910-rsp-48-2-0275", "versions": []}
        expected = {
            "id": "0034-8910-rsp-48-2-0275",
            "versions": [
                {
                    "data": "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275.xml",
                    "assets": {"0034-8910-rsp-48-2-0275-gf01.gif": [""]},
                }
            ],
        }

        self.assertEqual(
            add_version(
                doc,
                "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275.xml",
                {"0034-8910-rsp-48-2-0275-gf01.gif": ""},
            ),
            expected,
        )

    def test_add_version_with_assets_mapping_nonempty(self):
        doc = {"id": "0034-8910-rsp-48-2-0275", "versions": []}
        expected = {
            "id": "0034-8910-rsp-48-2-0275",
            "versions": [
                {
                    "data": "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275.xml",
                    "assets": {
                        "0034-8910-rsp-48-2-0275-gf01.gif": [
                            "/rawfiles/8e644999a8fa4/0034-8910-rsp-48-2-0275-gf01.gif"
                        ]
                    },
                }
            ],
        }

        self.assertEqual(
            add_version(
                doc,
                "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275.xml",
                {
                    "0034-8910-rsp-48-2-0275-gf01.gif": "/rawfiles/8e644999a8fa4/0034-8910-rsp-48-2-0275-gf01.gif"
                },
            ),
            expected,
        )

    def test_add_version_with_assets_mapping_nonempty(self):
        doc = {
            "id": "0034-8910-rsp-48-2-0275",
            "versions": [
                {
                    "data": "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275.xml",
                    "assets": {
                        "0034-8910-rsp-48-2-0275-gf01.gif": [
                            "/rawfiles/8e644999a8fa4/0034-8910-rsp-48-2-0275-gf01.gif"
                        ]
                    },
                }
            ],
        }
        expected = {
            "id": "0034-8910-rsp-48-2-0275",
            "versions": [
                {
                    "data": "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275.xml",
                    "assets": {
                        "0034-8910-rsp-48-2-0275-gf01.gif": [
                            "/rawfiles/8e644999a8fa4/0034-8910-rsp-48-2-0275-gf01.gif",
                            "/rawfiles/7a664999a8fb3/0034-8910-rsp-48-2-0275-gf01.gif",
                        ]
                    },
                }
            ],
        }

        self.assertEqual(
            add_asset_version(
                doc,
                "0034-8910-rsp-48-2-0275-gf01.gif",
                "/rawfiles/7a664999a8fb3/0034-8910-rsp-48-2-0275-gf01.gif",
            ),
            expected,
        )


if __name__ == "__main__":
    unittest.main()
