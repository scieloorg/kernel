import unittest
from copy import deepcopy

from documentstore import domain

SAMPLE_MANIFEST = {
    "id": "0034-8910-rsp-48-2-0275",
    "versions": [
        {
            "data": "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275.xml",
            "assets": {
                "0034-8910-rsp-48-2-0275-gf01.gif": [
                    (
                        "2018-08-05 23:03:44.971230",
                        "/rawfiles/8e644999a8fa4/0034-8910-rsp-48-2-0275-gf01.gif",
                    ),
                    (
                        "2018-08-05 23:08:41.590174",
                        "/rawfiles/bf139b9aa3066/0034-8910-rsp-48-2-0275-gf01.gif",
                    ),
                ]
            },
            "timestamp": "2018-08-05 23:02:29.392990",
        },
        {
            "data": "/rawfiles/2d3ad9c6bc656/0034-8910-rsp-48-2-0275.xml",
            "assets": {
                "0034-8910-rsp-48-2-0275-gf01.gif": [
                    (
                        "2018-08-05 23:30:29.392995",
                        "/rawfiles/bf139b9aa3066/0034-8910-rsp-48-2-0275-gf01.gif",
                    )
                ]
            },
            "timestamp": "2018-08-05 23:30:29.392990",
        },
    ],
}


class DocumentTests(unittest.TestCase):
    def make_one(self):
        _manifest = deepcopy(SAMPLE_MANIFEST)
        return domain.Document(manifest=_manifest)

    def test_manifest_is_generated_on_init(self):
        document = domain.Document(doc_id="0034-8910-rsp-48-2-0275")
        self.assertTrue(isinstance(document.manifest, dict))

    def test_manifest_as_arg_on_init(self):
        existing_manifest = {"id": "0034-8910-rsp-48-2-0275", "versions": []}
        document = domain.Document(manifest=existing_manifest)
        self.assertEqual(existing_manifest, document.manifest)

    def test_manifest_with_unknown_schema_is_allowed(self):
        existing_manifest = {"versions": []}
        document = domain.Document(manifest=existing_manifest)
        self.assertEqual(existing_manifest, document.manifest)

    def test_missing_doc_id_return_empty_string(self):
        existing_manifest = {"versions": []}
        document = domain.Document(manifest=existing_manifest)
        self.assertEqual(document.doc_id(), "")

    def test_doc_id(self):
        document = domain.Document(doc_id="0034-8910-rsp-48-2-0275")
        self.assertEqual(document.doc_id(), "0034-8910-rsp-48-2-0275")

    def test_new_version_of_data(self):
        document = self.make_one()
        self.assertEqual(len(document.manifest["versions"]), 2)

        document.new_version(
            "/rawfiles/5e3ad9c6cd6b8/0034-8910-rsp-48-2-0275.xml",
            assets_getter=lambda data_url, timeout: (None, []),
        )
        self.assertEqual(len(document.manifest["versions"]), 3)

    def test_get_latest_version(self):
        document = self.make_one()
        latest = document.version()
        self.assertEqual(
            latest["data"], "/rawfiles/2d3ad9c6bc656/0034-8910-rsp-48-2-0275.xml"
        )

    def test_get_latest_version_when_there_isnt_any(self):
        document = domain.Document(doc_id="0034-8910-rsp-48-2-0275")
        self.assertRaises(ValueError, lambda: document.version())

    def test_get_oldest_version(self):
        document = self.make_one()
        oldest = document.version(0)
        self.assertEqual(
            oldest["data"], "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275.xml"
        )

    def test_version_only_shows_newest_assets(self):
        document = self.make_one()
        oldest = document.version(0)
        expected = {
            "data": "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275.xml",
            "assets": {
                "0034-8910-rsp-48-2-0275-gf01.gif": "/rawfiles/bf139b9aa3066/0034-8910-rsp-48-2-0275-gf01.gif"
            },
            "timestamp": "2018-08-05 23:02:29.392990",
        }
        self.assertEqual(oldest, expected)

    def test_new_version_automaticaly_references_latest_known_assets(self):
        manifest = {
            "id": "0034-8910-rsp-48-2-0275",
            "versions": [
                {
                    "data": "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275.xml",
                    "assets": {
                        "0034-8910-rsp-48-2-0275-gf01.gif": [
                            (
                                "2018-08-05 23:03:44.971230",
                                "/rawfiles/8e644999a8fa4/0034-8910-rsp-48-2-0275-gf01.gif",
                            ),
                            (
                                "2018-08-05 23:03:49.971250",
                                "/rawfiles/bf139b9aa3066/0034-8910-rsp-48-2-0275-gf01.gif",
                            ),
                        ]
                    },
                }
            ],
        }

        document = domain.Document(manifest=manifest)
        document.new_version(
            "/rawfiles/2d3ad9c6bc656/0034-8910-rsp-48-2-0275.xml",
            assets_getter=lambda data_url, timeout: (
                None,
                [("0034-8910-rsp-48-2-0275-gf01.gif", None)],
            ),
        )
        latest = document.version()
        self.assertEqual(
            latest["assets"]["0034-8910-rsp-48-2-0275-gf01.gif"],
            "/rawfiles/bf139b9aa3066/0034-8910-rsp-48-2-0275-gf01.gif",
        )

    def test_version_at_later_time(self):
        """
        No manifesto `SAMPLE_MANIFEST`, a versão mais recente possui foi
        produzida nos seguintes instantes: a) dados em 2018-08-05 23:30:29.392990
        e b) ativo digital em 2018-08-05 23:30:29.392995.
        """
        document = self.make_one()
        target = document.version_at("2018-12-31")
        expected = {
            "data": "/rawfiles/2d3ad9c6bc656/0034-8910-rsp-48-2-0275.xml",
            "assets": {
                "0034-8910-rsp-48-2-0275-gf01.gif": "/rawfiles/bf139b9aa3066/0034-8910-rsp-48-2-0275-gf01.gif"
            },
            "timestamp": "2018-08-05 23:30:29.392990",
        }
        self.assertEqual(target, expected)

    def test_version_at_given_time(self):
        document = self.make_one()
        target = document.version_at("2018-08-05 23:04:00")
        expected = {
            "data": "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275.xml",
            "assets": {
                "0034-8910-rsp-48-2-0275-gf01.gif": "/rawfiles/8e644999a8fa4/0034-8910-rsp-48-2-0275-gf01.gif"
            },
            "timestamp": "2018-08-05 23:02:29.392990",
        }
        self.assertEqual(target, expected)

    def test_version_at_time_between_data_and_asset_registration(self):
        document = self.make_one()
        target = document.version_at("2018-08-05 23:03:44")
        expected = {
            "data": "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275.xml",
            "assets": {"0034-8910-rsp-48-2-0275-gf01.gif": ""},
            "timestamp": "2018-08-05 23:02:29.392990",
        }
        self.assertEqual(target, expected)

    def test_version_at_time_prior_to_data_registration(self):
        document = self.make_one()
        self.assertRaises(ValueError, lambda: document.version_at("2018-07-01"))
