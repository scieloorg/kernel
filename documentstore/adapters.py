import pymongo

from . import interfaces
from . import exceptions
from . import domain


class MongoDB:
    def __init__(self, uri, dbname="document-store", colname="manifests"):
        self._client = pymongo.MongoClient(uri)
        self._dbname = dbname
        self._colname = colname

    def db(self):
        return self._client[self._dbname]

    def collection(self):
        return self.db()[self._colname]


class Session(interfaces.Session):
    def __init__(self, mongodb_client):
        self._mongodb_client = mongodb_client
        self._collection = self._mongodb_client.collection()

    @property
    def documents(self):
        return DocumentStore(self._collection)

    @property
    def documents_bundles(self):
        return None


class DocumentStore:
    def __init__(self, collection):
        self._collection = collection

    def add(self, document):
        data = document.manifest
        if not data.get("_id"):
            data["_id"] = document.id()
        try:
            self._collection.insert_one(data)
        except pymongo.errors.DuplicateKeyError:
            raise exceptions.AlreadyExists(
                "cannot add document with id "
                '"%s": the id is already in use' % document.id()
            ) from None

    def update(self, document):
        data = document.manifest
        if not data.get("_id"):
            data["_id"] = document.id()
        self._collection.replace_one({"_id": data["_id"]}, data)

    def fetch(self, id):
        manifest = self._collection.find_one({"_id": id})
        if manifest:
            return domain.Document(manifest=manifest)
        else:
            raise exceptions.DoesNotExist(
                "cannot fetch document with id " '"%s": document does not exist' % id
            )
