from documentstore import interfaces, exceptions, domain


class Session(interfaces.Session):
    def __init__(self):
        self._documents = InMemoryDocumentStore()
        self._documents_bundles = InMemoryDocumentsBundleStore()

    @property
    def documents(self):
        return self._documents

    @property
    def documents_bundles(self):
        return self._documents_bundles


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
