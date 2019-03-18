import unittest
from unittest import mock
import datetime

from documentstore import services, exceptions, domain

from . import apptesting


def make_services():
    session = apptesting.Session()
    return services.get_handlers(lambda: session), session


class CommandTestMixin:
    SUBSCRIBERS_EVENTS = [subscriber[0] for subscriber in services.DEFAULT_SUBSCRIBERS]

    def test_command_interface(self):
        self.assertIsNotNone(self.command)
        self.assertTrue(callable(self.command))


class CreateDocumentsBundleTest(CommandTestMixin, unittest.TestCase):
    def setUp(self):
        self.services, self.session = make_services()
        self.command = self.services.get("create_documents_bundle")
        self.event = services.Events.DOCUMENTSBUNDLE_CREATED

    def test_event(self):
        self.assertIn(self.event, self.SUBSCRIBERS_EVENTS)

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
                self.event,
                {
                    "id": "xpto",
                    "docs": ["/document/1"],
                    "metadata": None,
                    "bundle": mock.ANY,
                },
            )


class FetchDocumentsBundleTest(CommandTestMixin, unittest.TestCase):
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
            result["metadata"], {"publication_year": "2018", "volume": "2"}
        )

    def test_command_with_unexpected_metadata(self):
        self.services["create_documents_bundle"](
            id="xpto",
            metadata={"publication_year": "2018", "volume": "2", "unknown": "0"},
        )
        result = self.command(id="xpto")
        self.assertEqual(
            result["metadata"], {"publication_year": "2018", "volume": "2"}
        )


class UpdateDocumentsBundleTest(CommandTestMixin, unittest.TestCase):
    def setUp(self):
        self.services, self.session = make_services()
        self.command = self.services.get("update_documents_bundle_metadata")
        self.event = services.Events.DOCUMENTSBUNDLE_METATADA_UPDATED

        datetime_patcher = mock.patch.object(
            domain, "datetime", mock.Mock(wraps=datetime.datetime)
        )
        mocked_datetime = datetime_patcher.start()
        mocked_datetime.utcnow.return_value = datetime.datetime(
            2018, 8, 5, 22, 33, 49, 795151
        )
        self.addCleanup(datetime_patcher.stop)

    def test_event(self):
        self.assertIn(self.event, self.SUBSCRIBERS_EVENTS)

    def test_command_raises_exception_if_does_not_exist(self):
        self.assertRaises(exceptions.DoesNotExist, self.command, id="xpto", metadata={})

    def test_command_success(self):
        self.services["create_documents_bundle"](
            id="xpto", metadata={"publication_year": "2018", "volume": "2"}
        )
        self.command(id="xpto", metadata={"publication_year": "2019"})
        result = self.services["fetch_documents_bundle"](id="xpto")
        self.assertEqual(
            result["metadata"], {"publication_year": "2019", "volume": "2"}
        )

    def test_command_with_unexpected_metadata(self):
        self.services["create_documents_bundle"](
            id="xpto", metadata={"publication_year": "2018", "volume": "2"}
        )
        self.command(id="xpto", metadata={"unknown": "0"})
        result = self.services["fetch_documents_bundle"](id="xpto")
        self.assertEqual(
            result["metadata"], {"publication_year": "2018", "volume": "2"}
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
        self.assertEqual(result["metadata"], {"publication_year": "2018", "volume": ""})

    def test_command_notify_event(self):
        self.services["create_documents_bundle"](
            id="xpto", metadata={"publication_year": "2018", "volume": "2"}
        )
        with mock.patch.object(self.session, "notify") as mock_notify:
            self.command(id="xpto", metadata={"publication_year": "2019"})
            mock_notify.assert_called_once_with(
                self.event,
                {
                    "id": "xpto",
                    "metadata": {"publication_year": "2019"},
                    "bundle": mock.ANY,
                },
            )


class AddDocumentToDocumentsBundleTest(CommandTestMixin, unittest.TestCase):
    def setUp(self):
        self.services, self.session = make_services()
        self.command = self.services.get("add_document_to_documents_bundle")
        self.event = services.Events.DOCUMENT_ADDED_TO_DOCUMENTSBUNDLE

    def test_event(self):
        self.assertIn(self.event, self.SUBSCRIBERS_EVENTS)

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
                self.event, {"id": "xpto", "doc": "/document/1", "bundle": mock.ANY}
            )


class InsertDocumentToDocumentsBundleTest(CommandTestMixin, unittest.TestCase):
    def setUp(self):
        self.services, self.session = make_services()
        self.command = self.services.get("insert_document_to_documents_bundle")
        self.event = services.Events.DOCUMENT_INSERTED_TO_DOCUMENTSBUNDLE

    def test_event(self):
        self.assertIn(self.event, self.SUBSCRIBERS_EVENTS)

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
                self.event,
                {"id": "xpto", "doc": "/document/3", "index": 10, "bundle": mock.ANY},
            )


class CreateJournalTest(CommandTestMixin, unittest.TestCase):
    def setUp(self):
        self.services, self.session = make_services()
        self.command = self.services.get("create_journal")
        self.event = services.Events.JOURNAL_CREATED

    def test_event(self):
        self.assertIn(self.event, self.SUBSCRIBERS_EVENTS)

    def test_command_success(self):
        self.assertIsNone(self.command(id="xpto"))

    def test_command_with_metadata_success(self):
        self.assertIsNone(
            self.command(
                id="xpto",
                metadata={
                    "title": "Journal Title",
                    "mission": [
                        {"language": "pt", "value": "Missão do Periódico"},
                        {"language": "en", "value": "Journal Mission"},
                    ],
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
                self.event, {"id": "jxpto", "journal": mock.ANY, "metadata": None}
            )


class AddIssueToJournalTest(CommandTestMixin, unittest.TestCase):
    def setUp(self):
        self.services, self.session = make_services()
        self.command = self.services.get("add_issue_to_journal")
        self.event = services.Events.ISSUE_ADDED_TO_JOURNAL
        create_journal_command = self.services.get("create_journal")
        create_journal_command(id="0034-8910-rsp")

    def test_event(self):
        self.assertIn(self.event, self.SUBSCRIBERS_EVENTS)

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
                    self.event,
                    {
                        "journal": JournalStub,
                        "id": "0034-8910-rsp",
                        "issue": "0034-8910-rsp-48-2",
                    },
                )


class InsertIssueToJournalTest(CommandTestMixin, unittest.TestCase):
    def setUp(self):
        self.services, self.session = make_services()
        self.command = self.services.get("insert_issue_to_journal")
        self.event = services.Events.ISSUE_INSERTED_TO_JOURNAL
        create_journal_command = self.services.get("create_journal")
        create_journal_command(id="0034-8910-rsp")

    def test_event(self):
        self.assertIn(self.event, self.SUBSCRIBERS_EVENTS)

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
                    self.event,
                    {
                        "journal": JournalStub,
                        "id": "0034-8910-rsp",
                        "index": 0,
                        "issue": "0034-8910-rsp-48-2",
                    },
                )


class RemoveIssueFromJournalTest(CommandTestMixin, unittest.TestCase):
    def setUp(self):
        self.services, self.session = make_services()
        self.command = self.services.get("remove_issue_from_journal")
        self.event = services.Events.ISSUE_REMOVED_FROM_JOURNAL
        create_journal_command = self.services.get("create_journal")
        create_journal_command(id="0034-8910-rsp")

    def test_event(self):
        self.assertIn(self.event, self.SUBSCRIBERS_EVENTS)

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
                    self.event,
                    {
                        "journal": JournalStub,
                        "id": "0034-8910-rsp",
                        "issue": "0034-8910-rsp-48-2",
                    },
                )


class SetAheadOfPrintBundleToJournalTest(CommandTestMixin, unittest.TestCase):
    def setUp(self):
        self.services, self.session = make_services()
        self.command = self.services.get("set_ahead_of_print_bundle_to_journal")
        self.event = services.Events.AHEAD_OF_PRINT_BUNDLE_SET_TO_JOURNAL
        create_journal_command = self.services.get("create_journal")
        create_journal_command(id="0034-8910-rsp")

    def test_event(self):
        self.assertIn(self.event, self.SUBSCRIBERS_EVENTS)

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
            self.assertEqual(JournalStub.ahead_of_print_bundle, "0034-8910-rsp-aop")

    def test_command_update_journals(self):
        with mock.patch.object(self.session.journals, "fetch") as mock_fetch:
            JournalStub = mock.Mock(spec=domain.Journal)
            JournalStub.ahead_of_print_bundle = mock.Mock()
            mock_fetch.return_value = JournalStub
            with mock.patch.object(self.session.journals, "update") as mock_update:
                self.command(id="0034-8910-rsp", aop="0034-8910-rsp-aop")
                mock_update.assert_called_once_with(JournalStub)

    def test_command_success(self):
        self.assertIsNone(self.command(id="0034-8910-rsp", aop="0034-8910-rsp-aop"))

    def test_command_notify_event(self):
        with mock.patch.object(self.session.journals, "fetch") as mock_fetch:
            JournalStub = mock.Mock(spec=domain.Journal)
            JournalStub.ahead_of_print_bundle = mock.Mock()
            mock_fetch.return_value = JournalStub
            with mock.patch.object(self.session, "notify") as mock_notify:
                self.command(id="0034-8910-rsp", aop="0034-8910-rsp-aop")
                mock_notify.assert_called_once_with(
                    self.event,
                    {
                        "journal": JournalStub,
                        "id": "0034-8910-rsp",
                        "aop": "0034-8910-rsp-aop",
                    },
                )


class RemoveAheadOfPrintBundleFromJournalTest(CommandTestMixin, unittest.TestCase):
    def setUp(self):
        self.services, self.session = make_services()
        self.command = self.services.get("remove_ahead_of_print_bundle_from_journal")
        self.event = services.Events.AHEAD_OF_PRINT_BUNDLE_REMOVED_FROM_JOURNAL
        create_journal_command = self.services.get("create_journal")
        create_journal_command(id="0034-8910-rsp")

    def test_event(self):
        self.assertIn(self.event, self.SUBSCRIBERS_EVENTS)

    def test_command_raises_exception_if_journal_does_not_exist(self):
        self.assertRaises(exceptions.DoesNotExist, self.command, id="0101-8910-csp")

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
        self.assertRaises(exceptions.DoesNotExist, self.command, id="0034-8910-rsp")

    def test_command_notify_event(self):
        with mock.patch.object(self.session.journals, "fetch") as mock_fetch:
            JournalStub = mock.Mock(spec=domain.Journal)
            JournalStub.remove_ahead_of_print_bundle = mock.Mock()
            mock_fetch.return_value = JournalStub
            with mock.patch.object(self.session, "notify") as mock_notify:
                self.command(id="0034-8910-rsp")
                mock_notify.assert_called_once_with(
                    self.event, {"journal": JournalStub, "id": "0034-8910-rsp"}
                )


class FetchJournalTest(CommandTestMixin, unittest.TestCase):
    def setUp(self):
        self.services, self.session = make_services()
        self.command = self.services.get("fetch_journal")
        create_journal_command = self.services.get("create_journal")
        create_journal_command(id="1678-4596-cr-49-02")

    def test_should_raise_does_not_exists_exception(self):
        self.assertRaises(
            exceptions.DoesNotExist, self.command, id="1678-4596-cr-49-03"
        )

    def test_should_return_a_journal(self):
        self.assertIsNotNone(self.command(id="1678-4596-cr-49-02"))

    def test_should_require_an_id(self):
        self.assertRaises(TypeError, self.command)


class UpdateJornalMetadataTest(CommandTestMixin, unittest.TestCase):
    def setUp(self):
        self.services, self.session = make_services()
        self.command = self.services.get("update_journal_metadata")
        self.event = services.Events.JOURNAL_METATADA_UPDATED
        self.services["create_journal"](
            id="1678-4596-cr",
            metadata={
                "title": "Journal Title",
                "mission": [
                    {"language": "pt", "value": "Missão do Periódico"},
                    {"language": "en", "value": "Journal Mission"},
                ],
            },
        )

    def test_event(self):
        self.assertIn(self.event, self.SUBSCRIBERS_EVENTS)

    def test_command_raises_exception_if_does_not_exist(self):
        self.session.journals.fetch = mock.Mock(side_effect=exceptions.DoesNotExist)
        self.assertRaises(
            exceptions.DoesNotExist, self.command, id="1678-4596-cr", metadata={}
        )

    def test_command_success(self):
        self.command(
            id="1678-4596-cr",
            metadata={
                "title": "Journal New Title",
                "mission": [
                    {"language": "pt", "value": "Missão do Periódico"},
                    {"language": "en", "value": "Journal Mission"},
                    {"language": "es", "value": "Misión de la Revista"},
                ],
            },
        )
        result = self.services["fetch_journal"](id="1678-4596-cr")
        self.assertEqual(
            result["metadata"],
            {
                "title": "Journal New Title",
                "mission": [
                    {"language": "pt", "value": "Missão do Periódico"},
                    {"language": "en", "value": "Journal Mission"},
                    {"language": "es", "value": "Misión de la Revista"},
                ],
            },
        )

    def test_command_with_unexpected_metadata(self):
        self.command(
            id="1678-4596-cr",
            metadata={
                "unknown": "0",
                "title": "Journal New Title",
                "title_iso": "Title ISO",
            },
        )
        result = self.services["fetch_journal"](id="1678-4596-cr")
        self.assertEqual(
            result["metadata"],
            {
                "title": "Journal New Title",
                "mission": [
                    {"language": "pt", "value": "Missão do Periódico"},
                    {"language": "en", "value": "Journal Mission"},
                ],
                "title_iso": "Title ISO",
            },
        )

    def test_command_remove_metadata(self):
        """
        Por ora, a maneira de remover um metadado é através da atribuição de uma
        string vazia para o mesmo. Note que este procedimento não removerá o metadado
        do manifesto.
        """
        self.command(id="1678-4596-cr", metadata={"title": ""})
        result = self.services["fetch_journal"](id="1678-4596-cr")
        self.assertEqual(
            result["metadata"],
            {
                "title": "",
                "mission": [
                    {"language": "pt", "value": "Missão do Periódico"},
                    {"language": "en", "value": "Journal Mission"},
                ],
            },
        )

    def test_command_notify_event(self):
        metadata = {
            "title": "Journal New Title",
            "mission": [
                {"language": "pt", "value": "Missão do Periódico"},
                {"language": "en", "value": "Journal Mission"},
                {"language": "es", "value": "Misión de la Revista"},
            ],
        }
        with mock.patch.object(self.session, "notify") as mock_notify:
            self.command(id="1678-4596-cr", metadata=metadata)
            mock_notify.assert_called_once_with(
                self.event,
                {"id": "1678-4596-cr", "metadata": metadata, "journal": mock.ANY},
            )
