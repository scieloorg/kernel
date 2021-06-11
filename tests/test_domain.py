import unittest
from unittest import mock
import functools
from copy import deepcopy
import datetime

from documentstore import domain, exceptions

SAMPLE_MANIFEST = {
    "id": "0034-8910-rsp-48-2-0275",
    "versions": [
        {
            "data": "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275.xml",
            "assets": {
                "0034-8910-rsp-48-2-0275-gf01.gif": [
                    (
                        "2018-08-05T23:03:44.971230Z",
                        "/rawfiles/8e644999a8fa4/0034-8910-rsp-48-2-0275-gf01.gif",
                    ),
                    (
                        "2018-08-05T23:08:41.590174Z",
                        "/rawfiles/bf139b9aa3066/0034-8910-rsp-48-2-0275-gf01.gif",
                    ),
                ]
            },
            "timestamp": "2018-08-05T23:02:29.392990Z",
            "renditions": [],
        },
        {
            "data": "/rawfiles/2d3ad9c6bc656/0034-8910-rsp-48-2-0275.xml",
            "assets": {
                "0034-8910-rsp-48-2-0275-gf01.gif": [
                    (
                        "2018-08-05T23:30:29.392995Z",
                        "/rawfiles/bf139b9aa3066/0034-8910-rsp-48-2-0275-gf01.gif",
                    )
                ]
            },
            "timestamp": "2018-08-05T23:30:29.392990Z",
            "renditions": [],
        },
    ],
}
SAMPLE_MANIFEST_WITH_RENDITIONS = {
    "id": "0034-8910-rsp-48-2-0275",
    "versions": [
        {
            "data": "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275.xml",
            "assets": {
                "0034-8910-rsp-48-2-0275-gf01.gif": [
                    (
                        "2018-08-05T23:03:44.971230Z",
                        "/rawfiles/8e644999a8fa4/0034-8910-rsp-48-2-0275-gf01.gif",
                    ),
                    (
                        "2018-08-05T23:08:41.590174Z",
                        "/rawfiles/bf139b9aa3066/0034-8910-rsp-48-2-0275-gf01.gif",
                    ),
                ]
            },
            "timestamp": "2018-08-05T23:02:29.392990Z",
            "renditions": [
                {
                    "filename": "0034-8910-rsp-48-2-0275-pt.pdf",
                    "mimetype": "application/pdf",
                    "lang": "pt",
                    "data": [
                        {
                            "url": "/rawfiles/bf139b9aa3066/0034-8910-rsp-48-2-0275-pt.pdf",
                            "size_bytes": 123456,
                        }
                    ],
                }
            ],
        },
        {
            "data": "/rawfiles/2d3ad9c6bc656/0034-8910-rsp-48-2-0275.xml",
            "assets": {
                "0034-8910-rsp-48-2-0275-gf01.gif": [
                    (
                        "2018-08-05T23:30:29.392995Z",
                        "/rawfiles/bf139b9aa3066/0034-8910-rsp-48-2-0275-gf01.gif",
                    )
                ]
            },
            "timestamp": "2018-08-05T23:30:29.392990Z",
            "renditions": [
                {
                    "filename": "0034-8910-rsp-48-2-0275-v2-pt.pdf",
                    "mimetype": "application/pdf",
                    "lang": "pt",
                    "data": [
                        {
                            "timestamp": "2018-08-05T23:30:43.491793Z",
                            "url": "/rawfiles/bf139b9aa3066/0034-8910-rsp-48-2-0275-v2-pt.pdf",
                            "size_bytes": 123456,
                        }
                    ],
                },
                {
                    "filename": "0034-8910-rsp-48-2-0275-v2-en.pdf",
                    "mimetype": "application/pdf",
                    "lang": "en",
                    "data": [
                        {
                            "timestamp": "2018-08-05T23:30:50.271593Z",
                            "url": "/rawfiles/bf139b9aa3066/0034-8910-rsp-48-2-0275-v2-en.pdf",
                            "size_bytes": 123456,
                        },
                        {
                            "timestamp": "2018-08-06T09:30:23.431397Z",
                            "url": "/rawfiles/bf139b9aa3066/0034-8910-rsp-48-2-0275-v2-2-en.pdf",
                            "size_bytes": 123456,
                        },
                    ],
                },
            ],
        },
    ],
}
SAMPLE_MANIFEST_WITH_DELETIONS = {
    "id": "0034-8910-rsp-48-2-0275",
    "versions": [
        {
            "data": "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275.xml",
            "assets": {
                "0034-8910-rsp-48-2-0275-gf01.gif": [
                    (
                        "2018-08-05T23:03:44.971230Z",
                        "/rawfiles/8e644999a8fa4/0034-8910-rsp-48-2-0275-gf01.gif",
                    ),
                    (
                        "2018-08-05T23:08:41.590174Z",
                        "/rawfiles/bf139b9aa3066/0034-8910-rsp-48-2-0275-gf01.gif",
                    ),
                ]
            },
            "timestamp": "2018-08-05T23:02:29.392990Z",
            "renditions": [],
        },
        {"deleted": True, "timestamp": "2018-08-05T23:30:29.392990Z"},
    ],
}


def fake_utcnow():
    return "2018-08-05T22:33:49.795151Z"


class UnittestMixin:
    def _assert_raises_with_message(self, type, message, func, *args):
        try:
            func(*args)
        except type as exc:
            self.assertEqual(str(exc), message)
        else:
            self.assertTrue(False)


new_bundle = functools.partial(domain.BundleManifest.new, now=fake_utcnow)


class DocumentTests(unittest.TestCase):
    def make_one(self):
        _manifest = deepcopy(SAMPLE_MANIFEST)
        return domain.Document(manifest=_manifest)

    def test_manifest_is_generated_on_init(self):
        document = domain.Document(id="0034-8910-rsp-48-2-0275")
        self.assertTrue(isinstance(document.manifest, dict))

    def test_manifest_as_arg_on_init(self):
        existing_manifest = {"id": "0034-8910-rsp-48-2-0275", "versions": []}
        document = domain.Document(manifest=existing_manifest)
        self.assertEqual(existing_manifest, document.manifest)

    def test_manifest_with_unknown_schema_is_allowed(self):
        existing_manifest = {"versions": []}
        document = domain.Document(manifest=existing_manifest)
        self.assertEqual(existing_manifest, document.manifest)

    def test_missing_id_return_empty_string(self):
        existing_manifest = {"versions": []}
        document = domain.Document(manifest=existing_manifest)
        self.assertEqual(document.id(), "")

    def test_id(self):
        document = domain.Document(id="0034-8910-rsp-48-2-0275")
        self.assertEqual(document.id(), "0034-8910-rsp-48-2-0275")

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
        document = domain.Document(id="0034-8910-rsp-48-2-0275")
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
            "timestamp": "2018-08-05T23:02:29.392990Z",
            "renditions": [],
        }
        self.assertEqual(oldest, expected)

    def test_version_of_deleted_document(self):
        document = domain.Document(manifest=SAMPLE_MANIFEST_WITH_DELETIONS)
        expected = {"deleted": True, "timestamp": "2018-08-05T23:30:29.392990Z"}
        self.assertEqual(document.version(), expected)

    def test_new_version_automaticaly_references_latest_known_assets(self):
        manifest = {
            "id": "0034-8910-rsp-48-2-0275",
            "versions": [
                {
                    "data": "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275.xml",
                    "assets": {
                        "0034-8910-rsp-48-2-0275-gf01.gif": [
                            (
                                "2018-08-05T23:03:44.971230Z",
                                "/rawfiles/8e644999a8fa4/0034-8910-rsp-48-2-0275-gf01.gif",
                            ),
                            (
                                "2018-08-05T23:03:49.971250Z",
                                "/rawfiles/bf139b9aa3066/0034-8910-rsp-48-2-0275-gf01.gif",
                            ),
                        ]
                    },
                    "renditions": [],
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
            "timestamp": "2018-08-05T23:30:29.392990Z",
            "renditions": [],
        }
        self.assertEqual(target, expected)

    def test_version_at_given_time(self):
        document = self.make_one()
        target = document.version_at("2018-08-05T23:04:00Z")
        expected = {
            "data": "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275.xml",
            "assets": {
                "0034-8910-rsp-48-2-0275-gf01.gif": "/rawfiles/8e644999a8fa4/0034-8910-rsp-48-2-0275-gf01.gif"
            },
            "timestamp": "2018-08-05T23:02:29.392990Z",
            "renditions": [],
        }
        self.assertEqual(target, expected)

    def test_version_at_time_between_data_and_asset_registration(self):
        document = self.make_one()
        target = document.version_at("2018-08-05T23:03:43Z")
        expected = {
            "data": "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275.xml",
            "assets": {"0034-8910-rsp-48-2-0275-gf01.gif": ""},
            "timestamp": "2018-08-05T23:02:29.392990Z",
            "renditions": [],
        }
        self.assertEqual(target, expected)

    def test_version_at_time_prior_to_data_registration(self):
        document = self.make_one()
        self.assertRaises(ValueError, lambda: document.version_at("2018-07-01"))

    def test_version_at_non_UCT_time_raises_exception(self):
        document = self.make_one()
        self.assertRaises(
            ValueError, lambda: document.version_at("2018-08-05 23:03:44")
        )

    def test_version_at_of_deleted_document(self):
        document = domain.Document(manifest=SAMPLE_MANIFEST_WITH_DELETIONS)
        expected = {"deleted": True, "timestamp": "2018-08-05T23:30:29.392990Z"}
        self.assertEqual(document.version_at("2018-08-05T23:30:29Z"), expected)

    def test_add_new_rendition(self):
        document = self.make_one()
        self.assertEqual(len(document.version()["renditions"]), 0)

        document.new_rendition_version(
            "0034-8910-rsp-48-2-0275-en.pdf",
            "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275-en.pdf",
            "application/pdf",
            "en",
            798765,
        )
        self.assertEqual(len(document.version()["renditions"]), 1)
        self.assertEqual(
            document.version()["renditions"][0]["filename"],
            "0034-8910-rsp-48-2-0275-en.pdf",
        )

    def test_add_second_rendition_version(self):
        document = self.make_one()
        self.assertEqual(len(document.version()["renditions"]), 0)

        document.new_rendition_version(
            "0034-8910-rsp-48-2-0275-en.pdf",
            "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275-en.pdf",
            "application/pdf",
            "en",
            798765,
        )
        document.new_rendition_version(
            "0034-8910-rsp-48-2-0275-en.pdf",
            "/rawfiles/5cb5f9b2691cd/0034-8910-rsp-48-2-0275-en.pdf",
            "application/pdf",
            "en",
            788523,
        )
        self.assertEqual(len(document.version()["renditions"]), 1)
        self.assertEqual(
            document.version()["renditions"][0]["filename"],
            "0034-8910-rsp-48-2-0275-en.pdf",
        )
        self.assertEqual(document.version()["renditions"][0]["size_bytes"], 788523)
        self.assertEqual(
            document.version()["renditions"][0]["url"],
            "/rawfiles/5cb5f9b2691cd/0034-8910-rsp-48-2-0275-en.pdf",
        )

    def test_add_new_rendition_raises_if_already_set(self):
        document = self.make_one()
        self.assertEqual(len(document.version()["renditions"]), 0)

        document.new_rendition_version(
            "0034-8910-rsp-48-2-0275-en.pdf",
            "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275-en.pdf",
            "application/pdf",
            "en",
            798765,
        )
        self.assertEqual(len(document.version()["renditions"]), 1)
        self.assertRaises(
            exceptions.VersionAlreadySet,
            document.new_rendition_version,
            "0034-8910-rsp-48-2-0275-en.pdf",
            "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275-en.pdf",
            "application/pdf",
            "en",
            798765,
        )

    def test_add_new_rendition_raises_if_version_is_deleted(self):
        sample_manifest = {
            "id": "0034-8910-rsp-48-2-0275",
            "versions": [{"deleted": True, "timestamp": "2018-08-05T23:30:29.392990Z"}],
        }
        document = domain.Document(manifest=sample_manifest)
        self.assertRaises(
            exceptions.DeletedVersion,
            document.new_rendition_version,
            "0034-8910-rsp-48-2-0275-en.pdf",
            "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275-en.pdf",
            "application/pdf",
            "en",
            798765,
        )

    def test_get_latest_renditions_of_latest_version(self):
        expected = [
            {
                "filename": "0034-8910-rsp-48-2-0275-v2-pt.pdf",
                "mimetype": "application/pdf",
                "lang": "pt",
                "url": "/rawfiles/bf139b9aa3066/0034-8910-rsp-48-2-0275-v2-pt.pdf",
                "size_bytes": 123456,
            },
            {
                "filename": "0034-8910-rsp-48-2-0275-v2-en.pdf",
                "mimetype": "application/pdf",
                "lang": "en",
                "url": "/rawfiles/bf139b9aa3066/0034-8910-rsp-48-2-0275-v2-2-en.pdf",
                "size_bytes": 123456,
            },
        ]
        document = domain.Document(manifest=SAMPLE_MANIFEST_WITH_RENDITIONS)
        self.assertEqual(document.version()["renditions"], expected)

    def test_get_renditions_of_a_given_version(self):
        expected = [
            {
                "filename": "0034-8910-rsp-48-2-0275-pt.pdf",
                "mimetype": "application/pdf",
                "lang": "pt",
                "url": "/rawfiles/bf139b9aa3066/0034-8910-rsp-48-2-0275-pt.pdf",
                "size_bytes": 123456,
            }
        ]
        document = domain.Document(manifest=SAMPLE_MANIFEST_WITH_RENDITIONS)
        self.assertEqual(document.version(index=0)["renditions"], expected)

    def test_get_renditions_of_a_given_version_by_timestamp(self):
        expected = [
            {
                "filename": "0034-8910-rsp-48-2-0275-v2-pt.pdf",
                "mimetype": "application/pdf",
                "lang": "pt",
                "url": "/rawfiles/bf139b9aa3066/0034-8910-rsp-48-2-0275-v2-pt.pdf",
                "size_bytes": 123456,
            },
            {
                "filename": "0034-8910-rsp-48-2-0275-v2-en.pdf",
                "mimetype": "application/pdf",
                "lang": "en",
                "url": "/rawfiles/bf139b9aa3066/0034-8910-rsp-48-2-0275-v2-en.pdf",
                "size_bytes": 123456,
            },
        ]
        document = domain.Document(manifest=SAMPLE_MANIFEST_WITH_RENDITIONS)
        self.assertEqual(
            document.version_at("2018-08-05T23:40:00Z")["renditions"], expected
        )

    def test_raises_when_try_to_get_data_from_deleted_document(self):
        sample_manifest = {
            "id": "0034-8910-rsp-48-2-0275",
            "versions": [{"deleted": True, "timestamp": "2018-08-05T23:30:29.392990Z"}],
        }
        document = domain.Document(manifest=sample_manifest)
        self.assertRaises(exceptions.DeletedVersion, document.data)

    def test_raises_when_try_to_add_asset_version_to_deleted_document(self):
        sample_manifest = {
            "id": "0034-8910-rsp-48-2-0275",
            "versions": [{"deleted": True, "timestamp": "2018-08-05T23:30:29.392990Z"}],
        }
        document = domain.Document(manifest=sample_manifest)
        self.assertRaises(
            exceptions.DeletedVersion,
            document.new_asset_version,
            "0034-8910-rsp-48-2-0275-v2.gif",
            "/rawfiles/bf139b9aa3066/0034-8910-rsp-48-2-0275-v2.gif",
        )

    def test_raises_when_try_to_delete_a_deleted_document(self):
        sample_manifest = {
            "id": "0034-8910-rsp-48-2-0275",
            "versions": [{"deleted": True, "timestamp": "2018-08-05T23:30:29.392990Z"}],
        }
        document = domain.Document(manifest=sample_manifest)
        self.assertRaises(exceptions.VersionAlreadySet, document.new_deleted_version)


class BundleManifestTest(UnittestMixin, unittest.TestCase):
    def test_new(self):
        fake_date = fake_utcnow()
        expected = {
            "id": "0034-8910-rsp-48-2",
            "created": fake_date,
            "updated": fake_date,
            "items": [],
            "metadata": {},
        }
        self.assertEqual(new_bundle("0034-8910-rsp-48-2"), expected)

    def test_new_set_same_value_to_created_updated(self):
        documents_bundle = domain.BundleManifest.new("0034-8910-rsp-48-2")
        self.assertEqual(documents_bundle["created"], documents_bundle["updated"])

    def test_set_metadata(self):
        documents_bundle = new_bundle("0034-8910-rsp-48-2")
        documents_bundle = domain.BundleManifest.set_metadata(
            documents_bundle, "publication_year", "2018", now=fake_utcnow
        )

        self.assertEqual(documents_bundle["metadata"]["publication_year"], "2018")

        self.assertEqual(documents_bundle["updated"], fake_utcnow())

    def test_set_metadata_updates_last_modification_date(self):
        documents_bundle = new_bundle("0034-8910-rsp-48-2")
        current_updated = documents_bundle["updated"]
        documents_bundle = domain.BundleManifest.set_metadata(
            documents_bundle, "publication_year", "2018"
        )
        self.assertTrue(current_updated < documents_bundle["updated"])

    def test_set_metadata_to_preexisting_set(self):
        documents_bundle = new_bundle("0034-8910-rsp-48-2")
        documents_bundle = domain.BundleManifest.set_metadata(
            documents_bundle,
            "publication_year",
            "2018",
            now=lambda: "2018-08-05T22:33:49.795151Z",
        )
        self.assertEqual(documents_bundle["metadata"]["publication_year"], "2018")
        self.assertEqual(documents_bundle["updated"], "2018-08-05T22:33:49.795151Z")

        documents_bundle = domain.BundleManifest.set_metadata(
            documents_bundle, "volume", "25", now=lambda: "2018-08-05T22:34:07.795151Z"
        )

        self.assertEqual(documents_bundle["updated"], "2018-08-05T22:34:07.795151Z")
        self.assertEqual(len(documents_bundle["metadata"]), 2)

    def test_get_metadata(self):
        documents_bundle = new_bundle("0034-8910-rsp-48-2")
        documents_bundle = domain.BundleManifest.set_metadata(
            documents_bundle, "publication_year", "2018"
        )
        self.assertEqual(
            domain.BundleManifest.get_metadata(documents_bundle, "publication_year"),
            "2018",
        )

    def test_get_metadata_always_returns_latest(self):
        documents_bundle = new_bundle("0034-8910-rsp-48-2")
        documents_bundle = domain.BundleManifest.set_metadata(
            documents_bundle, "publication_year", "2018"
        )
        documents_bundle = domain.BundleManifest.set_metadata(
            documents_bundle, "publication_year", "2019"
        )
        self.assertEqual(
            domain.BundleManifest.get_metadata(documents_bundle, "publication_year"),
            "2019",
        )

    def test_get_metadata_defaults_to_empty_str_when_missing(self):
        documents_bundle = new_bundle("0034-8910-rsp-48-2")
        self.assertEqual(
            domain.BundleManifest.get_metadata(documents_bundle, "publication_year"), ""
        )

    def test_get_metadata_with_user_defined_default(self):
        documents_bundle = new_bundle("0034-8910-rsp-48-2")
        self.assertEqual(
            domain.BundleManifest.get_metadata(
                documents_bundle, "publication_year", default="2019"
            ),
            "2019",
        )

    def test_set_component(self):
        bundle = new_bundle("0034-8910-rsp")
        bundle = domain.BundleManifest.set_component(
            bundle, "component-1", "component-1"
        )
        self.assertEqual(bundle["component-1"], "component-1")

    def test_set_component_updates_last_modification_date(self):
        bundle = new_bundle("0034-8910-rsp-48-2")
        current_updated = bundle["updated"]
        bundle = domain.BundleManifest.set_component(
            bundle, "component-1", "component-1"
        )
        self.assertTrue(current_updated < bundle["updated"])

    def test_set_component_to_preexisting_set(self):
        bundle = new_bundle("0034-8910-rsp-48-2")
        bundle = domain.BundleManifest.set_component(
            bundle, "component-1", "component-1"
        )
        bundle = domain.BundleManifest.set_component(
            bundle, "component-1", "component-123"
        )
        self.assertEqual(bundle["component-1"], "component-123")

    def test_get_component_returns_empty_str(self):
        bundle = new_bundle("0034-8910-rsp")
        self.assertEqual(
            domain.BundleManifest.get_component(bundle, "component-1", ""), ""
        )

    def test_get_component_returns_given_default_value(self):
        bundle = new_bundle("0034-8910-rsp")
        self.assertEqual(
            domain.BundleManifest.get_component(bundle, "component-1", [1, 2, 3]),
            [1, 2, 3],
        )

    def test_get_component_returns_component_set(self):
        bundle = new_bundle("0034-8910-rsp")
        bundle = domain.BundleManifest.set_component(
            bundle, "component-1", "component-123"
        )
        self.assertEqual(
            domain.BundleManifest.get_component(bundle, "component-1", ""),
            "component-123",
        )

    def test_remove_component(self):
        bundle = new_bundle("0034-8910-rsp")
        bundle = domain.BundleManifest.set_component(
            bundle, "component-1", "component-123"
        )
        _bundle = domain.BundleManifest.remove_component(bundle, "component-1")
        self.assertEqual(
            domain.BundleManifest.get_component(_bundle, "component-1"), ""
        )

    def test_remove_component_raises_exception_if_does_not_exist(self):
        bundle = new_bundle("0034-8910-rsp")
        self._assert_raises_with_message(
            exceptions.DoesNotExist,
            'cannot remove component "component-1" from bundle: '
            "the component does not exist",
            domain.BundleManifest.remove_component,
            bundle,
            "component-1",
        )

    def test_get_item(self):
        bundle = new_bundle("0034-8910-rsp-48-2")
        item = {"id": "0034-8910-rsp-48-2-0275"}

        self.assertEqual([], bundle["items"])
        self.assertIsNone(
            domain.BundleManifest.get_item(bundle, "0034-8910-rsp-48-2-0275")
        )

        bundle = domain.BundleManifest.add_item(bundle, item)
        self.assertEqual(
            item, domain.BundleManifest.get_item(bundle, "0034-8910-rsp-48-2-0275")
        )

    def test_add_item(self):
        documents_bundle = new_bundle("0034-8910-rsp-48-2")
        current_updated = documents_bundle["updated"]
        documents_bundle = domain.BundleManifest.add_item(
            documents_bundle, {"id": "/documents/0034-8910-rsp-48-2-0275"}
        )
        self.assertEqual(
            documents_bundle["items"][-1], {"id": "/documents/0034-8910-rsp-48-2-0275"}
        )
        self.assertTrue(current_updated < documents_bundle["updated"])

    def test_add_item_raises_exception_if_item_already_exists(self):
        documents_bundle = new_bundle("0034-8910-rsp-48-2")
        documents_bundle = domain.BundleManifest.add_item(
            documents_bundle, {"id": "/documents/0034-8910-rsp-48-2-0275"}
        )
        current_updated = documents_bundle["updated"]
        current_item_len = len(documents_bundle["items"])
        self._assert_raises_with_message(
            exceptions.AlreadyExists,
            'cannot add item "/documents/0034-8910-rsp-48-2-0275" in bundle: '
            "the item id already exists",
            domain.BundleManifest.add_item,
            documents_bundle,
            {"id": "/documents/0034-8910-rsp-48-2-0275"},
        )
        self.assertEqual(current_updated, documents_bundle["updated"])
        self.assertEqual(current_item_len, len(documents_bundle["items"]))

    def test_insert_item(self):
        documents_bundle = new_bundle("0034-8910-rsp-48-2")
        current_updated = documents_bundle["updated"]
        documents_bundle = domain.BundleManifest.add_item(
            documents_bundle, {"id": "/documents/0034-8910-rsp-48-2-0775"}
        )
        documents_bundle = domain.BundleManifest.insert_item(
            documents_bundle, 0, {"id": "/documents/0034-8910-rsp-48-2-0275"}
        )
        self.assertEqual(
            documents_bundle["items"][0], {"id": "/documents/0034-8910-rsp-48-2-0275"}
        )
        self.assertEqual(
            documents_bundle["items"][1], {"id": "/documents/0034-8910-rsp-48-2-0775"}
        )
        self.assertTrue(current_updated < documents_bundle["updated"])

    def test_insert_item_raises_exception_if_item_already_exists(self):
        documents_bundle = new_bundle("0034-8910-rsp-48-2")
        documents_bundle = domain.BundleManifest.add_item(
            documents_bundle, {"id": "/documents/0034-8910-rsp-48-2-0775"}
        )
        current_updated = documents_bundle["updated"]
        current_item_len = len(documents_bundle["items"])
        self._assert_raises_with_message(
            exceptions.AlreadyExists,
            'cannot insert item id "/documents/0034-8910-rsp-48-2-0775" in bundle: '
            "the item id already exists",
            domain.BundleManifest.insert_item,
            documents_bundle,
            0,
            {"id": "/documents/0034-8910-rsp-48-2-0775"},
        )
        self.assertEqual(current_updated, documents_bundle["updated"])
        self.assertEqual(current_item_len, len(documents_bundle["items"]))

    def test_insert_item_follows_python_semantics(self):
        documents_bundle = new_bundle("0034-8910-rsp-48-2")
        documents_bundle = domain.BundleManifest.add_item(
            documents_bundle, {"id": "/documents/0034-8910-rsp-48-2-0475"}
        )
        documents_bundle = domain.BundleManifest.insert_item(
            documents_bundle, -10, {"id": "/documents/0034-8910-rsp-48-2-0275"}
        )
        self.assertEqual(
            documents_bundle["items"][0], {"id": "/documents/0034-8910-rsp-48-2-0275"}
        )
        documents_bundle = domain.BundleManifest.insert_item(
            documents_bundle, 10, {"id": "/documents/0034-8910-rsp-48-2-0975"}
        )
        self.assertEqual(
            documents_bundle["items"][-1], {"id": "/documents/0034-8910-rsp-48-2-0975"}
        )

    def test_remove_item(self):
        documents_bundle = new_bundle("0034-8910-rsp-48-2")
        current_updated = documents_bundle["updated"]
        documents_bundle = domain.BundleManifest.add_item(
            documents_bundle, {"id": "/documents/0034-8910-rsp-48-2-0475"}
        )
        documents_bundle = domain.BundleManifest.remove_item(
            documents_bundle, "/documents/0034-8910-rsp-48-2-0475"
        )
        self.assertNotIn(
            {"id": "/documents/0034-8910-rsp-48-2-0475"}, documents_bundle["items"]
        )
        self.assertTrue(current_updated < documents_bundle["updated"])

    def test_remove_item_raises_exception_if_item_does_not_exist(self):
        documents_bundle = new_bundle("0034-8910-rsp-48-2")
        current_updated = documents_bundle["updated"]
        current_item_len = len(documents_bundle["items"])
        self._assert_raises_with_message(
            exceptions.DoesNotExist,
            "cannot remove item from bundle: "
            'the item id "/documents/0034-8910-rsp-48-2-0775" does not exist',
            domain.BundleManifest.remove_item,
            documents_bundle,
            "/documents/0034-8910-rsp-48-2-0775",
        )
        self.assertEqual(current_updated, documents_bundle["updated"])
        self.assertEqual(current_item_len, len(documents_bundle["items"]))

    def test_bundle_manifest_should_raise_value_error_when_dict_interface_isnt_used(
        self,
    ):
        documents_bundle = new_bundle("0034-8910-rsp-48-2")
        self._assert_raises_with_message(
            ValueError,
            'cannot add this item "0034-8910-rsp-48-2-0775": item must be dict',
            domain.BundleManifest.add_item,
            documents_bundle,
            "0034-8910-rsp-48-2-0775",
        )

    def test_bundle_manifest_should_raise_key_error_when_item_does_not_have_id_key(
        self,
    ):
        documents_bundle = new_bundle("0034-8910-rsp-48-2")
        current_updated = documents_bundle["updated"]
        self._assert_raises_with_message(
            KeyError,
            "'cannot add this item \"{}\": item must contain id key'",
            domain.BundleManifest.add_item,
            documents_bundle,
            {},
        )

        self.assertEqual(0, len(documents_bundle["items"]))
        self.assertEqual(current_updated, documents_bundle["updated"])

    def test_add_item_save_the_item_as_dict(self):
        bundle_manifest = new_bundle("0034-8910-rsp-48-2")
        bundle_manifest = domain.BundleManifest.add_item(
            bundle_manifest, [("id", "/documents/0034-8910-rsp-48-2-0275")]
        )

        self.assertEqual(
            [{"id": "/documents/0034-8910-rsp-48-2-0275"}], bundle_manifest["items"]
        )


class DocumentsBundleTest(UnittestMixin, unittest.TestCase):
    def setUp(self):
        datetime_patcher = mock.patch.object(
            domain, "datetime", mock.Mock(wraps=datetime.datetime)
        )
        mocked_datetime = datetime_patcher.start()
        mocked_datetime.utcnow.return_value = datetime.datetime(
            2018, 8, 5, 22, 33, 49, 795151
        )
        self.addCleanup(datetime_patcher.stop)

    def test_manifest_is_generated_on_init(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        self.assertTrue(isinstance(documents_bundle.manifest, dict))

    def test_manifest_as_arg_on_init(self):
        existing_manifest = new_bundle("0034-8910-rsp-48-2")
        documents_bundle = domain.DocumentsBundle(manifest=existing_manifest)
        self.assertEqual(existing_manifest, documents_bundle.manifest)

    def test_manifest_schema_is_not_validated_on_init(self):
        existing_manifest = {"versions": []}
        documents_bundle = domain.DocumentsBundle(manifest=existing_manifest)
        self.assertEqual(existing_manifest, documents_bundle.manifest)

    def test_id_returns_id(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        self.assertEqual(documents_bundle.id(), "0034-8910-rsp-48-2")

    def test_publication_year_is_empty_str(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        self.assertEqual(documents_bundle.publication_year, "")

    def test_set_publication_year(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.publication_year = "2018"
        self.assertEqual(documents_bundle.publication_year, "2018")
        self.assertEqual(
            documents_bundle.manifest["metadata"]["publication_year"], "2018",
        )

    def test_pid_is_empty_str(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        self.assertEqual(documents_bundle.pid, "")

    def test_set_pid(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.pid = "1413-785220180001"
        self.assertEqual(documents_bundle.pid, "1413-785220180001")
        self.assertEqual(
            documents_bundle.manifest["metadata"]["pid"], "1413-785220180001"
        )

    def test_set_publication_year_convert_to_str(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.publication_year = 2018
        self.assertEqual(documents_bundle.publication_year, "2018")

    def test_set_publication_year_validates_four_digits_year(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        self._assert_raises_with_message(
            ValueError,
            "cannot set publication_year with value " '"18": the value is not valid',
            setattr,
            documents_bundle,
            "publication_year",
            18,
        )

    def test_publication_months_is_empty_dict(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        self.assertEqual(documents_bundle.publication_months, {})

    def test_set_publication_months(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.publication_months = {"start": "08", "end": "09"}
        self.assertEqual(
            documents_bundle.publication_months, {"start": "08", "end": "09"}
        )
        self.assertEqual(
            documents_bundle.manifest["metadata"]["publication_months"],
            {"start": "08", "end": "09"},
        )

    def test_set_publication_months_validates_not_dict(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        self._assert_raises_with_message(
            ValueError,
            "cannot set publication_months with value " '"Jan": the value is not valid',
            setattr,
            documents_bundle,
            "publication_months",
            "Jan",
        )

    def test_volume_is_empty_str(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        self.assertEqual(documents_bundle.volume, "")

    def test_set_volume(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.volume = "25"
        self.assertEqual(documents_bundle.volume, "25")
        self.assertEqual(documents_bundle.manifest["metadata"]["volume"], "25")

    def test_set_volume_convert_to_str(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.volume = 25
        self.assertEqual(documents_bundle.volume, "25")

    def test_set_volume_content_is_not_validated(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.volume = "25.A"
        self.assertEqual(documents_bundle.volume, "25.A")

    def test_number_is_empty_str(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        self.assertEqual(documents_bundle.number, "")

    def test_set_number(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.number = "3"
        self.assertEqual(documents_bundle.number, "3")
        self.assertEqual(
            documents_bundle.manifest["metadata"]["number"], "3",
        )

    def test_set_number_convert_to_str(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.number = 3
        self.assertEqual(documents_bundle.number, "3")

    def test_set_number_content_is_not_validated(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.number = "3.A"
        self.assertEqual(documents_bundle.number, "3.A")

    def test_supplement_is_empty_str(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        self.assertEqual(documents_bundle.supplement, "")

    def test_set_supplement(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.supplement = "3"
        self.assertEqual(documents_bundle.supplement, "3")
        self.assertEqual(documents_bundle.manifest["metadata"]["supplement"], "3")

    def test_set_supplement_convert_to_str(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.supplement = 3
        self.assertEqual(documents_bundle.supplement, "3")

    def test_set_titles(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.titles = [
            {"language": "en", "value": "Title"},
            {"language": "pt", "value": "Título"},
        ]
        self.assertEqual(
            documents_bundle.titles,
            [
                {"language": "en", "value": "Title"},
                {"language": "pt", "value": "Título"},
            ],
        )
        self.assertEqual(
            documents_bundle.manifest["metadata"]["titles"],
            [
                {"language": "en", "value": "Title"},
                {"language": "pt", "value": "Título"},
            ],
        )

    def test_set_titles_content_is_not_validated(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        self._assert_raises_with_message(
            TypeError,
            "cannot set titles with value "
            '"invalid-titles": value must be list of dict',
            setattr,
            documents_bundle,
            "titles",
            "invalid-titles",
        )

    def test_add_document(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.add_document({"id": "/documents/0034-8910-rsp-48-2-0275"})
        self.assertIn(
            {"id": "/documents/0034-8910-rsp-48-2-0275"},
            documents_bundle.manifest["items"],
        )

    def test_add_document_raises_exception_if_item_already_exists(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.add_document({"id": "/documents/0034-8910-rsp-48-2-0275"})
        self._assert_raises_with_message(
            exceptions.AlreadyExists,
            'cannot add item "/documents/0034-8910-rsp-48-2-0275" in bundle: '
            "the item id already exists",
            documents_bundle.add_document,
            {"id": "/documents/0034-8910-rsp-48-2-0275"},
        )

    def test_documents_returns_empty_list(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        self.assertEqual(documents_bundle.documents, [])

    def test_documents_returns_added_documents_list(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.add_document({"id": "/documents/0034-8910-rsp-48-2-0275"})
        documents_bundle.add_document({"id": "/documents/0034-8910-rsp-48-2-0276"})
        documents_bundle.add_document({"id": "/documents/0034-8910-rsp-48-2-0277"})
        self.assertEqual(
            documents_bundle.documents,
            [
                {"id": "/documents/0034-8910-rsp-48-2-0275"},
                {"id": "/documents/0034-8910-rsp-48-2-0276"},
                {"id": "/documents/0034-8910-rsp-48-2-0277"},
            ],
        )

    def test_remove_document(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.add_document({"id": "/documents/0034-8910-rsp-48-2-0275"})
        documents_bundle.add_document({"id": "/documents/0034-8910-rsp-48-2-0276"})
        documents_bundle.add_document({"id": "/documents/0034-8910-rsp-48-2-0277"})
        documents_bundle.remove_document("/documents/0034-8910-rsp-48-2-0275")
        self.assertNotIn(
            {"id": "/documents/0034-8910-rsp-48-2-0275"},
            documents_bundle.manifest["items"],
        )
        self.assertEqual(2, len(documents_bundle.manifest["items"]))

    def test_remove_document_raises_exception_if_item_does_not_exist(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.add_document(
            {"id": "/documents/0034-8910-rsp-48-2-0276", "order": 4}
        )
        documents_bundle.add_document(
            {"id": "/documents/0034-8910-rsp-48-2-0277", "order": 2}
        )
        self._assert_raises_with_message(
            exceptions.DoesNotExist,
            "cannot remove item from bundle: "
            'the item id "/documents/0034-8910-rsp-48-2-0275" does not exist',
            documents_bundle.remove_document,
            "/documents/0034-8910-rsp-48-2-0275",
        )

    def test_insert_document(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.add_document({"id": "/documents/0034-8910-rsp-48-2-0275"})
        documents_bundle.add_document({"id": "/documents/0034-8910-rsp-48-2-0276"})
        documents_bundle.add_document({"id": "/documents/0034-8910-rsp-48-2-0277"})
        documents_bundle.insert_document(
            1, {"id": "/documents/0034-8910-rsp-48-2-0271"}
        )

        self.assertEqual(
            {"id": "/documents/0034-8910-rsp-48-2-0271"},
            documents_bundle.manifest["items"][1],
        )
        self.assertEqual(4, len(documents_bundle.manifest["items"]))

    def test_insert_document_raises_exception_if_item_already_exists(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.add_document({"id": "/documents/0034-8910-rsp-48-2-0275"})
        self._assert_raises_with_message(
            exceptions.AlreadyExists,
            'cannot insert item id "/documents/0034-8910-rsp-48-2-0275" in bundle: '
            "the item id already exists",
            documents_bundle.insert_document,
            1,
            {"id": "/documents/0034-8910-rsp-48-2-0275"},
        )

    def test_data_is_not_none(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        self.assertIsNotNone(documents_bundle.data())

    def test_data_metadata_returns_a_dict(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        self.assertEqual(documents_bundle.data()["metadata"], {})

    def test_data_returns_latest_metadata_version(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.titles = [
            {"language": "en", "value": "Title"},
            {"language": "pt", "value": "Título"},
        ]
        self.assertEqual(
            documents_bundle.data()["metadata"]["titles"],
            [
                {"language": "en", "value": "Title"},
                {"language": "pt", "value": "Título"},
            ],
        )
        documents_bundle.titles = [
            {"language": "en", "value": "Title"},
            {"language": "pt", "value": "Título"},
            {"language": "es", "value": "Título"},
        ]
        self.assertEqual(
            documents_bundle.data()["metadata"]["titles"],
            [
                {"language": "en", "value": "Title"},
                {"language": "pt", "value": "Título"},
                {"language": "es", "value": "Título"},
            ],
        )


class JournalTest(UnittestMixin, unittest.TestCase):
    def setUp(self):
        datetime_patcher = mock.patch.object(
            domain, "datetime", mock.Mock(wraps=datetime.datetime)
        )
        mocked_datetime = datetime_patcher.start()
        mocked_datetime.utcnow.return_value = datetime.datetime(
            2018, 8, 5, 22, 33, 49, 795151
        )
        self.addCleanup(datetime_patcher.stop)

    def test_manifest_is_generated_on_init(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        self.assertTrue(isinstance(journal.manifest, dict))

    def test_manifest_as_arg_on_init(self):
        existing_manifest = new_bundle("0034-8910-rsp-48-2")
        journal = domain.Journal(manifest=existing_manifest)
        self.assertEqual(existing_manifest, journal.manifest)

    def test_manifest_schema_is_not_validated_on_init(self):
        existing_manifest = {"versions": []}
        journal = domain.Journal(manifest=existing_manifest)
        self.assertEqual(existing_manifest, journal.manifest)

    def test_id_returns_id(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        self.assertEqual(journal.id(), "0034-8910-rsp-48-2")

    def test_set_mission(self):
        documents_bundle = domain.Journal(id="0034-8910-rsp-48-2")

        documents_bundle.mission = [
            {
                "language": "pt",
                "value": "Publicar trabalhos científicos originais sobre a Amazonia.",
            },
            {
                "language": "es",
                "value": "Publicar trabajos científicos originales sobre Amazonia.",
            },
            {
                "language": "en",
                "value": "To publish original scientific papers about Amazonia.",
            },
        ]

        self.assertEqual(
            documents_bundle.mission,
            [
                {
                    "language": "pt",
                    "value": "Publicar trabalhos científicos originais sobre a Amazonia.",
                },
                {
                    "language": "es",
                    "value": "Publicar trabajos científicos originales sobre Amazonia.",
                },
                {
                    "language": "en",
                    "value": "To publish original scientific papers about Amazonia.",
                },
            ],
        )
        self.assertEqual(
            documents_bundle.manifest["metadata"]["mission"],
            [
                {
                    "language": "pt",
                    "value": "Publicar trabalhos científicos originais sobre a Amazonia.",
                },
                {
                    "language": "es",
                    "value": "Publicar trabajos científicos originales sobre Amazonia.",
                },
                {
                    "language": "en",
                    "value": "To publish original scientific papers about Amazonia.",
                },
            ],
        )

    def test_set_mission_content_is_not_validated(self):
        documents_bundle = domain.Journal(id="0034-8910-rsp-48-2")
        self._assert_raises_with_message(
            TypeError,
            "cannot set mission with value "
            '"mission-invalid": value must be list of dict',
            setattr,
            documents_bundle,
            "mission",
            "mission-invalid",
        )

    def test_title_is_empty_str(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        self.assertEqual(journal.title, "")

    def test_set_title(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        journal.title = "Rev. Saúde Pública"

        self.assertEqual(journal.title, "Rev. Saúde Pública")
        self.assertEqual(
            journal.manifest["metadata"]["title"], "Rev. Saúde Pública",
        )

    def test_title_iso_is_empty_str(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        self.assertEqual(journal.title_iso, "")

    def test_set_title_iso(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        journal.title_iso = "Rev. Saúde Pública"

        self.assertEqual(journal.title_iso, "Rev. Saúde Pública")
        self.assertEqual(
            journal.manifest["metadata"]["title_iso"], "Rev. Saúde Pública",
        )

    def test_short_title_is_empty_str(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        self.assertEqual(journal.short_title, "")

    def test_set_short_title(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        journal.short_title = "Rev. Saúde Pública"

        self.assertEqual(journal.short_title, "Rev. Saúde Pública")
        self.assertEqual(
            journal.manifest["metadata"]["short_title"], "Rev. Saúde Pública",
        )

    def test_acronym_is_empty_str(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        self.assertEqual(journal.acronym, "")

    def test_set_acronym_slug(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        journal.acronym = "rsp"
        self.assertEqual(journal.acronym, "rsp")
        self.assertEqual(
            journal.manifest["metadata"]["acronym"], "rsp",
        )

    def test_scielo_issn_is_empty_str(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        self.assertEqual(journal.scielo_issn, "")

    def test_set_scielo_issn(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        journal.scielo_issn = "1809-4392"
        self.assertEqual(journal.scielo_issn, "1809-4392")
        self.assertEqual(
            journal.manifest["metadata"]["scielo_issn"], "1809-4392",
        )

    def test_print_issn_is_empty_str(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        self.assertEqual(journal.print_issn, "")

    def test_set_print_issn(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        journal.print_issn = "1809-4392"
        self.assertEqual(journal.print_issn, "1809-4392")
        self.assertEqual(
            journal.manifest["metadata"]["print_issn"], "1809-4392",
        )

    def test_electronic_issn_is_empty_str(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        self.assertEqual(journal.electronic_issn, "")

    def test_set_electronic_issn(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        journal.electronic_issn = "1809-4392"
        self.assertEqual(journal.electronic_issn, "1809-4392")
        self.assertEqual(
            journal.manifest["metadata"]["electronic_issn"], "1809-4392",
        )

    def test_status_is_empty_list(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        self.assertEqual(journal.status_history, [])

    def test_set_status(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        journal.status_history = [{"status": "current"}]
        self.assertEqual(journal.status_history, [{"status": "current"}])
        self.assertEqual(
            journal.manifest["metadata"]["status_history"], [{"status": "current"}],
        )

    def test_get_created(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        self.assertEqual(journal.created(), "2018-08-05T22:33:49.795151Z")

    def test_get_updated(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        self.assertEqual(journal.updated(), "2018-08-05T22:33:49.795151Z")

    def test_update_title_get_updated(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        self.assertEqual(journal.updated(), "2018-08-05T22:33:49.795151Z")

        datetime_patcher = mock.patch.object(
            domain, "datetime", mock.Mock(wraps=datetime.datetime)
        )
        mocked_datetime = datetime_patcher.start()
        mocked_datetime.utcnow.return_value = datetime.datetime(
            2018, 8, 5, 22, 34, 49, 795151
        )
        self.addCleanup(datetime_patcher.stop)
        journal.title = "Novo Journal"
        self.assertEqual(journal.updated(), "2018-08-05T22:34:49.795151Z")

    def test_subject_areas(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        journal.subject_areas = [
            "Agricultural Sciences",
            "Applied Social Sciences",
            "Biological Sciences",
            "Engineering",
            "Exact and Earth Sciences",
            "Health Sciences",
            "Human Sciences",
            "Linguistics, Letters and Arts",
        ]
        self.assertEqual(
            journal.subject_areas,
            (
                "Agricultural Sciences",
                "Applied Social Sciences",
                "Biological Sciences",
                "Engineering",
                "Exact and Earth Sciences",
                "Health Sciences",
                "Human Sciences",
                "Linguistics, Letters and Arts",
            ),
        )
        self.assertEqual(
            journal.manifest["metadata"]["subject_areas"],
            (
                "Agricultural Sciences",
                "Applied Social Sciences",
                "Biological Sciences",
                "Engineering",
                "Exact and Earth Sciences",
                "Health Sciences",
                "Human Sciences",
                "Linguistics, Letters and Arts",
            ),
        )

    def test_set_subject_areas_content_raises_type_error(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        invalid = 1
        self._assert_raises_with_message(
            TypeError,
            "cannot set subject_areas with value "
            '"%s": value must be tuple' % invalid,
            setattr,
            journal,
            "subject_areas",
            invalid,
        )

    def test_set_subject_areas_content_raises_value_error(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        subject_areas = (
            "Agricultural Sciences",
            "Applied Social Sciences",
            "Biological Sciences",
            "Engineering",
            "AGRICULTURAL",
            "APPLIED SOCIAL",
            "BIOLOGICAL",
        )
        invalid = ["AGRICULTURAL", "APPLIED SOCIAL", "BIOLOGICAL"]
        self._assert_raises_with_message(
            ValueError,
            "cannot set subject_areas with value %s: " % repr(subject_areas)
            + "%s are not valid" % repr(invalid),
            setattr,
            journal,
            "subject_areas",
            subject_areas,
        )

    def test_set_subject_areas_content_raises_value_error_for_string(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        subject_areas = "LINGUISTIC, LITERATURE AND ARTS"
        invalid = list(subject_areas)
        self._assert_raises_with_message(
            ValueError,
            "cannot set subject_areas with value %s: " % repr(tuple(subject_areas))
            + "%s are not valid" % repr(invalid),
            setattr,
            journal,
            "subject_areas",
            subject_areas,
        )

    def test_set_sponsors(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        journal.sponsors = (
            {
                "name": "FAPESP",
                "url": "http://www.fapesp.br/",
                "logo_path": "fixtures/imgs/fapesp.png",
            },
        )

        self.assertEqual(
            journal.sponsors,
            (
                {
                    "name": "FAPESP",
                    "url": "http://www.fapesp.br/",
                    "logo_path": "fixtures/imgs/fapesp.png",
                },
            ),
        )

        self.assertEqual(
            journal.manifest["metadata"]["sponsors"],
            (
                {
                    "name": "FAPESP",
                    "url": "http://www.fapesp.br/",
                    "logo_path": "fixtures/imgs/fapesp.png",
                },
            ),
        )

    def test_set_sponsors_should_raise_type_error(self):
        invalid_boolean_sponsors = ((True,),)
        invalid_number_sponsors = ((1, 1.1),)
        journal = domain.Journal(id="0034-8910-rsp-48-2")

        self._assert_raises_with_message(
            TypeError,
            "cannot set sponsors this type %s" % repr(invalid_boolean_sponsors),
            setattr,
            journal,
            "sponsors",
            invalid_boolean_sponsors,
        )

        self._assert_raises_with_message(
            TypeError,
            "cannot set sponsors this type %s" % repr(invalid_number_sponsors),
            setattr,
            journal,
            "sponsors",
            invalid_number_sponsors,
        )

    def test_metrics_str(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        self.assertEqual(journal.metrics, {})

    def test_set_metrics(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        journal.metrics = {
            "scimago": {"url": "http://scimago.org", "title": "Scimago"},
            "google": {"total_h5": 10, "h5_median": 5, "h5_year": 2018},
            "scielo": "valor medio",
        }
        self.assertEqual(
            journal.metrics,
            {
                "scimago": {"url": "http://scimago.org", "title": "Scimago"},
                "google": {"total_h5": 10, "h5_median": 5, "h5_year": 2018},
                "scielo": "valor medio",
            },
        )
        self.assertEqual(
            journal.manifest["metadata"]["metrics"],
            {
                "scimago": {"url": "http://scimago.org", "title": "Scimago"},
                "google": {"total_h5": 10, "h5_median": 5, "h5_year": 2018},
                "scielo": "valor medio",
            },
        )

    def test_set_metrics_content_is_not_validated(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        self._assert_raises_with_message(
            TypeError,
            "cannot set metrics with value " '"metrics-invalid": value must be dict',
            setattr,
            journal,
            "metrics",
            "metrics-invalid",
        )

    def test_set_subject_categories(self):
        journal = domain.Journal(id="0234-8410-bjmbr-587-90")
        categories = [
            "Health Sciences Orthopedics",
            "Human Sciences Psychology",
            "Psychoanalysis",
        ]
        journal.subject_categories = categories
        self.assertEqual(
            journal.manifest["metadata"]["subject_categories"], categories,
        )

    def test_set_int_subject_categories_content_raises_type_error(self):
        journal = domain.Journal(id="0234-8410-bjmbr-587-90")
        invalid = 9
        self._assert_raises_with_message(
            TypeError,
            "cannot set subject_categories with value "
            '"%s": value must be list like object' % invalid,
            setattr,
            journal,
            "subject_categories",
            invalid,
        )

    def test_set_str_subject_categories(self):
        journal = domain.Journal(id="0234-8410-bjmbr-587-90")
        categories = "Health Sciences"
        journal.subject_categories = categories
        self.assertEqual(
            journal.manifest["metadata"]["subject_categories"], list(categories),
        )

    def test_set_tuple_subject_categories(self):
        journal = domain.Journal(id="0234-8410-bjmbr-587-90")
        categories = ("Health Sciences Orthopedics", "Human Sciences Psychology")
        journal.subject_categories = categories
        self.assertEqual(
            journal.manifest["metadata"]["subject_categories"], list(categories),
        )

    def test_set_list_like_object_to_subject_categories(self):
        journal = domain.Journal(id="0234-8410-bjmbr-587-90")

        class Fibonacci:
            def __init__(self, maximo=1000000):
                self.current, self.p_element = 0, 1
                self.maximo = maximo

            def __iter__(self):
                return self

            def __next__(self):
                if self.current > self.maximo:
                    raise StopIteration

                ret = self.current

                self.current, self.p_element = (
                    self.p_element,
                    self.current + self.p_element,
                )

                return str(ret)

        fib_obj = Fibonacci(maximo=10)

        journal.subject_categories = fib_obj
        self.assertEqual(
            journal.manifest["metadata"]["subject_categories"],
            ["0", "1", "1", "2", "3", "5", "8"],
        )

    def test_institution_responsible_for_is_empty_str(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        self.assertEqual(journal.institution_responsible_for, ())

    def test_set_institution_responsible_for(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        journal.institution_responsible_for = ("Usp", "Scielo")

        self.assertEqual(journal.institution_responsible_for, ("Usp", "Scielo"))
        self.assertEqual(
            journal.manifest["metadata"]["institution_responsible_for"],
            ("Usp", "Scielo"),
        )

    def test_set_institution_responsible_for_content_raises_type_error(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        invalid = 1
        self._assert_raises_with_message(
            TypeError,
            "cannot set institution_responsible_for with value "
            '"%s": value must be tuple' % invalid,
            setattr,
            journal,
            "institution_responsible_for",
            invalid,
        )

    def test_institution_responsible_for_content_value_for_string(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        journal.institution_responsible_for = ["USP", "SCIELO"]
        self.assertEqual(journal.institution_responsible_for, ("USP", "SCIELO"))

    def test_set_online_submission_url(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        url = "http://mc04.manuscriptcentral.com/rsp-scielo"
        journal.online_submission_url = url
        self.assertEqual(journal.online_submission_url, url)
        self.assertEqual(journal.manifest["metadata"]["online_submission_url"], url)

    def test_online_submission_url_default_is_empty(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        self.assertEqual(journal.online_submission_url, "")

    def test_set_next_journal(self):
        journal = domain.Journal(id="0034-8910-MR")
        next_journal = {"title": "Materials Research", "id": "journal/0034-8910"}
        journal.next_journal = next_journal
        self.assertEqual(
            journal.manifest["metadata"]["next_journal"], next_journal,
        )

    def test_set_str_to_next_journal_should_raise_type_error(self):
        journal = domain.Journal(id="0034-8910-MR")
        invalid = "name"
        self._assert_raises_with_message(
            TypeError,
            "cannot set next_journal with value "
            '"%s": value must be dict' % repr(invalid),
            setattr,
            journal,
            "next_journal",
            invalid,
        )

    def test_set_int_to_next_journal_should_raise_type_error(self):
        journal = domain.Journal(id="0034-8910-MR")
        invalid = 10
        self._assert_raises_with_message(
            TypeError,
            "cannot set next_journal with value "
            '"%s": value must be dict' % repr(invalid),
            setattr,
            journal,
            "next_journal",
            invalid,
        )

    def test_set_tuple_to_next_journal_should_raise_type_error(self):
        journal = domain.Journal(id="0034-8910-MR")
        invalid = ("item 1", "item 2")
        self._assert_raises_with_message(
            TypeError,
            "cannot set next_journal with value "
            '"%s": value must be dict' % repr(invalid),
            setattr,
            journal,
            "next_journal",
            invalid,
        )

    def test_next_journal_return_empty_dict(self):
        journal = domain.Journal(id="0034-8910-MR")
        self.assertEqual(journal.next_journal, {})

    def test_next_journal_return_raise_key_error_metadata(self):
        journal = domain.Journal(id="0034-8910-MR")

        with self.assertRaises(KeyError):
            journal.manifest["metadata"]["next_journal"]

    def test_set_previous_journal(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        expected = {"title": "Título Anterior", "id": "ID título anterior"}
        journal.previous_journal = expected
        self.assertEqual(journal.previous_journal, expected)
        self.assertEqual(
            journal.manifest["metadata"]["previous_journal"], expected,
        )

    def test_previous_journal_default_is_empty(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        self.assertEqual(journal.previous_journal, {})

    def test_status_history(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        journal.status_history = [{"status": "CURRENT"}]
        self.assertEqual(journal.status_history, [{"status": "CURRENT"}])

        journal.status_history = [{"status": "SUSPENDED", "notes": "motivo"}]
        self.assertEqual(
            journal.status_history, [{"status": "SUSPENDED", "notes": "motivo"}]
        )

        journal.status_history = [{"status": "CEASED"}]
        self.assertEqual(journal.status_history, [{"status": "CEASED"}])

    def test_contact_is_empty_list(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        self.assertEqual(journal.contact, {})

    def test_set_contact(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")

        data_journal = {
            "name": "Faculdade de Saúde Pública da Universidade de São Paulo",
            "country": "Brasil",
            "state": "SP",
            "city": "São Paulo",
            "address": "Avenida Dr. Arnaldo, 715\n01246-904 São Paulo SP Brazil",
            "phone_number": "+55 11 3061-7985",
            "email": "revsp@usp.br",
            "enable_contact": "true",
        }

        journal.contact = data_journal
        self.assertEqual(journal.contact, data_journal)
        self.assertEqual(
            journal.manifest["metadata"]["contact"], data_journal,
        )

    def test_set_contact_content_is_not_validated(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        self._assert_raises_with_message(
            ValueError,
            "cannot set contact with value 'contact-invalid': value must be dict",
            setattr,
            journal,
            "contact",
            "contact-invalid",
        )

    def test_add_issue(self):
        journal = domain.Journal(id="0034-8910-rsp")
        journal.add_issue({"id": "0034-8910-rsp-48-2"})
        self.assertIn({"id": "0034-8910-rsp-48-2"}, journal.manifest["items"])

    def test_add_issue_raises_exception_if_item_already_exists(self):
        journal = domain.Journal(id="0034-8910-rsp")
        journal.add_issue({"id": "0034-8910-rsp-48-2"})
        self._assert_raises_with_message(
            exceptions.AlreadyExists,
            'cannot add item "0034-8910-rsp-48-2" in bundle: '
            "the item id already exists",
            journal.add_issue,
            {"id": "0034-8910-rsp-48-2"},
        )

    def test_insert_issue(self):
        journal = domain.Journal(id="0034-8910-rsp")
        input_expected = [
            (0, {"id": "0034-8910-rsp-48-2"}, 0),
            (1, {"id": "0034-8910-rsp-48-3"}, 1),
            (10, {"id": "0034-8910-rsp-48-4"}, -1),
        ]
        for index, issue, expected in input_expected:
            with self.subTest(index=index, issue=issue, expected=expected):
                journal.insert_issue(index, issue)
                self.assertEqual(issue, journal.manifest["items"][expected])

    def test_insert_issue_shifts_item_in_current_position(self):
        journal = domain.Journal(id="0034-8910-rsp")
        journal.insert_issue(0, {"id": "0034-8910-rsp-48-2"})
        journal.insert_issue(0, {"id": "0034-8910-rsp-48-3"})
        self.assertEqual(
            [{"id": "0034-8910-rsp-48-3"}, {"id": "0034-8910-rsp-48-2"}],
            journal.manifest["items"],
        )

    def test_insert_issue_shifts_item_in_the_last_position(self):
        journal = domain.Journal(id="0034-8910-rsp")
        journal.insert_issue(0, {"id": "0034-8910-rsp-48-2"})
        journal.insert_issue(0, {"id": "0034-8910-rsp-48-3"})
        journal.insert_issue(-1, {"id": "0034-8910-rsp-48-4"})
        self.assertEqual(
            [
                {"id": "0034-8910-rsp-48-3"},
                {"id": "0034-8910-rsp-48-4"},
                {"id": "0034-8910-rsp-48-2"},
            ],
            journal.manifest["items"],
        )

    def test_insert_issue_raises_exception_if_item_already_exists(self):
        journal = domain.Journal(id="0034-8910-rsp")
        journal.insert_issue(0, {"id": "0034-8910-rsp-48-2"})
        self._assert_raises_with_message(
            exceptions.AlreadyExists,
            'cannot insert item id "0034-8910-rsp-48-2" in bundle: '
            "the item id already exists",
            journal.insert_issue,
            1,
            {"id": "0034-8910-rsp-48-2"},
        )

    def test_remove_issue(self):
        journal = domain.Journal(id="0034-8910-rsp")
        journal.add_issue({"id": "0034-8910-rsp-48-2"})
        journal.add_issue({"id": "0034-8910-rsp-48-3"})
        journal.add_issue({"id": "0034-8910-rsp-48-4"})
        journal.remove_issue("0034-8910-rsp-48-3")
        self.assertEqual(
            [{"id": "0034-8910-rsp-48-2"}, {"id": "0034-8910-rsp-48-4"}],
            journal.manifest["items"],
        )

    def test_remove_issue_raises_exception_if_item_does_not_exist(self):
        journal = domain.Journal(id="0034-8910-rsp")
        self._assert_raises_with_message(
            exceptions.DoesNotExist,
            "cannot remove item from bundle: "
            'the item id "0034-8910-rsp-48-2" does not exist',
            journal.remove_issue,
            "0034-8910-rsp-48-2",
        )

    def test_get_issues(self):
        journal = domain.Journal(id="0034-8910-rsp")
        input_issues = [
            {"id": "0034-8910-rsp-48-1"},
            {"id": "0034-8910-rsp-48-2"},
            {"id": "0034-8910-rsp-48-3"},
        ]

        for issue in input_issues:
            journal.insert_issue(0, issue)

        self.assertEqual(
            [
                {"id": "0034-8910-rsp-48-3"},
                {"id": "0034-8910-rsp-48-2"},
                {"id": "0034-8910-rsp-48-1"},
            ],
            journal.issues,
        )

    def test_get_issues_should_be_empty(self):
        journal = domain.Journal(id="0034-8910-rsp")
        self.assertEqual([], journal.issues)

    def test_provisional_is_empty_str(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        self.assertEqual(journal.provisional, "")

    def test_set_provisional(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        journal.provisional = "0034-8910-rsp-48-3"
        self.assertEqual(journal.provisional, "0034-8910-rsp-48-3")
        self.assertEqual(journal.manifest["provisional"], "0034-8910-rsp-48-3")

    def test_set_ahead_of_print_bundle(self):
        journal = domain.Journal(id="0034-8910-rsp")
        journal.ahead_of_print_bundle = "0034-8910-rsp-aop"
        self.assertEqual("0034-8910-rsp-aop", journal.manifest["aop"])

    def test_ahead_of_print_bundle_return_empty_str(self):
        journal = domain.Journal(id="0034-8910-MR")
        self.assertEqual(journal.ahead_of_print_bundle, "")

    def test_remove_ahead_of_print_bundle(self):
        journal = domain.Journal(id="0034-8910-MR")
        journal.ahead_of_print_bundle = "0034-8910-MR"
        self.assertIn("aop", journal.manifest.keys())
        journal.remove_ahead_of_print_bundle()
        self.assertNotIn("aop", journal.manifest.keys())

    def test_remove_ahead_of_print_bundle_raises_exception_if_it_does_not_exist(self):
        journal = domain.Journal(id="0034-8910-rsp")
        self._assert_raises_with_message(
            exceptions.DoesNotExist,
            'cannot remove component "aop" from bundle: the component does not exist',
            journal.remove_ahead_of_print_bundle,
        )

    def test_should_have_a_data_method(self):
        journal = domain.Journal(id="0034-8910-MR")
        self.assertIsNotNone(journal.data())

    def test_should_has_an_empty_metadata(self):
        journal = domain.Journal(id="0034-8910-MR")
        self.assertEqual(journal.data()["metadata"], {})

    def test_should_return_latest_metadata_version(self):
        journal = domain.Journal(id="0034-8910-MR")

        journal.title = "Ciência Agrária 1"
        self.assertEqual(journal.data()["metadata"]["title"], "Ciência Agrária 1")

        journal.title = "Ciência Agrária 2"
        self.assertEqual(journal.data()["metadata"]["title"], "Ciência Agrária 2")


class RetryGracefullyDecoratorTests(unittest.TestCase):
    def test_max_retries(self):
        retry_gracefully = domain.retry_gracefully(max_retries=2, backoff_factor=0.001)

        failing_obj = mock.Mock(
            side_effect=[exceptions.RetryableError(), exceptions.RetryableError(), True]
        )
        failing_obj.__qualname__ = "failing_function"
        decorated_obj = retry_gracefully(failing_obj)
        self.assertEqual(decorated_obj(), True)
        self.assertEqual(failing_obj.call_count, 3)

    def test_user_defined_exceptions(self):
        retry_gracefully = domain.retry_gracefully(
            max_retries=2,
            backoff_factor=0.001,
            exc_list=(exceptions.RetryableError, TypeError),
        )

        failing_obj = mock.Mock(
            side_effect=[TypeError(), exceptions.RetryableError(), True]
        )
        failing_obj.__qualname__ = "failing_function"
        decorated_obj = retry_gracefully(failing_obj)
        self.assertEqual(decorated_obj(), True)
        self.assertEqual(failing_obj.call_count, 3)

    def test_max_retries_default_value(self):
        retry_gracefully = domain.retry_gracefully()
        self.assertEqual(retry_gracefully.max_retries, 4)

    def test_backoff_factor_default_value(self):
        retry_gracefully = domain.retry_gracefully()
        self.assertEqual(retry_gracefully.backoff_factor, 1.2)

    def test_sleep_increases_exponentially(self):
        retry_gracefully = domain.retry_gracefully(max_retries=2, backoff_factor=1.2)
        retry_gracefully._sleep = mock.MagicMock(return_value=None)

        failing_obj = mock.Mock(
            side_effect=[exceptions.RetryableError(), exceptions.RetryableError(), True]
        )
        failing_obj.__qualname__ = "failing_function"
        decorated_obj = retry_gracefully(failing_obj)
        self.assertEqual(decorated_obj(), True)

        calls = [mock.call(1.2 ** i) for i in range(1, 3)]
        retry_gracefully._sleep.assert_has_calls(calls)


class MetadataWithStylesForArticleWithTransTitlesTests(unittest.TestCase):

    def setUp(self):
        self.xml = (
            '<article xmlns:mml="http://www.w3.org/1998/Math/MathML" xmlns:xlink="http://www.w3.org/1999/xlink" article-type="research-article" dtd-version="1.1" specific-use="sps-1.9" xml:lang="pt">'
            '<front>'
            '<article-meta>'
            '''<title-group>
                <article-title>Uma Reflexão de Professores sobre Demonstrações Relativas à Irracionalidade de <inline-formula><mml:math display="inline" id="m1"><mml:mrow><mml:msqrt><mml:mn>2</mml:mn></mml:msqrt></mml:mrow></mml:math></inline-formula> </article-title>
                <trans-title-group xml:lang="en">
                  <trans-title>Teachers' Considerations on the Irrationality Proof of <inline-formula><mml:math display="inline" id="m2"><mml:mrow><mml:msqrt><mml:mn>2</mml:mn></mml:msqrt></mml:mrow></mml:math></inline-formula> </trans-title>
                </trans-title-group>
                <trans-title-group xml:lang="es">
                  <trans-title>Español <inline-formula><mml:math display="inline" id="m2"><mml:mrow><mml:msqrt><mml:mn>2</mml:mn></mml:msqrt></mml:mrow></mml:math></inline-formula> </trans-title>
                </trans-title-group>
            </title-group>'''
            '</article-meta>'
            '</front>'
            '</article>'
        ).encode("utf-8")

    def test_display_format(self):
        result = domain.display_format(self.xml)
        expected = {
            "article_title": {
                "pt": 
                    ('Uma Reflexão de Professores sobre Demonstrações '
                        'Relativas à Irracionalidade de '
                        '<inline-formula><mml:math display="inline" id="m1">'
                        '<mml:mrow><mml:msqrt><mml:mn>2</mml:mn></mml:msqrt>'
                        '</mml:mrow></mml:math></inline-formula> '),
                "en": (
                    """Teachers' Considerations on the Irrationality Proof """
                    """of <inline-formula><mml:math display="inline" """
                    """id="m2">"""
                    """<mml:mrow><mml:msqrt><mml:mn>2</mml:mn></mml:msqrt>"""
                    """</mml:mrow></mml:math></inline-formula> """),
                "es": (
                    """Español <inline-formula><mml:math display="inline" """
                    """id="m2"><mml:mrow><mml:msqrt><mml:mn>2</mml:mn>"""
                    """</mml:msqrt></mml:mrow></mml:math></inline-formula> """
                    ),
            }
        }
        self.assertEqual(expected, result)


class MetadataWithStylesForArticleWithSubarticlesTests(unittest.TestCase):

    def setUp(self):
        self.xml = (
            '<article xmlns:mml="http://www.w3.org/1998/Math/MathML" xmlns:xlink="http://www.w3.org/1999/xlink" article-type="research-article" dtd-version="1.1" specific-use="sps-1.9" xml:lang="en">'
            '<front>'
            '<article-meta>'
            '''
            <title-group>
                <article-title>Heparin solution in the prevention of occlusions in Hickman<sup>®</sup> catheters a randomized clinical trial<xref ref-type="fn" rid="fn1">*</xref></article-title>
            </title-group>
            '''
            '</article-meta>'
            '</front>'

            '''
            <sub-article article-type="translation" id="s1" xml:lang="pt">
                <front-stub>
                  <title-group>
                    <article-title>Solução de <bold>heparina</bold> na prevenção de oclusão do Cateter de Hickman<sup>®</sup> ensaio clínico randomizado<xref ref-type="fn" rid="fn2">*</xref></article-title>
                  </title-group>
              </front-stub>
            </sub-article>
            <sub-article article-type="translation" id="s2" xml:lang="es">
                <front-stub>
                  <title-group>
                    <article-title>Solución <italic>de heparina para prevenir</italic> oclusiones en catéteres de Hickman<sup>®</sup> un ensayo clínico aleatorizado<xref ref-type="fn" rid="fn3">*</xref></article-title>
                  </title-group>
                </front-stub>
            </sub-article>
            '''
            '</article>'
        ).encode("utf-8")

    def test_display_format_removes_xref(self):
        result = domain.display_format(self.xml)
        expected = {
            "article_title": {
                "en": (
                    """Heparin solution in the prevention of occlusions """
                    """in Hickman<sup>®</sup> catheters a randomized """
                    """clinical trial"""
                    ),
                "pt": (
                    """Solução de <b>heparina</b> na prevenção de oclusão do """
                    """Cateter de Hickman<sup>®</sup> ensaio clínico """
                    """randomizado"""),
                "es": (
                    """Solución <i>de heparina para prevenir</i> oclusiones en """
                    """catéteres de Hickman<sup>®</sup> un ensayo clínico """
                    """aleatorizado"""),
            }
        }
        self.assertDictEqual(expected, result)
