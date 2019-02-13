import unittest
from unittest.mock import Mock

from documentstore import adapters, domain, exceptions


class MongoClientStub:
    def collection(self):
        return None


class StoreTestMixin:
    def setUp(self):
        self.DBCollectionMock = Mock()
        self.DBCollectionMock.insert_one = Mock()
        self.DBCollectionMock.find_one = Mock()
        self.DBCollectionMock.replace_one = Mock()

    def test_session(self):
        session = adapters.Session(MongoClientStub())
        self.assertIsInstance(session.documents, adapters.DocumentStore)
        self.assertIsInstance(session.documents_bundles, adapters.DocumentsBundleStore)
        self.assertIsInstance(session.journals, adapters.JournalStore)

    def test_add(self):
        store = self.Adapter(self.DBCollectionMock)
        data = self.DomainClass(id="0034-8910-rsp-48-2")
        store.add(data)
        expected = data.manifest
        expected["_id"] = "0034-8910-rsp-48-2"
        self.DBCollectionMock.insert_one.assert_called_once_with(expected)

    def test_add_data_with_divergent_ids(self):
        store = self.Adapter(self.DBCollectionMock)
        data = self.DomainClass(manifest={"_id": "1", "id": "0034-8910-rsp-48-2"})
        store.add(data)
        expected = data.manifest
        self.DBCollectionMock.insert_one.assert_called_once_with(expected)

    def test_add_raises_exception_if_already_exists(self):
        import pymongo

        self.DBCollectionMock.insert_one.side_effect = pymongo.errors.DuplicateKeyError(
            ""
        )
        store = self.Adapter(self.DBCollectionMock)
        data = self.DomainClass(id="0034-8910-rsp-48-2")
        self.assertRaises(exceptions.AlreadyExists, store.add, data)

    def test_fetch_raises_exception_if_does_not_exist(self):
        self.DBCollectionMock.find_one.return_value = None
        store = self.Adapter(self.DBCollectionMock)
        self.assertRaises(exceptions.DoesNotExist, store.fetch, "0034-8910-rsp-48-2")

    def test_fetch(self):
        self.DBCollectionMock.find_one.return_value = {"_id": "0034-8910-rsp-48-2"}
        store = self.Adapter(self.DBCollectionMock)
        store.fetch("0034-8910-rsp-48-2")
        self.DBCollectionMock.find_one.assert_called_once_with(
            {"_id": "0034-8910-rsp-48-2"}
        )

    def test_fetch_returns_domain_instance(self):
        manifest = {"_id": "0034-8910-rsp-48-2", "id": "0034-8910-rsp-48-2"}
        self.DBCollectionMock.find_one.return_value = manifest
        store = self.Adapter(self.DBCollectionMock)
        data = store.fetch("0034-8910-rsp-48-2")
        # XXX: Teste incompleto, pois não testa o retorno de forma precisa
        self.assertEqual(data.id(), "0034-8910-rsp-48-2")
        self.assertEqual(data.manifest, manifest)

    def test_update(self):
        store = self.Adapter(self.DBCollectionMock)
        data = self.DomainClass(id="0034-8910-rsp-48-2")
        store.update(data)
        expected = data.manifest
        expected["_id"] = "0034-8910-rsp-48-2"
        self.DBCollectionMock.replace_one.assert_called_once_with(
            {"_id": "0034-8910-rsp-48-2"}, expected
        )

    def test_update_raises_exception_if_does_not_exist(self):
        self.DBCollectionMock.replace_one.return_value = Mock(matched_count=0)
        store = self.Adapter(self.DBCollectionMock)
        data = self.DomainClass(id="0034-8910-rsp-48-2")
        self.assertRaises(exceptions.DoesNotExist, store.update, data)

    def test_update_with_manifest_without__id(self):
        store = self.Adapter(self.DBCollectionMock)
        data = self.DomainClass(manifest={"_id": "1", "id": "0034-8910-rsp-48-2"})
        store.update(data)
        self.DBCollectionMock.replace_one.assert_called_once_with(
            {"_id": "1"}, data.manifest
        )


class DocumentsBundleStoreTest(StoreTestMixin, unittest.TestCase):

    Adapter = adapters.DocumentsBundleStore
    DomainClass = domain.DocumentsBundle


class DocumentsStoreTest(StoreTestMixin, unittest.TestCase):

    Adapter = adapters.DocumentStore
    DomainClass = domain.Document


class JournalStoreTest(StoreTestMixin, unittest.TestCase):

    Adapter = adapters.JournalStore
    DomainClass = domain.Journal
