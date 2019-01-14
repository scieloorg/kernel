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


class InMemoryDocumentStore(interfaces.DocumentStore):
    def __init__(self):
        self._data = {}

    def add(self, document):
        id = document.id()
        if id in self._data:
            raise exceptions.AlreadyExists()
        else:
            self.update(document)

    def update(self, document):
        data = document.manifest
        id = document.id()
        self._data[id] = data

    def fetch(self, id):
        manifest = self._data.get(id)
        if manifest:
            return domain.Document(manifest=manifest)
        else:
            raise exceptions.DoesNotExist()


class InMemoryDocumentsBundleStore(interfaces.DocumentsBundleStore):
    def __init__(self):
        self._data = {}

    def add(self, bundle):
        id = bundle.id()
        if id in self._data:
            raise exceptions.AlreadyExists()
        else:
            self.update(bundle)

    def update(self, bundle):
        data = bundle.manifest
        id = bundle.id()
        self._data[id] = data

    def fetch(self, id):
        manifest = self._data.get(id)
        if manifest:
            return domain.DocumentsBundle(manifest=manifest)
        else:
            raise exceptions.DoesNotExist()


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
