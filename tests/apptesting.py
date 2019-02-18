from collections import OrderedDict

from documentstore import interfaces, exceptions, domain


class Session(interfaces.Session):
    def __init__(self):
        self._documents = InMemoryDocumentStore()
        self._documents_bundles = InMemoryDocumentsBundleStore()
        self._journals = InMemoryJournalStore()
        self._changes = InMemoryChangesDataStore()

    @property
    def documents(self):
        return self._documents

    @property
    def documents_bundles(self):
        return self._documents_bundles

    @property
    def journals(self):
        return self._journals

    @property
    def changes(self):
        return self._changes


class InMemoryDataStore(interfaces.DataStore):
    def __init__(self):
        self._data_store = {}

    def add(self, data):
        id = data.id()
        if id in self._data_store:
            raise exceptions.AlreadyExists()
        else:
            self.update(data)

    def update(self, data):
        _manifest = data.manifest
        id = data.id()
        self._data_store[id] = _manifest

    def fetch(self, id):
        manifest = self._data_store.get(id)
        if manifest:
            return self.DomainClass(manifest=manifest)
        else:
            raise exceptions.DoesNotExist()


class InMemoryDocumentStore(InMemoryDataStore):
    DomainClass = domain.Document


class InMemoryDocumentsBundleStore(InMemoryDataStore):
    DomainClass = domain.DocumentsBundle


class InMemoryJournalStore(InMemoryDataStore):
    DomainClass = domain.Journal


def document_registry_data_fixture(prefix=""):
    return {
        "data": f"https://raw.githubusercontent.com/scieloorg/packtools/master/tests/samples/{prefix}0034-8910-rsp-48-2-0347.xml",
        "assets": [
            {
                "asset_id": "0034-8910-rsp-48-2-0347-gf01",
                "asset_url": "http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf01.jpg",
            },
            {
                "asset_id": "0034-8910-rsp-48-2-0347-gf01-en",
                "asset_url": "http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf01-en.jpg",
            },
            {
                "asset_id": "0034-8910-rsp-48-2-0347-gf02",
                "asset_url": "http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf02.jpg",
            },
            {
                "asset_id": "0034-8910-rsp-48-2-0347-gf02-en",
                "asset_url": "http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf02-en.jpg",
            },
            {
                "asset_id": "0034-8910-rsp-48-2-0347-gf03",
                "asset_url": "http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf03.jpg",
            },
            {
                "asset_id": "0034-8910-rsp-48-2-0347-gf03-en",
                "asset_url": "http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf03-en.jpg",
            },
            {
                "asset_id": "0034-8910-rsp-48-2-0347-gf04",
                "asset_url": "http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf04.jpg",
            },
            {
                "asset_id": "0034-8910-rsp-48-2-0347-gf04-en",
                "asset_url": "http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf04-en.jpg",
            },
        ],
    }


class InMemoryChangesDataStore(interfaces.ChangesDataStore):
    def __init__(self):
        self._data_store = OrderedDict()

    def add(self, change: dict):

        if change["timestamp"] in self._data_store:
            raise exceptions.AlreadyExists()
        else:
            self._data_store[change["timestamp"]] = change

    def filter(self, since: str = "", limit: int = 500):

        first = 0
        for i, change_key in enumerate(self._data_store):
            if self._data_store[change_key]["timestamp"] < since:
                continue
            else:
                first = i
                break

        return list(self._data_store.values())[first:limit]
