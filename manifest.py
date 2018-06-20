import unittest
from typing import Union


def new(docid: str) -> dict:
    return {"id": str(docid), "versions": []}


def _new_version(data_uri: str, assets: Union[dict, list]) -> dict:
    _assets = {str(aid): [] for aid in assets}
    for aid, alist in _assets.items():
        try:
            asset_uri = assets[aid]
        except TypeError:
            # assets não é um dict
            break
        else:
            if asset_uri:
                alist.append(assets[aid])
    return {"data": data_uri, "assets": _assets}


def add_version(manifest: dict, data_uri: str, assets: Union[dict, list]) -> dict:
    _manifest = manifest.copy()
    version = _new_version(data_uri, assets)
    _manifest["versions"].append(version)
    return _manifest


class TestNewManifest(unittest.TestCase):
    def test_minimal_structure(self):
        expected = {"id": "0034-8910-rsp-48-2-0275", "versions": []}
        self.assertEqual(new("0034-8910-rsp-48-2-0275"), expected)

    def test_docids_are_converted_to_str(self):
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

    def test_add_version_with_assets_mapping(self):
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


if __name__ == "__main__":
    unittest.main()
