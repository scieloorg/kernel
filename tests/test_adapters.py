import unittest
from unittest.mock import Mock

from documentstore import adapters, domain, exceptions, interfaces
from . import apptesting


class StoreTestMixin:
    def setUp(self):
        self.DBCollectionMock = Mock()
        self.DBCollectionMock.insert_one = Mock()
        self.DBCollectionMock.find_one = Mock()
        self.DBCollectionMock.replace_one = Mock()

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


class SessionTestMixin:
    """Testa a interface de `interfaces.Session`. Qualquer classe que implementar
    a interface mencionada deverá acompanhar um conjunto de testes que herdam
    deste mixin, conforme o exemplo:

        class AppTestingSessionTests(SessionTestMixin, inittest.TestCase):
            Session = apptesting.Session
    """

    def test_documents_attribute(self):
        session = self.Session()
        self.assertIsInstance(session.documents, interfaces.DataStore)

    def test_documents_bundles_attribute(self):
        session = self.Session()
        self.assertIsInstance(session.documents_bundles, interfaces.DataStore)

    def test_journals_attribute(self):
        session = self.Session()
        self.assertIsInstance(session.journals, interfaces.DataStore)

    def test_observe_returns_none(self):
        session = self.Session()
        self.assertIsNone(session.observe("test_event", lambda d: d))

    def test_notify_runs_callbacks(self):
        callback = Mock()
        session = self.Session()
        session.observe("test_event", callback)
        session.notify("test_event", "foo")
        callback.assert_called_once_with("foo", session)

    def test_notify_doesnt_propagate_exceptions(self):
        import logging

        try:
            # essa manobra de desligar temporariamente o log é para evitar
            # que a mensagem que será emitida em decorrência da execução de
            # `notify` suje o relatório de execução dos testes automatizados.
            # caso essa manobra seja necessária novamente, sugiro transformá-la
            # num decorator ou context-manager.
            logging.disable(logging.CRITICAL)

            session = self.Session()
            session.observe("test_event", lambda d, s: 1 / 0)
            self.assertIsNone(session.notify("test_event", "foo"))
        finally:
            logging.disable(logging.NOTSET)

    def test_notify_logs_exceptions(self):
        session = self.Session()
        session.observe("test_event", lambda d, s: 1 / 0)
        with self.assertLogs("documentstore.interfaces") as log:
            session.notify("test_event", "foo")

        has_message = False
        for log_message in log.output:
            if (
                "ERROR:documentstore.interfaces:cannot run callback" in log_message
                and "Traceback (most recent call last):" in log_message
                and "ZeroDivisionError: division by zero" in log_message
            ):
                has_message = True
        self.assertTrue(has_message)


class AppTestingSessionTests(SessionTestMixin, unittest.TestCase):
    Session = apptesting.Session


class MongoClientStub:
    def collection(self, colname):
        return None


class SessionTests(SessionTestMixin, unittest.TestCase):
    def Session(self):
        return adapters.Session(MongoClientStub())
