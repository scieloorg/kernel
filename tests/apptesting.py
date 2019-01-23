from documentstore import interfaces, exceptions, domain


class Session(interfaces.Session):
    def __init__(self):
        self._documents = InMemoryDocumentStore()

    @property
    def documents(self):
        return self._documents


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
