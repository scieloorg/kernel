import unittest
from unittest.mock import Mock

from documentstore import adapters, domain, exceptions


class DocumentsBundleStoreTest(unittest.TestCase):
    def setUp(self):
        self.DBCollectionMock = Mock()
        self.DBCollectionMock.insert_one = Mock()
        self.DBCollectionMock.find_one = Mock()
        self.DBCollectionMock.replace_one = Mock()

    def test_add(self):
        bundles = adapters.DocumentsBundleStore(self.DBCollectionMock)
        bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        bundles.add(bundle)
        expected = bundle.manifest
        expected["_id"] = "0034-8910-rsp-48-2"
        self.DBCollectionMock.insert_one.assert_called_once_with(expected)

    def test_add_bundle_with_divergent_ids(self):
        bundles = adapters.DocumentsBundleStore(self.DBCollectionMock)
        bundle = domain.DocumentsBundle(
            manifest={"_id": "1", "id": "0034-8910-rsp-48-2"}
        )
        bundles.add(bundle)
        expected = bundle.manifest
        self.DBCollectionMock.insert_one.assert_called_once_with(expected)

    def test_add_raises_exception_if_already_exists(self):
        import pymongo

        self.DBCollectionMock.insert_one.side_effect = pymongo.errors.DuplicateKeyError(
            ""
        )
        bundles = adapters.DocumentsBundleStore(self.DBCollectionMock)
        bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        self.assertRaises(exceptions.AlreadyExists, bundles.add, bundle)

    def test_fetch_raises_exception_if_does_not_exist(self):
        self.DBCollectionMock.find_one.return_value = None
        bundles = adapters.DocumentsBundleStore(self.DBCollectionMock)
        self.assertRaises(exceptions.DoesNotExist, bundles.fetch, "0034-8910-rsp-48-2")

    def test_fetch(self):
        self.DBCollectionMock.find_one.return_value = {"_id": "0034-8910-rsp-48-2"}
        bundles = adapters.DocumentsBundleStore(self.DBCollectionMock)
        bundles.fetch("0034-8910-rsp-48-2")
        self.DBCollectionMock.find_one.assert_called_once_with(
            {"_id": "0034-8910-rsp-48-2"}
        )

    def test_fetch_returns_documents_bundle(self):
        manifest = {"_id": "0034-8910-rsp-48-2", "id": "0034-8910-rsp-48-2"}
        self.DBCollectionMock.find_one.return_value = manifest
        bundles = adapters.DocumentsBundleStore(self.DBCollectionMock)
        bundle = bundles.fetch("0034-8910-rsp-48-2")
        # XXX: Teste incompleto, pois não testa o retorno de forma precisa
        self.assertEqual(bundle.id(), "0034-8910-rsp-48-2")
        self.assertEqual(bundle.manifest, manifest)

    def test_update(self):
        bundles = adapters.DocumentsBundleStore(self.DBCollectionMock)
        bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        bundles.update(bundle)
        expected = bundle.manifest
        expected["_id"] = "0034-8910-rsp-48-2"
        self.DBCollectionMock.replace_one.assert_called_once_with(
            {"_id": "0034-8910-rsp-48-2"}, expected
        )

    def test_update_raises_exception_if_does_not_exist(self):
        self.DBCollectionMock.replace_one.return_value = Mock(matched_count=0)
        bundles = adapters.DocumentsBundleStore(self.DBCollectionMock)
        bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        self.assertRaises(exceptions.DoesNotExist, bundles.update, bundle)

    def test_update_with_manifest_without__id(self):
        bundles = adapters.DocumentsBundleStore(self.DBCollectionMock)
        bundle = domain.DocumentsBundle(
            manifest={"_id": "1", "id": "0034-8910-rsp-48-2"}
        )
        bundles.update(bundle)
        self.DBCollectionMock.replace_one.assert_called_once_with(
            {"_id": "1"}, bundle.manifest
        )
