import unittest
from unittest import mock
import datetime

from documentstore import services, exceptions, domain

from . import apptesting


def make_services():
    session = apptesting.Session()
    return services.get_handlers(lambda: session), session


class CreateDocumentsBundleTest(unittest.TestCase):
    def setUp(self):
        self.services, self.session = make_services()
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

    def test_command_notify_event(self):
        with mock.patch.object(self.session, "notify") as mock_notify:
            self.command(id="xpto", docs=["/document/1"])
            mock_notify.assert_called_once_with(
                services.Events.DOCUMENTSBUNDLE_CREATED,
                {
                    "id": "xpto",
                    "docs": ["/document/1"],
                    "metadata": None,
                    "bundle": mock.ANY,
                },
            )


class FetchDocumentsBundleTest(unittest.TestCase):
    def setUp(self):
        self.services, self.session = make_services()
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
        self.services, self.session = make_services()
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

    def test_command_notify_event(self):
        self.services["create_documents_bundle"](
            id="xpto", metadata={"publication_year": "2018", "volume": "2"}
        )
        with mock.patch.object(self.session, "notify") as mock_notify:
            self.command(id="xpto", metadata={"publication_year": "2019"})
            mock_notify.assert_called_once_with(
                services.Events.DOCUMENTSBUNDLE_METATADA_UPDATED,
                {
                    "id": "xpto",
                    "metadata": {"publication_year": "2019"},
                    "bundle": mock.ANY,
                },
            )


class AddDocumentToDocumentsBundleTest(unittest.TestCase):
    def setUp(self):
        self.services, self.session = make_services()
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

    def test_command_notify_event(self):
        self.services["create_documents_bundle"](id="xpto")
        with mock.patch.object(self.session, "notify") as mock_notify:
            self.command(id="xpto", doc="/document/1")
            mock_notify.assert_called_once_with(
                services.Events.DOCUMENT_ADDED_TO_DOCUMENTSBUNDLE,
                {"id": "xpto", "doc": "/document/1", "bundle": mock.ANY},
            )


class InsertDocumentToDocumentsBundleTest(unittest.TestCase):
    def setUp(self):
        self.services, self.session = make_services()
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

    def test_command_notify_event(self):
        self.services["create_documents_bundle"](id="xpto")
        with mock.patch.object(self.session, "notify") as mock_notify:
            self.command(id="xpto", index=10, doc="/document/3")
            mock_notify.assert_called_once_with(
                services.Events.DOCUMENT_INSERTED_TO_DOCUMENTSBUNDLE,
                {"id": "xpto", "doc": "/document/3", "index": 10, "bundle": mock.ANY},
            )


class CreateJournalTest(unittest.TestCase):
    def setUp(self):
        self.services, self.session = make_services()
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

    def test_command_notify_event(self):
        with mock.patch.object(self.session, "notify") as mock_notify:
            self.command(id="jxpto")
            mock_notify.assert_called_once_with(
                services.Events.JOURNAL_CREATED,
                {"id": "jxpto", "journal": mock.ANY, "metadata": None},
            )


class AddIssueToJournalTest(unittest.TestCase):
    def setUp(self):
        self.services, self.session = make_services()
        self.command = self.services.get("add_issue_to_journal")
        create_journal_command = self.services.get("create_journal")
        create_journal_command(id="0034-8910-rsp")

    def test_command_interface(self):
        self.assertIsNotNone(self.command)
        self.assertTrue(callable(self.command))

    def test_command_calls_add_issue(self):
        with mock.patch.object(self.session.journals, "fetch") as mock_fetch:
            JournalStub = mock.Mock(spec=domain.Journal)
            JournalStub.add_issue = mock.Mock()
            mock_fetch.return_value = JournalStub
            self.command(id="0034-8910-rsp", issue="0034-8910-rsp-48-2")
            JournalStub.add_issue.assert_called_once_with("0034-8910-rsp-48-2")

    def test_command_update_journals(self):
        with mock.patch.object(self.session.journals, "fetch") as mock_fetch:
            JournalStub = mock.Mock(spec=domain.Journal)
            JournalStub.add_issue = mock.Mock()
            mock_fetch.return_value = JournalStub
            with mock.patch.object(self.session.journals, "update") as mock_update:
                self.command(id="0034-8910-rsp", issue="0034-8910-rsp-48-2")
                mock_update.assert_called_once_with(JournalStub)

    def test_command_success(self):
        self.assertIsNone(self.command(id="0034-8910-rsp", issue="0034-8910-rsp-48-2"))

    def test_command_raises_exception_if_journal_does_not_exist(self):
        self.assertRaises(
            exceptions.DoesNotExist,
            self.command,
            id="0101-8910-csp",
            issue="0101-8910-csp-48-2",
        )

    def test_command_raises_exception_if_issue_already_exists(self):
        self.command(id="0034-8910-rsp", issue="0034-8910-rsp-48-2")
        self.assertRaises(
            exceptions.AlreadyExists,
            self.command,
            id="0034-8910-rsp",
            issue="0034-8910-rsp-48-2",
        )

    def test_command_notify_event(self):
        with mock.patch.object(self.session.journals, "fetch") as mock_fetch:
            JournalStub = mock.Mock(spec=domain.Journal)
            JournalStub.insert_issue = mock.Mock()
            mock_fetch.return_value = JournalStub
            with mock.patch.object(self.session, "notify") as mock_notify:
                self.command(id="0034-8910-rsp", issue="0034-8910-rsp-48-2")
                mock_notify.assert_called_once_with(
                    services.Events.ISSUE_ADDED_TO_JOURNAL,
                    {
                        "journal": JournalStub,
                        "id": "0034-8910-rsp",
                        "issue": "0034-8910-rsp-48-2",
                    },
                )


class InsertIssueToJournalTest(unittest.TestCase):
    def setUp(self):
        self.services, self.session = make_services()
        self.command = self.services.get("insert_issue_to_journal")
        create_journal_command = self.services.get("create_journal")
        create_journal_command(id="0034-8910-rsp")

    def test_command_interface(self):
        self.assertIsNotNone(self.command)
        self.assertTrue(callable(self.command))

    def test_command_raises_exception_if_journal_does_not_exist(self):
        self.assertRaises(
            exceptions.DoesNotExist,
            self.command,
            id="0101-8910-csp",
            index=0,
            issue="0101-8910-csp-48-2",
        )

    def test_command_calls_insert_issue(self):
        with mock.patch.object(self.session.journals, "fetch") as mock_fetch:
            JournalStub = mock.Mock(spec=domain.Journal)
            JournalStub.insert_issue = mock.Mock()
            mock_fetch.return_value = JournalStub
            self.command(id="0034-8910-rsp", index=0, issue="0034-8910-rsp-48-2")
            JournalStub.insert_issue.assert_called_once_with(0, "0034-8910-rsp-48-2")

    def test_command_update_journals(self):
        with mock.patch.object(self.session.journals, "fetch") as mock_fetch:
            JournalStub = mock.Mock(spec=domain.Journal)
            JournalStub.insert_issue = mock.Mock()
            mock_fetch.return_value = JournalStub
            with mock.patch.object(self.session.journals, "update") as mock_update:
                self.command(id="0034-8910-rsp", index=0, issue="0034-8910-rsp-48-2")
                mock_update.assert_called_once_with(JournalStub)

    def test_command_success(self):
        self.assertIsNone(
            self.command(id="0034-8910-rsp", index=0, issue="0034-8910-rsp-48-2")
        )
        self.assertIsNone(
            self.command(id="0034-8910-rsp", index=10, issue="0034-8910-rsp-48-3")
        )
        self.assertIsNone(
            self.command(id="0034-8910-rsp", index=-1, issue="0034-8910-rsp-48-4")
        )

    def test_command_raises_exception_if_issue_already_exists(self):
        self.command(id="0034-8910-rsp", index=0, issue="0034-8910-rsp-48-2")
        self.assertRaises(
            exceptions.AlreadyExists,
            self.command,
            id="0034-8910-rsp",
            index=0,
            issue="0034-8910-rsp-48-2",
        )
        self.assertRaises(
            exceptions.AlreadyExists,
            self.command,
            id="0034-8910-rsp",
            index=5,
            issue="0034-8910-rsp-48-2",
        )

    def test_command_notify_event(self):
        with mock.patch.object(self.session.journals, "fetch") as mock_fetch:
            JournalStub = mock.Mock(spec=domain.Journal)
            JournalStub.insert_issue = mock.Mock()
            mock_fetch.return_value = JournalStub
            with mock.patch.object(self.session, "notify") as mock_notify:
                self.command(id="0034-8910-rsp", index=0, issue="0034-8910-rsp-48-2")
                mock_notify.assert_called_once_with(
                    services.Events.ISSUE_INSERTED_TO_JOURNAL,
                    {
                        "journal": JournalStub,
                        "id": "0034-8910-rsp",
                        "index": 0,
                        "issue": "0034-8910-rsp-48-2",
                    },
                )


class RemoveIssueFromJournalTest(unittest.TestCase):
    def setUp(self):
        self.services, self.session = make_services()
        self.command = self.services.get("remove_issue_from_journal")
        create_journal_command = self.services.get("create_journal")
        create_journal_command(id="0034-8910-rsp")

    def test_command_interface(self):
        self.assertIsNotNone(self.command)
        self.assertTrue(callable(self.command))

    def test_command_raises_exception_if_journal_does_not_exist(self):
        self.assertRaises(
            exceptions.DoesNotExist,
            self.command,
            id="0101-8910-csp",
            issue="0101-8910-csp-48-2",
        )

    def test_command_calls_remove_issue(self):
        with mock.patch.object(self.session.journals, "fetch") as mock_fetch:
            JournalStub = mock.Mock(spec=domain.Journal)
            JournalStub.remove_issue = mock.Mock()
            mock_fetch.return_value = JournalStub
            self.command(id="0034-8910-rsp", issue="0034-8910-rsp-48-2")
            JournalStub.remove_issue.assert_called_once_with("0034-8910-rsp-48-2")

    def test_command_update_journals(self):
        with mock.patch.object(self.session.journals, "fetch") as mock_fetch:
            JournalStub = mock.Mock(spec=domain.Journal)
            JournalStub.remove_issue = mock.Mock()
            mock_fetch.return_value = JournalStub
            with mock.patch.object(self.session.journals, "update") as mock_update:
                self.command(id="0034-8910-rsp", issue="0034-8910-rsp-48-2")
                mock_update.assert_called_once_with(JournalStub)

    def test_command_success(self):
        self.services.get("add_issue_to_journal")(
            id="0034-8910-rsp", issue="0034-8910-rsp-48-2"
        )
        self.assertIsNone(self.command(id="0034-8910-rsp", issue="0034-8910-rsp-48-2"))

    def test_command_raises_exception_if_issue_does_not_exist(self):
        self.assertRaises(
            exceptions.DoesNotExist,
            self.command,
            id="0034-8910-rsp",
            issue="0034-8910-rsp-48-2",
        )

    def test_command_notify_event(self):
        with mock.patch.object(self.session.journals, "fetch") as mock_fetch:
            JournalStub = mock.Mock(spec=domain.Journal)
            JournalStub.remove_issue = mock.Mock()
            mock_fetch.return_value = JournalStub
            with mock.patch.object(self.session, "notify") as mock_notify:
                self.command(id="0034-8910-rsp", issue="0034-8910-rsp-48-2")
                mock_notify.assert_called_once_with(
                    services.Events.ISSUE_REMOVED_FROM_JOURNAL,
                    {
                        "journal": JournalStub,
                        "id": "0034-8910-rsp",
                        "issue": "0034-8910-rsp-48-2",
                    },
                )


class SetAheadOfPrintBundleToJournalTest(unittest.TestCase):
    def setUp(self):
        self.services, self.session = make_services()
        self.command = self.services.get("set_ahead_of_print_bundle_to_journal")
        create_journal_command = self.services.get("create_journal")
        create_journal_command(id="0034-8910-rsp")

    def test_command_interface(self):
        self.assertIsNotNone(self.command)
        self.assertTrue(callable(self.command))

    def test_command_raises_exception_if_journal_does_not_exist(self):
        self.assertRaises(
            exceptions.DoesNotExist,
            self.command,
            id="0101-8910-csp",
            aop="0101-8910-csp-aop",
        )

    def test_command_calls_ahead_of_print_bundle(self):
        with mock.patch.object(self.session.journals, "fetch") as mock_fetch:
            JournalStub = mock.Mock(spec=domain.Journal)
            JournalStub.ahead_of_print_bundle = mock.Mock()
            mock_fetch.return_value = JournalStub
            self.command(id="0034-8910-rsp", aop="0034-8910-rsp-aop")
            self.assertEqual(
                JournalStub.ahead_of_print_bundle, "0034-8910-rsp-aop")

    def test_command_update_journals(self):
        with mock.patch.object(self.session.journals, "fetch") as mock_fetch:
            JournalStub = mock.Mock(spec=domain.Journal)
            JournalStub.ahead_of_print_bundle = mock.Mock()
            mock_fetch.return_value = JournalStub
            with mock.patch.object(self.session.journals, "update") as mock_update:
                self.command(id="0034-8910-rsp", aop="0034-8910-rsp-aop")
                mock_update.assert_called_once_with(JournalStub)

    def test_command_success(self):
        self.assertIsNone(
            self.command(id="0034-8910-rsp", aop="0034-8910-rsp-aop")
        )

    def test_command_notify_event(self):
        with mock.patch.object(self.session.journals, "fetch") as mock_fetch:
            JournalStub = mock.Mock(spec=domain.Journal)
            JournalStub.ahead_of_print_bundle = mock.Mock()
            mock_fetch.return_value = JournalStub
            with mock.patch.object(self.session, "notify") as mock_notify:
                self.command(id="0034-8910-rsp", aop="0034-8910-rsp-aop")
                mock_notify.assert_called_once_with(
                    services.Events.AHEAD_OF_PRINT_BUNDLE_SET_TO_JOURNAL,
                    {
                        "journal": JournalStub,
                        "id": "0034-8910-rsp",
                        "aop": "0034-8910-rsp-aop",
                    },
                )


class RemoveAheadOfPrintBundleFromJournalTest(unittest.TestCase):
    def setUp(self):
        self.services, self.session = make_services()
        self.command = self.services.get("remove_ahead_of_print_bundle_from_journal")
        create_journal_command = self.services.get("create_journal")
        create_journal_command(id="0034-8910-rsp")

    def test_command_interface(self):
        self.assertIsNotNone(self.command)
        self.assertTrue(callable(self.command))

    def test_command_raises_exception_if_journal_does_not_exist(self):
        self.assertRaises(
            exceptions.DoesNotExist,
            self.command,
            id="0101-8910-csp",
        )

    def test_command_calls_remove_ahead_of_print(self):
        with mock.patch.object(self.session.journals, "fetch") as mock_fetch:
            JournalStub = mock.Mock(spec=domain.Journal)
            JournalStub.remove_ahead_of_print_bundle = mock.Mock()
            mock_fetch.return_value = JournalStub
            self.command(id="0034-8910-rsp")
            JournalStub.remove_ahead_of_print_bundle.assert_called_once_with()

    def test_command_update_journals(self):
        with mock.patch.object(self.session.journals, "fetch") as mock_fetch:
            JournalStub = mock.Mock(spec=domain.Journal)
            JournalStub.remove_ahead_of_print_bundle = mock.Mock()
            mock_fetch.return_value = JournalStub
            with mock.patch.object(self.session.journals, "update") as mock_update:
                self.command(id="0034-8910-rsp")
                mock_update.assert_called_once_with(JournalStub)

    def test_command_raises_exception_if_ahead_of_print_does_not_exist(self):
        self.assertRaises(
            exceptions.DoesNotExist,
            self.command,
            id="0034-8910-rsp"
        )

    def test_command_notify_event(self):
        with mock.patch.object(self.session.journals, "fetch") as mock_fetch:
            JournalStub = mock.Mock(spec=domain.Journal)
            JournalStub.remove_ahead_of_print_bundle = mock.Mock()
            mock_fetch.return_value = JournalStub
            with mock.patch.object(self.session, "notify") as mock_notify:
                self.command(id="0034-8910-rsp")
                mock_notify.assert_called_once_with(
                    services.Events.AHEAD_OF_PRINT_BUNDLE_REMOVED_FROM_JOURNAL,
                    {
                        "journal": JournalStub,
                        "id": "0034-8910-rsp",
                    },
                )


class FetchJournalTest(unittest.TestCase):
    def setUp(self):
        self.services, self.session = make_services()
        self.command = self.services.get("fetch_journal")
        create_journal_command = self.services.get("create_journal")
        create_journal_command(id="1678-4596-cr-49-02")

    def test_assert_command_interface_exists(self):
        self.assertIsNotNone(self.command)
        self.assertTrue(callable(self.command))

    def test_should_raise_does_not_exists_exception(self):
        self.assertRaises(
            exceptions.DoesNotExist, self.command, id="1678-4596-cr-49-03"
        )

    def test_should_return_a_journal(self):
        self.assertIsNotNone(self.command(id="1678-4596-cr-49-02"))

    def test_should_require_an_id(self):
        self.assertRaises(TypeError, self.command)
