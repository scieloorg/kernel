import os
import unittest
from unittest.mock import patch
from pyramid import testing
from pyramid.httpexceptions import HTTPNotFound, HTTPCreated, HTTPNoContent

from documentstore import services, restfulapi
from . import apptesting

_CWD = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_CWD, "0034-8910-rsp-48-2-0347.xml"), "rb") as f:
    SAMPLE_DOCUMENT_DATA = f.read()


def make_request():
    request = testing.DummyRequest()
    session = apptesting.Session()
    request.services = services.get_handlers(lambda: session)
    return request


def fetch_data_stub(url, timeout=2):
    assert url.endswith("0034-8910-rsp-48-2-0347.xml")
    return SAMPLE_DOCUMENT_DATA


@patch("documentstore.domain.fetch_data", new=fetch_data_stub)
class FetchDocumentDataUnitTests(unittest.TestCase):
    def test_when_doesnt_exist_returns_http_404(self):
        request = make_request()
        request.matchdict = {"document_id": "unknown"}
        self.assertRaises(HTTPNotFound, restfulapi.fetch_document_data, request)

    def test_when_exists_returns_xml_as_bytes(self):
        request = make_request()
        request.matchdict = {"document_id": "my-testing-doc"}
        request.services["register_document"](
            id="my-testing-doc",
            data_url="https://raw.githubusercontent.com/scieloorg/packtools/master/tests/samples/0034-8910-rsp-48-2-0347.xml",
            assets={},
        )

        document_data = restfulapi.fetch_document_data(request)
        self.assertIsInstance(document_data, bytes)

    def test_versions_prior_to_creation_returns_http_404(self):
        request = make_request()
        request.matchdict = {"document_id": "my-testing-doc"}
        request.GET = {"when": "1900-01-01"}
        request.services["register_document"](
            id="my-testing-doc",
            data_url="https://raw.githubusercontent.com/scieloorg/packtools/master/tests/samples/0034-8910-rsp-48-2-0347.xml",
            assets={},
        )
        self.assertRaises(HTTPNotFound, restfulapi.fetch_document_data, request)

    def test_versions_in_distant_future_returns_xml_as_bytes(self):
        request = make_request()
        request.matchdict = {"document_id": "my-testing-doc"}
        request.GET = {"when": "2100-01-01"}
        request.services["register_document"](
            id="my-testing-doc",
            data_url="https://raw.githubusercontent.com/scieloorg/packtools/master/tests/samples/0034-8910-rsp-48-2-0347.xml",
            assets={},
        )

        document_data = restfulapi.fetch_document_data(request)
        self.assertIsInstance(document_data, bytes)


@patch("documentstore.domain.fetch_data", new=fetch_data_stub)
class PutDocumentUnitTests(unittest.TestCase):
    def test_registration_of_new_document_returns_201(self):
        request = make_request()
        request.matchdict = {"document_id": "0034-8910-rsp-48-2-0347"}
        request.validated = apptesting.document_registry_data_fixture()
        self.assertIsInstance(restfulapi.put_document(request), HTTPCreated)

    def test_registration_of_update_returns_204(self):
        request = make_request()
        request.matchdict = {"document_id": "0034-8910-rsp-48-2-0347"}
        request.validated = apptesting.document_registry_data_fixture()
        restfulapi.put_document(request)

        request.matchdict = {"document_id": "0034-8910-rsp-48-2-0347"}
        request.validated = apptesting.document_registry_data_fixture(prefix="v2-")
        self.assertIsInstance(restfulapi.put_document(request), HTTPNoContent)

    def test_registration_of_update_is_idempotent_and_returns_204(self):
        request = make_request()
        request.matchdict = {"document_id": "0034-8910-rsp-48-2-0347"}
        request.validated = apptesting.document_registry_data_fixture()
        restfulapi.put_document(request)
        self.assertIsInstance(restfulapi.put_document(request), HTTPNoContent)


class ParseSettingsFunctionTests(unittest.TestCase):
    def test_known_values_are_preserved_when_given(self):
        defaults = [("apptest.foo", "APPTEST_FOO", str, "modified foo")]
        self.assertEqual(
            restfulapi.parse_settings(
                {"apptest.foo": "original foo"}, defaults=defaults
            ),
            {"apptest.foo": "original foo"},
        )

    def test_use_default_when_value_is_missing(self):
        defaults = [("apptest.foo", "APPTEST_FOO", str, "foo value")]
        self.assertEqual(
            restfulapi.parse_settings({}, defaults=defaults),
            {"apptest.foo": "foo value"},
        )

    def test_env_vars_have_precedence_over_given_values(self):
        try:
            os.environ["APPTEST_FOO"] = "foo from env"

            defaults = [("apptest.foo", "APPTEST_FOO", str, "foo value")]
            self.assertEqual(
                restfulapi.parse_settings({}, defaults=defaults),
                {"apptest.foo": "foo from env"},
            )
        finally:
            os.environ.pop("APPTEST_FOO", None)

    def test_known_values_always_have_their_types_converted(self):
        defaults = [("apptest.foo", "APPTEST_FOO", int, "42")]
        self.assertEqual(
            restfulapi.parse_settings({}, defaults=defaults), {"apptest.foo": 42}
        )
        self.assertEqual(
            restfulapi.parse_settings({"apptest.foo": "17"}, defaults=defaults),
            {"apptest.foo": 17},
        )
        try:
            os.environ["APPTEST_FOO"] = "13"

            self.assertEqual(
                restfulapi.parse_settings({}, defaults=defaults), {"apptest.foo": 13}
            )
        finally:
            os.environ.pop("APPTEST_FOO", None)
