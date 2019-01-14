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
