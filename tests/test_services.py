import os
import unittest
from unittest import mock
import datetime
import random

from bson.objectid import ObjectId
from documentstore import services, exceptions, domain

from . import apptesting


def make_services():
    session = apptesting.Session()
    return services.get_handlers(lambda: session, subscribers=[]), session


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
        self.assertIsNone(
            self.command(id="xpto", docs=[{"id": "/document/1"}, {"id": "/document/2"}])
        )

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
            self.command(id="xpto", docs=[{"id": "/document/1"}])
            mock_notify.assert_called_once_with(
                self.event,
                {
                    "id": "xpto",
                    "docs": [{"id": "/document/1"}],
                    "metadata": None,
                    "instance": mock.ANY,
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
            id="xpto", docs=[{"id": "/document/1"}, {"id": "/document/2"}]
        )
        result = self.command(id="xpto")
        self.assertEqual(
            result["items"], [{"id": "/document/1"}, {"id": "/document/2"}]
        )

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
        mocked_datetime.utcnow.side_effect = lambda: (
            datetime.datetime(2018, 8, 5, 22, 33, 49, random.randint(1, 1000000))
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
                    "instance": mock.ANY,
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
        self.command(id="xpto", doc={"id": "/document/1"})
        result = self.services["fetch_documents_bundle"](id="xpto")
        self.assertEqual(result["items"], [{"id": "/document/1"}])
        self.command(id="xpto", doc={"id": "/document/2"})
        result = self.services["fetch_documents_bundle"](id="xpto")
        self.assertEqual(
            result["items"], [{"id": "/document/1"}, {"id": "/document/2"}]
        )

    def test_command_raises_exception_if_already_exists(self):
        self.services["create_documents_bundle"](
            id="xpto", docs=[{"id": "/document/1"}]
        )
        self.assertRaises(
            exceptions.AlreadyExists, self.command, id="xpto", doc={"id": "/document/1"}
        )

    def test_command_notify_event(self):
        self.services["create_documents_bundle"](id="xpto")
        with mock.patch.object(self.session, "notify") as mock_notify:
            self.command(id="xpto", doc={"id": "/document/1"})
            mock_notify.assert_called_once_with(
                self.event,
                {"id": "xpto", "doc": {"id": "/document/1"}, "instance": mock.ANY},
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
            exceptions.DoesNotExist,
            self.command,
            id="xpto",
            index=0,
            doc={"id": "/document/1"},
        )

    def test_command_success(self):
        self.services["create_documents_bundle"](id="xpto")
        self.command(id="xpto", index=1, doc={"id": "/document/1"})
        result = self.services["fetch_documents_bundle"](id="xpto")
        self.assertEqual(result["items"], [{"id": "/document/1"}])
        self.command(id="xpto", index=0, doc={"id": "/document/2"})
        result = self.services["fetch_documents_bundle"](id="xpto")
        self.assertEqual(
            result["items"], [{"id": "/document/2"}, {"id": "/document/1"}]
        )
        self.command(id="xpto", index=10, doc={"id": "/document/3"})
        result = self.services["fetch_documents_bundle"](id="xpto")
        self.assertEqual(
            result["items"],
            [{"id": "/document/2"}, {"id": "/document/1"}, {"id": "/document/3"}],
        )

    def test_command_raises_exception_if_already_exists(self):
        self.services["create_documents_bundle"](
            id="xpto", docs=[{"id": "/document/1"}, {"id": "/document/2"}]
        )
        self.assertRaises(
            exceptions.AlreadyExists,
            self.command,
            id="xpto",
            index=0,
            doc={"id": "/document/1"},
        )
        self.assertRaises(
            exceptions.AlreadyExists,
            self.command,
            id="xpto",
            index=1,
            doc={"id": "/document/1"},
        )

    def test_command_notify_event(self):
        self.services["create_documents_bundle"](id="xpto")
        with mock.patch.object(self.session, "notify") as mock_notify:
            self.command(id="xpto", index=10, doc={"id": "/document/3"})
            mock_notify.assert_called_once_with(
                self.event,
                {
                    "id": "xpto",
                    "doc": {"id": "/document/3"},
                    "index": 10,
                    "instance": mock.ANY,
                },
            )


class UpdateDocumentInDocumentsBundleTest(CommandTestMixin, unittest.TestCase):
    def setUp(self):
        self.services, self.session = make_services()
        self.command = self.services.get("update_documents_in_documents_bundle")
        self.event = services.Events.ISSUE_DOCUMENTS_UPDATED
        create_documents_bundle_command = self.services.get("create_documents_bundle")
        create_documents_bundle_command(id="issue-example-id")

    def test_event(self):
        self.assertIn(self.event, self.SUBSCRIBERS_EVENTS)

    def test_raises_does_not_exists_if_journal_not_found(self):
        self.assertRaises(
            exceptions.DoesNotExist, self.command, id="not-found-issue", docs=[]
        )

    def test_issues_list_should_be_updated(self):
        with mock.patch.object(self.session.documents_bundles, "fetch") as mock_fetch:
            DocumentsBundleStub = mock.Mock(spec=domain.DocumentsBundle)
            DocumentsBundleStub.documents = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
            DocumentsBundleStub.add_document = mock.Mock()
            DocumentsBundleStub.remove_document = mock.Mock()
            mock_fetch.return_value = DocumentsBundleStub

            self.command(id="issue-example-id", docs=["d"])
            DocumentsBundleStub.remove_document.assert_has_calls(
                [mock.call("a"), mock.call("b"), mock.call("c")]
            )
            DocumentsBundleStub.add_document.assert_called_once_with("d")

    def test_raises_already_exists_if_duplicated_are_in_list(self):
        self.assertRaises(
            exceptions.AlreadyExists,
            self.command,
            id="issue-example-id",
            docs=[{"id": "a"}, {"id": "a"}, {"id": "b"}, {"id": "a"}, {"id": "b"}],
        )

    def test_should_call_update_issue(self):
        with mock.patch.object(self.session.documents_bundles, "update") as mock_update:
            self.command(id="issue-example-id", docs=[{"id": "a"}])
            mock_update.assert_called_once()

    def test_should_empty_bundle_document(self):
        with mock.patch.object(self.session.documents_bundles, "fetch") as mock_fetch:
            DocumentsBundleStub = mock.Mock(spec=domain.DocumentsBundle)
            DocumentsBundleStub.documents = [{"id": "a"}]
            DocumentsBundleStub.add_document = mock.Mock()
            DocumentsBundleStub.remove_document = mock.Mock()
            mock_fetch.return_value = DocumentsBundleStub

            self.command(id="issue-example-id", docs=[])
            DocumentsBundleStub.remove_document.assert_has_calls([mock.call("a")])
            DocumentsBundleStub.add_document.assert_not_called()

    def test_command_notify_event(self):
        with mock.patch.object(self.session.documents_bundles, "fetch") as mock_fetch:
            DocumentsBundleStub = mock.Mock(spec=domain.DocumentsBundle)
            DocumentsBundleStub.documents = []
            mock_fetch.return_value = DocumentsBundleStub

            with mock.patch.object(self.session, "notify") as mock_notify:
                self.command(id="issue-example-id", docs=[{"id": "a"}])
                mock_notify.assert_called_once_with(
                    self.event,
                    {
                        "instance": DocumentsBundleStub,
                        "id": "issue-example-id",
                        "docs": [{"id": "a"}],
                    },
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
                self.event, {"id": "jxpto", "instance": mock.ANY, "metadata": None}
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
            self.command(id="0034-8910-rsp", issue={"id": "0034-8910-rsp-48-2"})
            JournalStub.add_issue.assert_called_once_with({"id": "0034-8910-rsp-48-2"})

    def test_command_update_journals(self):
        with mock.patch.object(self.session.journals, "fetch") as mock_fetch:
            JournalStub = mock.Mock(spec=domain.Journal)
            JournalStub.add_issue = mock.Mock()
            mock_fetch.return_value = JournalStub
            with mock.patch.object(self.session.journals, "update") as mock_update:
                self.command(id="0034-8910-rsp", issue={"id": "0034-8910-rsp-48-2"})
                mock_update.assert_called_once_with(JournalStub)

    def test_command_success(self):
        self.assertIsNone(
            self.command(id="0034-8910-rsp", issue={"id": "0034-8910-rsp-48-2"})
        )

    def test_command_raises_exception_if_journal_does_not_exist(self):
        self.assertRaises(
            exceptions.DoesNotExist,
            self.command,
            id="0101-8910-csp",
            issue="0101-8910-csp-48-2",
        )

    def test_command_raises_exception_if_issue_already_exists(self):
        self.command(id="0034-8910-rsp", issue={"id": "0034-8910-rsp-48-2"})
        self.assertRaises(
            exceptions.AlreadyExists,
            self.command,
            id="0034-8910-rsp",
            issue={"id": "0034-8910-rsp-48-2"},
        )

    def test_command_notify_event(self):
        with mock.patch.object(self.session.journals, "fetch") as mock_fetch:
            JournalStub = mock.Mock(spec=domain.Journal)
            JournalStub.insert_issue = mock.Mock()
            mock_fetch.return_value = JournalStub
            with mock.patch.object(self.session, "notify") as mock_notify:
                self.command(id="0034-8910-rsp", issue={"id": "0034-8910-rsp-48-2"})
                mock_notify.assert_called_once_with(
                    self.event,
                    {
                        "instance": JournalStub,
                        "id": "0034-8910-rsp",
                        "issue": {"id": "0034-8910-rsp-48-2"},
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
            issue={"id": "0101-8910-csp-48-2"},
        )

    def test_command_calls_insert_issue(self):
        with mock.patch.object(self.session.journals, "fetch") as mock_fetch:
            JournalStub = mock.Mock(spec=domain.Journal)
            JournalStub.insert_issue = mock.Mock()
            mock_fetch.return_value = JournalStub
            self.command(
                id="0034-8910-rsp", index=0, issue={"id": "0034-8910-rsp-48-2"}
            )
            JournalStub.insert_issue.assert_called_once_with(
                0, {"id": "0034-8910-rsp-48-2"}
            )

    def test_command_update_journals(self):
        with mock.patch.object(self.session.journals, "fetch") as mock_fetch:
            JournalStub = mock.Mock(spec=domain.Journal)
            JournalStub.insert_issue = mock.Mock()
            mock_fetch.return_value = JournalStub
            with mock.patch.object(self.session.journals, "update") as mock_update:
                self.command(
                    id="0034-8910-rsp", index=0, issue={"id": "0034-8910-rsp-48-2"}
                )
                mock_update.assert_called_once_with(JournalStub)

    def test_command_success(self):
        self.assertIsNone(
            self.command(
                id="0034-8910-rsp", index=0, issue={"id": "0034-8910-rsp-48-2"}
            )
        )
        self.assertIsNone(
            self.command(
                id="0034-8910-rsp", index=10, issue={"id": "0034-8910-rsp-48-3"}
            )
        )
        self.assertIsNone(
            self.command(
                id="0034-8910-rsp", index=-1, issue={"id": "0034-8910-rsp-48-4"}
            )
        )

    def test_command_raises_exception_if_issue_already_exists(self):
        self.command(id="0034-8910-rsp", index=0, issue={"id": "0034-8910-rsp-48-2"})
        self.assertRaises(
            exceptions.AlreadyExists,
            self.command,
            id="0034-8910-rsp",
            index=0,
            issue={"id": "0034-8910-rsp-48-2"},
        )
        self.assertRaises(
            exceptions.AlreadyExists,
            self.command,
            id="0034-8910-rsp",
            index=5,
            issue={"id": "0034-8910-rsp-48-2"},
        )

    def test_command_notify_event(self):
        with mock.patch.object(self.session.journals, "fetch") as mock_fetch:
            JournalStub = mock.Mock(spec=domain.Journal)
            JournalStub.insert_issue = mock.Mock()
            mock_fetch.return_value = JournalStub
            with mock.patch.object(self.session, "notify") as mock_notify:
                self.command(
                    id="0034-8910-rsp", index=0, issue={"id": "0034-8910-rsp-48-2"}
                )
                mock_notify.assert_called_once_with(
                    self.event,
                    {
                        "instance": JournalStub,
                        "id": "0034-8910-rsp",
                        "index": 0,
                        "issue": {"id": "0034-8910-rsp-48-2"},
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
            id="0034-8910-rsp", issue={"id": "0034-8910-rsp-48-2"}
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
                        "instance": JournalStub,
                        "id": "0034-8910-rsp",
                        "issue": "0034-8910-rsp-48-2",
                    },
                )


class UpdateIssuesInJournalTest(CommandTestMixin, unittest.TestCase):
    def setUp(self):
        self.services, self.session = make_services()
        self.command = self.services.get("update_issues_in_journal")
        self.event = services.Events.JOURNAL_ISSUES_UPDATED
        create_journal_command = self.services.get("create_journal")
        create_journal_command(id="journal-example-id")

    def test_event(self):
        self.assertIn(self.event, self.SUBSCRIBERS_EVENTS)

    def test_raises_does_not_exists_if_journal_not_found(self):
        self.assertRaises(
            exceptions.DoesNotExist, self.command, id="not-found-journal", issues=[]
        )

    def test_issues_list_should_be_updated(self):
        with mock.patch.object(self.session.journals, "fetch") as mock_fetch:
            JournalStub = mock.Mock(spec=domain.Journal)
            JournalStub.issues = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
            JournalStub.add_issue = mock.Mock()
            JournalStub.remove_issue = mock.Mock()
            mock_fetch.return_value = JournalStub

            self.command(id="journal-example-id", issues=["d"])
            JournalStub.remove_issue.assert_has_calls(
                [mock.call("a"), mock.call("b"), mock.call("c")]
            )
            JournalStub.add_issue.assert_called_once_with("d")

    def test_raises_already_exists_if_duplicated_are_in_list(self):
        self.assertRaises(
            exceptions.AlreadyExists,
            self.command,
            id="journal-example-id",
            issues=[{"id": "a"}, {"id": "a"}, {"id": "b"}, {"id": "a"}, {"id": "b"}],
        )

    def test_should_call_update_journal(self):
        with mock.patch.object(self.session.journals, "update") as mock_update:
            self.command(id="journal-example-id", issues=[{"id": "a"}])
            mock_update.assert_called_once()

    def test_should_empty_journal_issues(self):
        with mock.patch.object(self.session.journals, "fetch") as mock_fetch:
            JournalStub = mock.Mock(spec=domain.Journal)
            JournalStub.issues = [{"id": "a"}]
            JournalStub.add_issue = mock.Mock()
            JournalStub.remove_issue = mock.Mock()
            mock_fetch.return_value = JournalStub

            self.command(id="journal-example-id", issues=[])
            JournalStub.remove_issue.assert_has_calls([mock.call("a")])
            JournalStub.add_issue.assert_not_called()

    def test_command_notify_event(self):
        with mock.patch.object(self.session.journals, "fetch") as mock_fetch:
            JournalStub = mock.Mock(spec=domain.Journal)
            JournalStub.issues = []
            mock_fetch.return_value = JournalStub

            with mock.patch.object(self.session, "notify") as mock_notify:
                self.command(id="journal-example-id", issues=[{"id": "a"}])
                mock_notify.assert_called_once_with(
                    self.event,
                    {
                        "instance": JournalStub,
                        "id": "journal-example-id",
                        "issues": [{"id": "a"}],
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
                        "instance": JournalStub,
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
                    self.event, {"instance": JournalStub, "id": "0034-8910-rsp"}
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
                {"id": "1678-4596-cr", "metadata": metadata, "instance": mock.ANY},
            )


class RegisterRenditionVersionTest(CommandTestMixin, unittest.TestCase):
    def setUp(self):
        self.services, self.session = make_services()
        self.command = self.services["register_rendition_version"]
        self.event = services.Events.RENDITION_VERSION_REGISTERED
        self.document = domain.Document(manifest=apptesting.manifest_data_fixture())
        self.session.documents.add(self.document)

    def test_register_rendition_version_returns_none(self):
        self.assertIsNone(
            self.command(
                self.document.id(),
                "0034-8910-rsp-48-2-0275-pt.pdf",
                "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275-pt.pdf",
                "application/pdf",
                "pt",
                23456,
            )
        )

    def test_register_duplicated_rendition_version_raises_error(self):
        self.command(
            self.document.id(),
            "0034-8910-rsp-48-2-0275-pt.pdf",
            "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275-pt.pdf",
            "application/pdf",
            "pt",
            23456,
        )
        self.assertRaises(
            exceptions.VersionAlreadySet,
            self.command,
            self.document.id(),
            "0034-8910-rsp-48-2-0275-pt.pdf",
            "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275-pt.pdf",
            "application/pdf",
            "pt",
            23456,
        )

    def test_register_new_rendition_version(self):
        """Qualquer diferença em qualquer campo é suficiente para que seja
        considerada uma nova versão válida.
        """
        self.command(
            self.document.id(),
            "0034-8910-rsp-48-2-0275-pt.pdf",
            "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275-pt.pdf",
            "application/pdf",
            "pt",
            23456,
        )
        self.assertIsNone(
            self.command(
                self.document.id(),
                "0034-8910-rsp-48-2-0275-pt.pdf",
                "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275-pt-v2.pdf",
                "application/pdf",
                "pt",
                23456,
            )
        )

    def test_command_notify_event(self):
        with mock.patch.object(self.session, "notify") as mock_notify:
            self.command(
                self.document.id(),
                "0034-8910-rsp-48-2-0275-pt.pdf",
                "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275-pt.pdf",
                "application/pdf",
                "pt",
                23456,
            )
            mock_notify.assert_called_once_with(
                self.event,
                {
                    "instance": mock.ANY,
                    "id": self.document.id(),
                    "filename": "0034-8910-rsp-48-2-0275-pt.pdf",
                    "data_url": "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275-pt.pdf",
                    "mimetype": "application/pdf",
                    "lang": "pt",
                    "size_bytes": 23456,
                },
            )


class FetchDocumentRenditionsTest(CommandTestMixin, unittest.TestCase):
    def setUp(self):
        self.services, self.session = make_services()
        self.command = self.services["fetch_document_renditions"]
        self.document = domain.Document(manifest=apptesting.manifest_data_fixture())
        self.session.documents.add(self.document)

    def test_fetch_rendition(self):
        self.services["register_rendition_version"](
            self.document.id(),
            "0034-8910-rsp-48-2-0275-pt.pdf",
            "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275-pt.pdf",
            "application/pdf",
            "pt",
            23456,
        )
        renditions = self.command(self.document.id())
        self.assertEqual(len(renditions), 1)
        self.assertEqual(
            renditions[0]["url"],
            "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275-pt.pdf",
        )

    def test_fetch_latest_version(self):
        self.services["register_rendition_version"](
            self.document.id(),
            "0034-8910-rsp-48-2-0275-pt.pdf",
            "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275-pt.pdf",
            "application/pdf",
            "pt",
            23456,
        )
        self.services["register_rendition_version"](
            self.document.id(),
            "0034-8910-rsp-48-2-0275-pt.pdf",
            "/rawfiles/8ca9f9c1397cc/0035-8910-rsp-48-2-0275-pt.pdf",
            "application/pdf",
            "pt",
            234567,
        )
        renditions = self.command(self.document.id())
        self.assertEqual(len(renditions), 1)
        self.assertEqual(
            renditions[0]["url"],
            "/rawfiles/8ca9f9c1397cc/0035-8910-rsp-48-2-0275-pt.pdf",
        )

    def test_fetch_version_at(self):
        self.services["register_rendition_version"](
            self.document.id(),
            "0034-8910-rsp-48-2-0275-pt.pdf",
            "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275-pt.pdf",
            "application/pdf",
            "pt",
            23456,
        )

        now = services.utcnow()[:-8] + "Z"  # em segundos

        datetime_patcher = mock.patch.object(
            domain, "datetime", mock.Mock(wraps=datetime.datetime)
        )
        mocked_datetime = datetime_patcher.start()
        # faz com que o timestamp da próxima versão seja do próximo ano
        mocked_datetime.utcnow.return_value = datetime.datetime(
            datetime.date.today().year + 1, 8, 5, 22, 34, 49, 795151
        )
        self.addCleanup(datetime_patcher.stop)

        self.services["register_rendition_version"](
            self.document.id(),
            "0034-8910-rsp-48-2-0275-pt.pdf",
            "/rawfiles/8ca9f9c1397cc/0035-8910-rsp-48-2-0275-pt.pdf",
            "application/pdf",
            "pt",
            234567,
        )
        renditions = self.command(self.document.id(), version_at=now)
        self.assertEqual(len(renditions), 1)
        self.assertEqual(
            renditions[0]["url"],
            "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275-pt.pdf",
        )


class DeleteDocumentTest(CommandTestMixin, unittest.TestCase):
    def setUp(self):
        self.services, self.session = make_services()
        self.command = self.services["delete_document"]
        self.document = domain.Document(manifest=apptesting.manifest_data_fixture())
        self.session.documents.add(self.document)
        self.event = services.Events.DOCUMENT_DELETED

    def test_delete_document_returns_none(self):
        self.assertIsNone(self.command(self.document.id()))

    def test_raises_when_document_does_not_exist(self):
        self.assertRaises(
            exceptions.DoesNotExist, self.command, "inexistent-document-id"
        )

    def test_command_notify_event(self):
        with mock.patch.object(self.session, "notify") as mock_notify:
            self.command(self.document.id())
            mock_notify.assert_called_once_with(
                self.event, {"instance": mock.ANY, "id": self.document.id()}
            )


class FetchChangeTest(CommandTestMixin, unittest.TestCase):
    def setUp(self):
        self.services, self.session = make_services()
        self.change_id = str(ObjectId())
        self.session.changes.add(
            {
                "_id": self.change_id,
                "timestamp": "2018-08-05T23:08:50.331687Z",
                "entity": "Document",
                "id": "S0034-89102014000200347",
                "content_gz": '{"hello": "world"}',
                "content_type": "application/json",
            }
        )

        self.command = self.services.get("fetch_change")

    def test_should_raise_does_not_exists_exception(self):
        self.assertRaises(exceptions.DoesNotExist, self.command, id="missing-change")

    def test_should_return_a_change(self):
        self.assertIsNotNone(self.command(id=self.change_id))

    def test_should_require_an_id(self):
        self.assertRaises(TypeError, self.command)


class RegisterDocumentVersionTest(CommandTestMixin, unittest.TestCase):
    def setUp(self):
        self.services, self.session = make_services()
        self.manifest = {
            "id": "0034-8910-rsp-48-2-0347",
            "versions": [
                {
                    "data": "https://url.to/0034-8910-rsp-48-2-0347.xml",
                    "assets": {
                        "0034-8910-rsp-48-2-0347-gf01": [
                            [
                                "2018-08-05T23:03:44.971230Z",
                                "http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf01.jpg",
                            ],
                        ],
                    },
                    "renditions": [],
                },
            ],
        }
        self.doc = domain.Document(manifest=self.manifest)
        self.session.documents.add(self.doc)
        self.command = self.services["register_document_version"]

    def test_swollows_VersionAlreadySet_exception_for_assets(self):
        with mock.patch("documentstore.domain.requests.get") as mock_request:
            with open(
                os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "0034-8910-rsp-48-2-0347.xml",
                )
            ) as fixture:
                mock_request.return_value.content = fixture.read().encode("utf-8")

            assets = self.doc.version()["assets"]
            self.assertIsNone(
                self.command(
                    id=self.doc.id(),
                    data_url="https://url.to.new/0034-8910-rsp-48-2-0347.xml",
                    assets=assets,
                )
            )
