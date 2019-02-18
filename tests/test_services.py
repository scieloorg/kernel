import unittest
from unittest import mock
import functools
import datetime

from documentstore import services, exceptions, domain

from . import apptesting


def make_services():
    session = apptesting.Session()
    return services.get_handlers(lambda: session)


class CreateDocumentsBundleTest(unittest.TestCase):
    def setUp(self):
        self.services = make_services()
        self.command = self.services.get("create_documents_bundle")

    def test_command_interface(self):
        self.assertIsNotNone(self.command)
        self.assertTrue(callable(self.command))

    def test_command_success(self):
        self.assertIsNone(self.command(id="xpto"))

    def test_command_with_documents_success(self):
        self.assertIsNone(self.command(id="xpto", docs=["/document/1", "/document/2"]))

    def test_command_with_metadata_success(self):
        self.assertIsNone(
            self.command(
                id="xpto", metadata={"publication_year": "2018", "volume": "2"}
            )
        )

    def test_command_raises_exception_if_already_exists(self):
        self.command(id="xpto")
        self.assertRaises(exceptions.AlreadyExists, self.command, id="xpto")


class FetchDocumentsBundleTest(unittest.TestCase):
    def setUp(self):
        self.services = make_services()
        self.command = self.services.get("fetch_documents_bundle")

        datetime_patcher = mock.patch.object(
            domain, "datetime", mock.Mock(wraps=datetime.datetime)
        )
        mocked_datetime = datetime_patcher.start()
        mocked_datetime.utcnow.return_value = datetime.datetime(
            2018, 8, 5, 22, 33, 49, 795151
        )
        self.addCleanup(datetime_patcher.stop)

    def test_command_interface(self):
        self.assertIsNotNone(self.command)
        self.assertTrue(callable(self.command))

    def test_command_raises_exception_if_does_not_exist(self):
        self.assertRaises(exceptions.DoesNotExist, self.command, id="xpto")

    def test_command_success(self):
        self.services["create_documents_bundle"](id="xpto")
        result = self.command(id="xpto")
        self.assertEqual(result["id"], "xpto")

    def test_command_with_documents_success(self):
        self.services["create_documents_bundle"](
            id="xpto", docs=["/document/1", "/document/2"]
        )
        result = self.command(id="xpto")
        self.assertEqual(result["items"], ["/document/1", "/document/2"])

    def test_command_with_metadata_success(self):
        self.services["create_documents_bundle"](
            id="xpto", metadata={"publication_year": "2018", "volume": "2"}
        )
        result = self.command(id="xpto")
        self.assertEqual(
            result["metadata"],
            {
                "publication_year": [("2018-08-05T22:33:49.795151Z", "2018")],
                "volume": [("2018-08-05T22:33:49.795151Z", "2")],
            },
        )

    def test_command_with_unexpected_metadata(self):
        self.services["create_documents_bundle"](
            id="xpto",
            metadata={"publication_year": "2018", "volume": "2", "unknown": "0"},
        )
        result = self.command(id="xpto")
        self.assertEqual(
            result["metadata"],
            {
                "publication_year": [("2018-08-05T22:33:49.795151Z", "2018")],
                "volume": [("2018-08-05T22:33:49.795151Z", "2")],
            },
        )


class UpdateDocumentsBundleTest(unittest.TestCase):
    def setUp(self):
        self.services = make_services()
        self.command = self.services.get("update_documents_bundle_metadata")

        datetime_patcher = mock.patch.object(
            domain, "datetime", mock.Mock(wraps=datetime.datetime)
        )
        mocked_datetime = datetime_patcher.start()
        mocked_datetime.utcnow.return_value = datetime.datetime(
            2018, 8, 5, 22, 33, 49, 795151
        )
        self.addCleanup(datetime_patcher.stop)

    def test_command_interface(self):
        self.assertIsNotNone(self.command)
        self.assertTrue(callable(self.command))

    def test_command_raises_exception_if_does_not_exist(self):
        self.assertRaises(exceptions.DoesNotExist, self.command, id="xpto", metadata={})

    def test_command_success(self):
        self.services["create_documents_bundle"](
            id="xpto", metadata={"publication_year": "2018", "volume": "2"}
        )
        self.command(id="xpto", metadata={"publication_year": "2019"})
        result = self.services["fetch_documents_bundle"](id="xpto")
        self.assertEqual(
            result["metadata"],
            {
                "publication_year": [
                    ("2018-08-05T22:33:49.795151Z", "2018"),
                    ("2018-08-05T22:33:49.795151Z", "2019"),
                ],
                "volume": [("2018-08-05T22:33:49.795151Z", "2")],
            },
        )

    def test_command_with_unexpected_metadata(self):
        self.services["create_documents_bundle"](
            id="xpto", metadata={"publication_year": "2018", "volume": "2"}
        )
        self.command(id="xpto", metadata={"unknown": "0"})
        result = self.services["fetch_documents_bundle"](id="xpto")
        self.assertEqual(
            result["metadata"],
            {
                "publication_year": [("2018-08-05T22:33:49.795151Z", "2018")],
                "volume": [("2018-08-05T22:33:49.795151Z", "2")],
            },
        )

    def test_command_remove_metadata(self):
        """
        Por ora, a maneira de remover um metadado é através da atribuição de uma
        string vazia para o mesmo. Note que este procedimento não removerá o metadado
        do manifesto.
        """
        self.services["create_documents_bundle"](
            id="xpto", metadata={"publication_year": "2018", "volume": "2"}
        )
        self.command(id="xpto", metadata={"volume": ""})
        result = self.services["fetch_documents_bundle"](id="xpto")
        self.assertEqual(
            result["metadata"],
            {
                "publication_year": [("2018-08-05T22:33:49.795151Z", "2018")],
                "volume": [
                    ("2018-08-05T22:33:49.795151Z", "2"),
                    ("2018-08-05T22:33:49.795151Z", ""),
                ],
            },
        )


class AddDocumentToDocumentsBundleTest(unittest.TestCase):
    def setUp(self):
        self.services = make_services()
        self.command = self.services.get("add_document_to_documents_bundle")

    def test_command_interface(self):
        self.assertIsNotNone(self.command)
        self.assertTrue(callable(self.command))

    def test_command_raises_exception_if_does_not_exist(self):
        self.assertRaises(
            exceptions.DoesNotExist, self.command, id="xpto", doc="/document/1"
        )

    def test_command_success(self):
        self.services["create_documents_bundle"](id="xpto")
        self.command(id="xpto", doc="/document/1")
        result = self.services["fetch_documents_bundle"](id="xpto")
        self.assertEqual(result["items"], ["/document/1"])
        self.command(id="xpto", doc="/document/2")
        result = self.services["fetch_documents_bundle"](id="xpto")
        self.assertEqual(result["items"], ["/document/1", "/document/2"])

    def test_command_raises_exception_if_already_exists(self):
        self.services["create_documents_bundle"](id="xpto", docs=["/document/1"])
        self.assertRaises(
            exceptions.AlreadyExists, self.command, id="xpto", doc="/document/1"
        )


class InsertDocumentToDocumentsBundleTest(unittest.TestCase):
    def setUp(self):
        self.services = make_services()
        self.command = self.services.get("insert_document_to_documents_bundle")

    def test_command_interface(self):
        self.assertIsNotNone(self.command)
        self.assertTrue(callable(self.command))

    def test_command_raises_exception_if_does_not_exist(self):
        self.assertRaises(
            exceptions.DoesNotExist, self.command, id="xpto", index=0, doc="/document/1"
        )

    def test_command_success(self):
        self.services["create_documents_bundle"](id="xpto")
        self.command(id="xpto", index=1, doc="/document/1")
        result = self.services["fetch_documents_bundle"](id="xpto")
        self.assertEqual(result["items"], ["/document/1"])
        self.command(id="xpto", index=0, doc="/document/2")
        result = self.services["fetch_documents_bundle"](id="xpto")
        self.assertEqual(result["items"], ["/document/2", "/document/1"])
        self.command(id="xpto", index=10, doc="/document/3")
        result = self.services["fetch_documents_bundle"](id="xpto")
        self.assertEqual(result["items"], ["/document/2", "/document/1", "/document/3"])

    def test_command_raises_exception_if_already_exists(self):
        self.services["create_documents_bundle"](
            id="xpto", docs=["/document/1", "/document/2"]
        )
        self.assertRaises(
            exceptions.AlreadyExists,
            self.command,
            id="xpto",
            index=0,
            doc="/document/1",
        )
        self.assertRaises(
            exceptions.AlreadyExists,
            self.command,
            id="xpto",
            index=1,
            doc="/document/1",
        )


class CreateJournalTest(unittest.TestCase):
    def setUp(self):
        self.services = make_services()
        self.command = self.services.get("create_journal")

    def test_command_interface(self):
        self.assertIsNotNone(self.command)
        self.assertTrue(callable(self.command))

    def test_command_success(self):
        self.assertIsNone(self.command(id="xpto"))

    def test_command_with_metadata_success(self):
        self.assertIsNone(
            self.command(
                id="xpto",
                metadata={
                    "title": "Journal Title",
                    "mission": {"pt": "Missão do Periódico", "en": "Journal Mission"},
                },
            )
        )

    def test_command_raises_exception_if_already_exists(self):
        self.command(id="xpto")
        self.assertRaises(exceptions.AlreadyExists, self.command, id="xpto")

