import functools
import unittest

from documentstore.domain import DocumentManifest


def fake_utcnow():
    return "2018-08-05T22:33:49.795151Z"


new = DocumentManifest.new
add_version = functools.partial(DocumentManifest.add_version, now=fake_utcnow)
add_asset_version = functools.partial(
    DocumentManifest.add_asset_version, now=fake_utcnow
)


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
                    "timestamp": fake_utcnow(),
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
                    "assets": {"0034-8910-rsp-48-2-0275-gf01.gif": []},
                    "timestamp": fake_utcnow(),
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
                            (
                                "2018-08-05 21:15:07.795137",
                                "/rawfiles/8e644999a8fa4/0034-8910-rsp-48-2-0275-gf01.gif",
                            )
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
                            (
                                "2018-08-05 21:15:07.795137",
                                "/rawfiles/8e644999a8fa4/0034-8910-rsp-48-2-0275-gf01.gif",
                            ),
                            (
                                fake_utcnow(),
                                "/rawfiles/7a664999a8fb3/0034-8910-rsp-48-2-0275-gf01.gif",
                            ),
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

    def test_additional_data_are_preserved_while_adding_versions_for_assets(self):
        doc = {
            "_revision": "a1eda318424",
            "id": "0034-8910-rsp-48-2-0275",
            "versions": [
                {
                    "data": "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275.xml",
                    "assets": {"0034-8910-rsp-48-2-0275-gf01.gif": []},
                }
            ],
        }
        expected = {
            "_revision": "a1eda318424",
            "id": "0034-8910-rsp-48-2-0275",
            "versions": [
                {
                    "data": "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275.xml",
                    "assets": {
                        "0034-8910-rsp-48-2-0275-gf01.gif": [
                            (
                                fake_utcnow(),
                                "/rawfiles/7a664999a8fb3/0034-8910-rsp-48-2-0275-gf01.gif",
                            )
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

    def test_add_asset_version_for_unknown_asset(self):
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

        self.assertRaises(
            KeyError,
            add_asset_version,
            doc,
            "0034-8910-rsp-48-2-0275-UNKNOWN.gif",
            "/rawfiles/7a664999a8fb3/0034-8910-rsp-48-2-0275-gf01.gif",
        )

    def test_additional_data_are_preserved_while_adding_versions(self):
        doc = {
            "_revision": "a1eda318424",
            "id": "0034-8910-rsp-48-2-0275",
            "versions": [],
        }
        new_version = add_version(
            doc,
            "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275.xml",
            ["0034-8910-rsp-48-2-0275-gf01.gif"],
        )

        self.assertEqual(new_version["_revision"], "a1eda318424")
