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


def manifest_data_fixture():
    return {
        "id": "0034-8910-rsp-48-2",
        "versions": [
            {
              "assets": {
                "0034-8910-rsp-48-2-0347-gf01.jpg": [
                  [
                    "2018-08-05T23:03:44.971230Z",
                    "http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf01.jpg"
                  ]
                ],
                "0034-8910-rsp-48-2-0347-gf01-en.jpg": [
                  [
                    "2018-08-05T23:08:41.590174Z",
                    "http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf01-en.jpg"
                  ]
                ],
              },
              "data": "https://ssm.scielo.br/tests/samples/0034-8910-rsp-48-2-0347.xml",
              "timestamp": "2018-08-05T23:02:29.392990Z"
            },
            {
              "assets": {
                "0034-8910-rsp-48-2-0347-gf02.tiff": [
                  [
                    "2018-08-05T23:04:43.323527Z",
                    "http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf02.tiff"
                  ]
                ],
                "0034-8910-rsp-48-2-0347-gf02-en.tiff": [
                  [
                    "2018-08-05T23:08:50.331687Z",
                    "http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf02-en.tiff"
                  ]
                ],
              },
              "data": "https://ssm.scielo.br/tests/samples/0034-8910-rsp-48-2-0347.xml",
              "timestamp": "2018-11-16T23:02:29.392990Z"
            },
        ],
        "author": {
            "last.name": "Smith",
            "first.name": "Joshua",
        },
        "logo.gif": "logo.gif",
        "namespace$": ["a", "b", "$"],
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

        return [
            change
            for timestamp, change in self._data_store.items()
            if timestamp >= since
        ][:limit]


class MongoDBCollectionStub:
    def __init__(self):
        self._mongo_store = OrderedDict()

    def insert_one(self, data):
        import pymongo

        if data["_id"] in self._mongo_store:
            raise pymongo.errors.DuplicateKeyError("")
        else:
            self._mongo_store[data["_id"]] = data

    def find(self, query, sort=None, projection=None):
        since = query["_id"]["$gte"]

        first = 0
        for i, change_key in enumerate(self._mongo_store):
            if self._mongo_store[change_key]["_id"] < since:
                continue
            else:
                first = i
                break

        return SliceResultStub(list(self._mongo_store.values())[first:])


class SliceResultStub:
    def __init__(self, data):
        self._data = data

    def limit(self, val):
        return self._data[:val]
