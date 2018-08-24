import pymongo

from . import interfaces
from . import exceptions
from . import domain


class MongoDB:
    def __init__(self, uri, dbname="article-store", colname="manifests"):
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
    def articles(self):
        return ArticleStore(self._collection)


class ArticleStore:
    def __init__(self, collection):
        self._collection = collection

    def add(self, article):
        data = article.manifest
        if not data.get("_id"):
            data["_id"] = article.doc_id()
        try:
            self._collection.insert_one(data)
        except pymongo.errors.DuplicateKeyError:
            raise exceptions.ArticleAlreadyExists(
                "cannot add article with id "
                '"%s": the id is already in use' % article.doc_id()
            ) from None

    def update(self, article):
        data = article.manifest
        if not data.get("_id"):
            data["_id"] = article.doc_id()
        self._collection.replace_one({"_id": data["_id"]}, data)

    def fetch(self, id):
        manifest = self._collection.find_one({"_id": id})
        if manifest:
            return domain.Article(manifest=manifest)
        else:
            raise exceptions.ArticleDoesNotExist(
                "cannot fetch article with id " '"%s": article does not exist' % id
            )
