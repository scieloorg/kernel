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
        },
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
                                "2018-08-05T23:03:44.971230Z",
                                "/rawfiles/8e644999a8fa4/0034-8910-rsp-48-2-0275-gf01.gif",
                            ),
                            (
                                "2018-08-05T23:03:49.971250Z",
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
            "timestamp": "2018-08-05T23:30:29.392990Z",
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
        }
        self.assertEqual(target, expected)

    def test_version_at_time_between_data_and_asset_registration(self):
        document = self.make_one()
        target = document.version_at("2018-08-05T23:03:43Z")
        expected = {
            "data": "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275.xml",
            "assets": {"0034-8910-rsp-48-2-0275-gf01.gif": ""},
            "timestamp": "2018-08-05T23:02:29.392990Z",
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
        self.assertEqual(
            documents_bundle["metadata"]["publication_year"], [(fake_utcnow(), "2018")]
        )

    def test_set_metadata_updates_last_modification_date(self):
        documents_bundle = new_bundle("0034-8910-rsp-48-2")
        current_updated = documents_bundle["updated"]
        documents_bundle = domain.BundleManifest.set_metadata(
            documents_bundle, "publication_year", "2018"
        )
        self.assertTrue(current_updated < documents_bundle["updated"])

    def test_set_metadata_doesnt_overwrite_existing_values(self):
        documents_bundle = new_bundle("0034-8910-rsp-48-2")
        documents_bundle = domain.BundleManifest.set_metadata(
            documents_bundle,
            "publication_year",
            "2018",
            now=lambda: "2018-08-05T22:33:49.795151Z",
        )
        documents_bundle = domain.BundleManifest.set_metadata(
            documents_bundle,
            "publication_year",
            "2019",
            now=lambda: "2018-08-05T22:34:07.795151Z",
        )
        self.assertEqual(
            documents_bundle["metadata"]["publication_year"],
            [
                ("2018-08-05T22:33:49.795151Z", "2018"),
                ("2018-08-05T22:34:07.795151Z", "2019"),
            ],
        )
        self.assertEqual(len(documents_bundle["metadata"]), 1)

    def test_set_metadata_to_preexisting_set(self):
        documents_bundle = new_bundle("0034-8910-rsp-48-2")
        documents_bundle = domain.BundleManifest.set_metadata(
            documents_bundle,
            "publication_year",
            "2018",
            now=lambda: "2018-08-05T22:33:49.795151Z",
        )
        documents_bundle = domain.BundleManifest.set_metadata(
            documents_bundle, "volume", "25", now=lambda: "2018-08-05T22:34:07.795151Z"
        )
        self.assertEqual(
            documents_bundle["metadata"]["publication_year"],
            [("2018-08-05T22:33:49.795151Z", "2018")],
        )
        self.assertEqual(
            documents_bundle["metadata"]["volume"],
            [("2018-08-05T22:34:07.795151Z", "25")],
        )
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

    def test_add_item(self):
        documents_bundle = new_bundle("0034-8910-rsp-48-2")
        current_updated = documents_bundle["updated"]
        documents_bundle = domain.BundleManifest.add_item(
            documents_bundle, "/documents/0034-8910-rsp-48-2-0275"
        )
        self.assertEqual(
            documents_bundle["items"][-1], "/documents/0034-8910-rsp-48-2-0275"
        )
        self.assertTrue(current_updated < documents_bundle["updated"])

    def test_add_item_raises_exception_if_item_already_exists(self):
        documents_bundle = new_bundle("0034-8910-rsp-48-2")
        documents_bundle = domain.BundleManifest.add_item(
            documents_bundle, "/documents/0034-8910-rsp-48-2-0275"
        )
        current_updated = documents_bundle["updated"]
        current_item_len = len(documents_bundle["items"])
        self._assert_raises_with_message(
            exceptions.AlreadyExists,
            'cannot add item "/documents/0034-8910-rsp-48-2-0275" in bundle: '
            "the item already exists",
            domain.BundleManifest.add_item,
            documents_bundle,
            "/documents/0034-8910-rsp-48-2-0275",
        )
        self.assertEqual(current_updated, documents_bundle["updated"])
        self.assertEqual(current_item_len, len(documents_bundle["items"]))

    def test_insert_item(self):
        documents_bundle = new_bundle("0034-8910-rsp-48-2")
        current_updated = documents_bundle["updated"]
        documents_bundle = domain.BundleManifest.add_item(
            documents_bundle, "/documents/0034-8910-rsp-48-2-0775"
        )
        documents_bundle = domain.BundleManifest.insert_item(
            documents_bundle, 0, "/documents/0034-8910-rsp-48-2-0275"
        )
        self.assertEqual(
            documents_bundle["items"][0], "/documents/0034-8910-rsp-48-2-0275"
        )
        self.assertEqual(
            documents_bundle["items"][1], "/documents/0034-8910-rsp-48-2-0775"
        )
        self.assertTrue(current_updated < documents_bundle["updated"])

    def test_insert_item_raises_exception_if_item_already_exists(self):
        documents_bundle = new_bundle("0034-8910-rsp-48-2")
        documents_bundle = domain.BundleManifest.add_item(
            documents_bundle, "/documents/0034-8910-rsp-48-2-0775"
        )
        current_updated = documents_bundle["updated"]
        current_item_len = len(documents_bundle["items"])
        self._assert_raises_with_message(
            exceptions.AlreadyExists,
            'cannot insert item "/documents/0034-8910-rsp-48-2-0775" in bundle: '
            "the item already exists",
            domain.BundleManifest.insert_item,
            documents_bundle,
            0,
            "/documents/0034-8910-rsp-48-2-0775",
        )
        self.assertEqual(current_updated, documents_bundle["updated"])
        self.assertEqual(current_item_len, len(documents_bundle["items"]))

    def test_insert_item_follows_python_semantics(self):
        documents_bundle = new_bundle("0034-8910-rsp-48-2")
        documents_bundle = domain.BundleManifest.add_item(
            documents_bundle, "/documents/0034-8910-rsp-48-2-0475"
        )
        documents_bundle = domain.BundleManifest.insert_item(
            documents_bundle, -10, "/documents/0034-8910-rsp-48-2-0275"
        )
        self.assertEqual(
            documents_bundle["items"][0], "/documents/0034-8910-rsp-48-2-0275"
        )
        documents_bundle = domain.BundleManifest.insert_item(
            documents_bundle, 10, "/documents/0034-8910-rsp-48-2-0975"
        )
        self.assertEqual(
            documents_bundle["items"][-1], "/documents/0034-8910-rsp-48-2-0975"
        )

    def test_remove_item(self):
        documents_bundle = new_bundle("0034-8910-rsp-48-2")
        current_updated = documents_bundle["updated"]
        documents_bundle = domain.BundleManifest.add_item(
            documents_bundle, "/documents/0034-8910-rsp-48-2-0475"
        )
        documents_bundle = domain.BundleManifest.remove_item(
            documents_bundle, "/documents/0034-8910-rsp-48-2-0475"
        )
        self.assertNotIn(
            "/documents/0034-8910-rsp-48-2-0475", documents_bundle["items"]
        )
        self.assertTrue(current_updated < documents_bundle["updated"])

    def test_remove_item_raises_exception_if_item_does_not_exist(self):
        documents_bundle = new_bundle("0034-8910-rsp-48-2")
        current_updated = documents_bundle["updated"]
        current_item_len = len(documents_bundle["items"])
        self._assert_raises_with_message(
            exceptions.DoesNotExist,
            'cannot remove item "/documents/0034-8910-rsp-48-2-0775" from bundle: '
            "the item does not exist",
            domain.BundleManifest.remove_item,
            documents_bundle,
            "/documents/0034-8910-rsp-48-2-0775",
        )
        self.assertEqual(current_updated, documents_bundle["updated"])
        self.assertEqual(current_item_len, len(documents_bundle["items"]))


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
            documents_bundle.manifest["metadata"]["publication_year"],
            [("2018-08-05T22:33:49.795151Z", "2018")],
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

    def test_volume_is_empty_str(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        self.assertEqual(documents_bundle.volume, "")

    def test_set_volume(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.volume = "25"
        self.assertEqual(documents_bundle.volume, "25")
        self.assertEqual(
            documents_bundle.manifest["metadata"]["volume"],
            [("2018-08-05T22:33:49.795151Z", "25")],
        )

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
            documents_bundle.manifest["metadata"]["number"],
            [("2018-08-05T22:33:49.795151Z", "3")],
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
        self.assertEqual(
            documents_bundle.manifest["metadata"]["supplement"],
            [("2018-08-05T22:33:49.795151Z", "3")],
        )

    def test_set_supplement_convert_to_str(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.supplement = 3
        self.assertEqual(documents_bundle.supplement, "3")

    def test_add_document(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.add_document("/documents/0034-8910-rsp-48-2-0275")
        self.assertIn(
            "/documents/0034-8910-rsp-48-2-0275", documents_bundle.manifest["items"]
        )

    def test_add_document_raises_exception_if_item_already_exists(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.add_document("/documents/0034-8910-rsp-48-2-0275")
        self._assert_raises_with_message(
            exceptions.AlreadyExists,
            'cannot add item "/documents/0034-8910-rsp-48-2-0275" in bundle: '
            "the item already exists",
            documents_bundle.add_document,
            "/documents/0034-8910-rsp-48-2-0275",
        )

    def test_documents_returns_empty_list(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        self.assertEqual(documents_bundle.documents, [])

    def test_documents_returns_added_documents_list(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.add_document("/documents/0034-8910-rsp-48-2-0275")
        documents_bundle.add_document("/documents/0034-8910-rsp-48-2-0276")
        documents_bundle.add_document("/documents/0034-8910-rsp-48-2-0277")
        self.assertEqual(
            documents_bundle.documents,
            [
                "/documents/0034-8910-rsp-48-2-0275",
                "/documents/0034-8910-rsp-48-2-0276",
                "/documents/0034-8910-rsp-48-2-0277",
            ],
        )

    def test_remove_document(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.add_document("/documents/0034-8910-rsp-48-2-0275")
        documents_bundle.add_document("/documents/0034-8910-rsp-48-2-0276")
        documents_bundle.add_document("/documents/0034-8910-rsp-48-2-0277")
        documents_bundle.remove_document("/documents/0034-8910-rsp-48-2-0275")
        self.assertNotIn(
            "/documents/0034-8910-rsp-48-2-0275", documents_bundle.manifest["items"]
        )
        self.assertEqual(2, len(documents_bundle.manifest["items"]))

    def test_remove_document_raises_exception_if_item_does_not_exist(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.add_document("/documents/0034-8910-rsp-48-2-0276")
        documents_bundle.add_document("/documents/0034-8910-rsp-48-2-0277")
        self._assert_raises_with_message(
            exceptions.DoesNotExist,
            'cannot remove item "/documents/0034-8910-rsp-48-2-0275" from bundle: '
            "the item does not exist",
            documents_bundle.remove_document,
            "/documents/0034-8910-rsp-48-2-0275",
        )

    def test_insert_document(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.add_document("/documents/0034-8910-rsp-48-2-0275")
        documents_bundle.add_document("/documents/0034-8910-rsp-48-2-0276")
        documents_bundle.add_document("/documents/0034-8910-rsp-48-2-0277")
        documents_bundle.insert_document(1, "/documents/0034-8910-rsp-48-2-0271")
        self.assertEqual(
            "/documents/0034-8910-rsp-48-2-0271", documents_bundle.manifest["items"][1]
        )
        self.assertEqual(4, len(documents_bundle.manifest["items"]))

    def test_insert_document_raises_exception_if_item_already_exists(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.add_document("/documents/0034-8910-rsp-48-2-0275")
        self._assert_raises_with_message(
            exceptions.AlreadyExists,
            'cannot insert item "/documents/0034-8910-rsp-48-2-0275" in bundle: '
            "the item already exists",
            documents_bundle.insert_document,
            1,
            "/documents/0034-8910-rsp-48-2-0275",
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
        documents_bundle.mission = {
            "pt": "Publicar trabalhos científicos originais sobre a Amazonia.",
            "es": "Publicar trabajos científicos originales sobre Amazonia.",
            "en": "To publish original scientific papers about Amazonia.",
        }
        self.assertEqual(
            documents_bundle.mission,
            {
                "pt": "Publicar trabalhos científicos originais sobre a Amazonia.",
                "es": "Publicar trabajos científicos originales sobre Amazonia.",
                "en": "To publish original scientific papers about Amazonia.",
            },
        )
        self.assertEqual(
            documents_bundle.manifest["metadata"]["mission"][-1],
            (
                "2018-08-05T22:33:49.795151Z",
                {
                    "pt": "Publicar trabalhos científicos originais sobre a Amazonia.",
                    "es": "Publicar trabajos científicos originales sobre Amazonia.",
                    "en": "To publish original scientific papers about Amazonia.",
                },
            ),
        )

    def test_set_mission_content_is_not_validated(self):
        documents_bundle = domain.Journal(id="0034-8910-rsp-48-2")
        self._assert_raises_with_message(
            TypeError,
            "cannot set mission with value " '"mission-invalid": value must be dict',
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
            journal.manifest["metadata"]["title"],
            [("2018-08-05T22:33:49.795151Z", "Rev. Saúde Pública")],
        )

    def test_title_iso_is_empty_str(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        self.assertEqual(journal.title_iso, "")

    def test_set_title_iso(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        journal.title_iso = "Rev. Saúde Pública"

        self.assertEqual(journal.title_iso, "Rev. Saúde Pública")
        self.assertEqual(
            journal.manifest["metadata"]["title_iso"],
            [("2018-08-05T22:33:49.795151Z", "Rev. Saúde Pública")],
        )

    def test_short_title_is_empty_str(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        self.assertEqual(journal.short_title, "")

    def test_set_short_title(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        journal.short_title = "Rev. Saúde Pública"

        self.assertEqual(journal.short_title, "Rev. Saúde Pública")
        self.assertEqual(
            journal.manifest["metadata"]["short_title"],
            [("2018-08-05T22:33:49.795151Z", "Rev. Saúde Pública")],
        )

    def test_title_slug_is_empty_str(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        self.assertEqual(journal.title_slug, "")

    def test_set_title_slug(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        journal.title_slug = "pesquisa-veterinaria-brasileira"
        self.assertEqual(journal.title_slug, "pesquisa-veterinaria-brasileira")
        self.assertEqual(
            journal.manifest["metadata"]["title_slug"],
            [("2018-08-05T22:33:49.795151Z", "pesquisa-veterinaria-brasileira")],
        )

    def test_acronym_is_empty_str(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        self.assertEqual(journal.acronym, "")

    def test_set_acronym_slug(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        journal.acronym = "rsp"
        self.assertEqual(journal.acronym, "rsp")
        self.assertEqual(
            journal.manifest["metadata"]["acronym"],
            [("2018-08-05T22:33:49.795151Z", "rsp")],
        )

    def test_scielo_issn_is_empty_str(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        self.assertEqual(journal.scielo_issn, "")

    def test_set_scielo_issn(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        journal.scielo_issn = "1809-4392"
        self.assertEqual(journal.scielo_issn, "1809-4392")
        self.assertEqual(
            journal.manifest["metadata"]["scielo_issn"],
            [("2018-08-05T22:33:49.795151Z", "1809-4392")],
        )

    def test_print_issn_is_empty_str(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        self.assertEqual(journal.print_issn, "")

    def test_set_print_issn(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        journal.print_issn = "1809-4392"
        self.assertEqual(journal.print_issn, "1809-4392")
        self.assertEqual(
            journal.manifest["metadata"]["print_issn"],
            [("2018-08-05T22:33:49.795151Z", "1809-4392")],
        )

    def test_electronic_issn_is_empty_str(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        self.assertEqual(journal.electronic_issn, "")

    def test_set_electronic_issn(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        journal.electronic_issn = "1809-4392"
        self.assertEqual(journal.electronic_issn, "1809-4392")
        self.assertEqual(
            journal.manifest["metadata"]["electronic_issn"],
            [("2018-08-05T22:33:49.795151Z", "1809-4392")],
        )

    def test_current_status_is_empty_str(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        self.assertEqual(journal.current_status, "")

    def test_set_current_status(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        journal.current_status = "current"
        self.assertEqual(journal.current_status, "current")
        self.assertEqual(
            journal.manifest["metadata"]["current_status"],
            [("2018-08-05T22:33:49.795151Z", "current")],
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
            "AGRICULTURAL SCIENCES",
            "APPLIED SOCIAL SCIENCES",
            "BIOLOGICAL SCIENCES",
            "ENGINEERING",
            "EXACT AND EARTH SCIENCES",
            "HEALTH SCIENCES",
            "HUMAN SCIENCES",
            "LINGUISTIC, LITERATURE AND ARTS",
        ]
        self.assertEqual(
            journal.subject_areas,
            (
                "AGRICULTURAL SCIENCES",
                "APPLIED SOCIAL SCIENCES",
                "BIOLOGICAL SCIENCES",
                "ENGINEERING",
                "EXACT AND EARTH SCIENCES",
                "HEALTH SCIENCES",
                "HUMAN SCIENCES",
                "LINGUISTIC, LITERATURE AND ARTS",
            ),
        )
        self.assertEqual(
            journal.manifest["metadata"]["subject_areas"][-1],
            (
                "2018-08-05T22:33:49.795151Z",
                (
                    "AGRICULTURAL SCIENCES",
                    "APPLIED SOCIAL SCIENCES",
                    "BIOLOGICAL SCIENCES",
                    "ENGINEERING",
                    "EXACT AND EARTH SCIENCES",
                    "HEALTH SCIENCES",
                    "HUMAN SCIENCES",
                    "LINGUISTIC, LITERATURE AND ARTS",
                ),
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
            "AGRICULTURAL",
            "APPLIED SOCIAL",
            "BIOLOGICAL",
            "ENGINEERING",
            "EXACT AND EARTH",
            "HEALTH",
            "HUMAN",
            "LINGUISTIC, LITERATURE AND ARTS",
        )
        invalid = [
            "AGRICULTURAL",
            "APPLIED SOCIAL",
            "BIOLOGICAL",
            "EXACT AND EARTH",
            "HEALTH",
            "HUMAN",
        ]
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
            journal.manifest["metadata"]["sponsors"][-1],
            (
                "2018-08-05T22:33:49.795151Z",
                (
                    {
                        "name": "FAPESP",
                        "url": "http://www.fapesp.br/",
                        "logo_path": "fixtures/imgs/fapesp.png",
                    },
                ),
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
            [
                (
                    "2018-08-05T22:33:49.795151Z",
                    {
                        "scimago": {"url": "http://scimago.org", "title": "Scimago"},
                        "google": {"total_h5": 10, "h5_median": 5, "h5_year": 2018},
                        "scielo": "valor medio",
                    },
                )
            ],
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

    def test_institution_responsible_for_is_empty_str(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        self.assertEqual(journal.institution_responsible_for, ())

    def test_set_institution_responsible_for(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        journal.institution_responsible_for = ("Usp", "Scielo")

        self.assertEqual(journal.institution_responsible_for, ("Usp", "Scielo"))
        self.assertEqual(
            journal.manifest["metadata"]["institution_responsible_for"][-1],
            ("2018-08-05T22:33:49.795151Z", ("Usp", "Scielo")),
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
        self.assertEqual(
            journal.manifest["metadata"]["online_submission_url"],
            [("2018-08-05T22:33:49.795151Z", url)],
        )

    def test_online_submission_url_default_is_empty(self):
        journal = domain.Journal(id="0034-8910-rsp-48-2")
        self.assertEqual(journal.online_submission_url, "")
