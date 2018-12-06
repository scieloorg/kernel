import unittest
import functools
from copy import deepcopy

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


new = functools.partial(domain.DocumentsBundle.new, now=fake_utcnow)


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
            latest["data"],
            "/rawfiles/2d3ad9c6bc656/0034-8910-rsp-48-2-0275.xml",
        )

    def test_get_latest_version_when_there_isnt_any(self):
        document = domain.Document(doc_id="0034-8910-rsp-48-2-0275")
        self.assertRaises(ValueError, lambda: document.version())

    def test_get_oldest_version(self):
        document = self.make_one()
        oldest = document.version(0)
        self.assertEqual(
            oldest["data"],
            "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275.xml",
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


class DocumentsBundleTest(unittest.TestCase):
    def test_new(self):
        fake_date = fake_utcnow()
        expected = {
            "id": "0034-8910-rsp-48-2",
            "created": fake_date,
            "updated": fake_date,
            "items": [],
            "metadata": {},
        }
        self.assertEqual(new("0034-8910-rsp-48-2"), expected)

    def test_new_set_same_value_to_created_updated(self):
        documents_bundle = domain.DocumentsBundle.new("0034-8910-rsp-48-2")
        self.assertEqual(
            documents_bundle["created"], documents_bundle["updated"]
        )

    def test_set_publication_year(self):
        documents_bundle = new("0034-8910-rsp-48-2")
        current_updated = documents_bundle["updated"]
        documents_bundle = domain.DocumentsBundle.set_publication_year(
            documents_bundle, "2018"
        )
        self.assertEqual(
            documents_bundle["metadata"]["publication_year"], "2018"
        )
        self.assertTrue(current_updated < documents_bundle["updated"])

    def test_set_publication_year_convert_to_str(self):
        documents_bundle = new("0034-8910-rsp-48-2")
        documents_bundle = domain.DocumentsBundle.set_publication_year(
            documents_bundle, 2018
        )
        self.assertEqual(
            documents_bundle["metadata"]["publication_year"], "2018"
        )

    def test_set_volume(self):
        documents_bundle = new("0034-8910-rsp-48-2")
        current_updated = documents_bundle["updated"]
        documents_bundle = domain.DocumentsBundle.set_volume(
            documents_bundle, "25"
        )
        self.assertEqual(documents_bundle["metadata"]["volume"], "25")
        self.assertTrue(current_updated < documents_bundle["updated"])

    def test_add_item(self):
        documents_bundle = new("0034-8910-rsp-48-2")
        current_updated = documents_bundle["updated"]
        documents_bundle = domain.DocumentsBundle.add_item(
            documents_bundle, "/documents/0034-8910-rsp-48-2-0275"
        )
        self.assertEqual(
            documents_bundle["items"][-1], "/documents/0034-8910-rsp-48-2-0275"
        )
        self.assertTrue(current_updated < documents_bundle["updated"])

    def _assert_raises_with_message(self, type, message, func, *args):
        try:
            func(*args)
        except type as exc:
            self.assertEqual(
                str(exc),
                message
            )
        else:
            self.assertTrue(False)

    def test_add_item_raises_exception_if_item_already_exists(self):
        documents_bundle = new("0034-8910-rsp-48-2")
        documents_bundle = domain.DocumentsBundle.add_item(
            documents_bundle, "/documents/0034-8910-rsp-48-2-0275"
        )
        current_updated = documents_bundle["updated"]
        current_item_len = len(documents_bundle["items"])
        self._assert_raises_with_message(
            exceptions.AlreadyExists,
            "cannot add documents bundle item "
            '"/documents/0034-8910-rsp-48-2-0275": the item already exists',
            domain.DocumentsBundle.add_item,
            documents_bundle,
            "/documents/0034-8910-rsp-48-2-0275"
        )
        self.assertEqual(current_updated, documents_bundle["updated"])
        self.assertEqual(current_item_len, len(documents_bundle["items"]))

    def test_insert_item(self):
        documents_bundle = new("0034-8910-rsp-48-2")
        current_updated = documents_bundle["updated"]
        documents_bundle = domain.DocumentsBundle.add_item(
            documents_bundle, "/documents/0034-8910-rsp-48-2-0775"
        )
        documents_bundle = domain.DocumentsBundle.insert_item(
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
        documents_bundle = new("0034-8910-rsp-48-2")
        documents_bundle = domain.DocumentsBundle.add_item(
            documents_bundle, "/documents/0034-8910-rsp-48-2-0775"
        )
        current_updated = documents_bundle["updated"]
        current_item_len = len(documents_bundle["items"])
        self._assert_raises_with_message(
            exceptions.AlreadyExists,
            "cannot insert documents bundle item "
            '"/documents/0034-8910-rsp-48-2-0775": the item already exists',
            domain.DocumentsBundle.insert_item,
            documents_bundle,
            0,
            "/documents/0034-8910-rsp-48-2-0775"
        )
        self.assertEqual(current_updated, documents_bundle["updated"])
        self.assertEqual(current_item_len, len(documents_bundle["items"]))

    def test_insert_item_follows_python_semantics(self):
        documents_bundle = new("0034-8910-rsp-48-2")
        documents_bundle = domain.DocumentsBundle.add_item(
            documents_bundle, "/documents/0034-8910-rsp-48-2-0475"
        )
        documents_bundle = domain.DocumentsBundle.insert_item(
            documents_bundle, -10, "/documents/0034-8910-rsp-48-2-0275"
        )
        self.assertEqual(
            documents_bundle["items"][0], "/documents/0034-8910-rsp-48-2-0275"
        )
        documents_bundle = domain.DocumentsBundle.insert_item(
            documents_bundle, 10, "/documents/0034-8910-rsp-48-2-0975"
        )
        self.assertEqual(
            documents_bundle["items"][-1], "/documents/0034-8910-rsp-48-2-0975"
        )

    def test_remove_item(self):
        documents_bundle = new("0034-8910-rsp-48-2")
        current_updated = documents_bundle["updated"]
        documents_bundle = domain.DocumentsBundle.add_item(
            documents_bundle, "/documents/0034-8910-rsp-48-2-0475"
        )
        documents_bundle = domain.DocumentsBundle.remove_item(
            documents_bundle, "/documents/0034-8910-rsp-48-2-0475"
        )
        self.assertNotIn(
            "/documents/0034-8910-rsp-48-2-0475", documents_bundle["items"]
        )
        self.assertTrue(current_updated < documents_bundle["updated"])

    def test_remove_item_raises_exception_if_item_does_not_exist(self):
        documents_bundle = new("0034-8910-rsp-48-2")
        current_updated = documents_bundle["updated"]
        current_item_len = len(documents_bundle["items"])
        self._assert_raises_with_message(
            exceptions.DoesNotExist,
            "cannot remove documents bundle item "
            '"/documents/0034-8910-rsp-48-2-0775": the item does not exist',
            domain.DocumentsBundle.remove_item,
            documents_bundle,
            "/documents/0034-8910-rsp-48-2-0775"
        )
        self.assertEqual(current_updated, documents_bundle["updated"])
        self.assertEqual(current_item_len, len(documents_bundle["items"]))
