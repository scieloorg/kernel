import unittest

from documentstore import services, exceptions

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
        expected = {"publication_year": "2018", "volume": "2"}
        self.services["create_documents_bundle"](id="xpto", metadata=expected)
        result = self.command(id="xpto")
        self.assertEqual(result["metadata"], expected)

    def test_command_with_unexpected_metadata(self):
        expected = {"publication_year": "2018", "volume": "2"}
        self.services["create_documents_bundle"](
            id="xpto",
            metadata={"publication_year": "2018", "volume": "2", "unknown": "0"},
        )
        result = self.command(id="xpto")
        self.assertEqual(result["metadata"], expected)
