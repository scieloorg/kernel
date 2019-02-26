"""Este módulo deve conter classes concretas que implementam as interfaces
definidas no módulo `interfaces`, ou seja, adaptadores.

Até o momento atual, há apenas implementações que visam o uso do MongoDB como
banco de dados e não há qualquer perspectiva para que sejam suportados
outros bancos de dados. Essa falta de perspectiva se reflete nos identificadores
das classes `Session`, `BaseStore`, `DocumentStore`, `DocumentsBundleStore` e 
`JournalStore` que carecem de um componente no nome que os diferencie de outras
implementações.
"""
import pymongo

from . import interfaces
from . import exceptions
from . import domain


class MongoDB:
    """Abstrai a configuração do MongoDB de maneira que nenhum outro objeto do 
    código necessita conhecer detalhes de conexão, nome do banco de dados ou
    das coleções que armazenam cada tipo de entidade. Caso seja necessário criar
    índices, aqui é o lugar.
    """

    def __init__(self, uri, dbname="document-store"):
        self._client = pymongo.MongoClient(uri)
        self._dbname = dbname

    def db(self):
        return self._client[self._dbname]

    def collection(self, colname):
        return self.db()[colname]


class Session(interfaces.Session):
    """Implementação de `interfaces.Session` para armazenamento em MongoDB.
    Trata-se de uma classe concreta e não deve ser generalizada.
    """

    def __init__(self, mongodb_client):
        self._mongodb_client = mongodb_client

    @property
    def documents(self):
        return DocumentStore(self._mongodb_client.collection(colname="documents"))

    @property
    def documents_bundles(self):
        return DocumentsBundleStore(
            self._mongodb_client.collection(colname="documents_bundles")
        )

    @property
    def journals(self):
        return JournalStore(self._mongodb_client.collection(colname="journals"))

    @property
    def changes(self):
        return ChangesStore(self._mongodb_client.collection(colname="changes"))


class BaseStore(interfaces.DataStore):
    """Implementação de `interfaces.DataStore` para armazenamento em MongoDB.
    Trata-se de uma classe abstrata que deve ser estendida por outras que
    implementam/definem o atributo `DomainClass`.
    """

    def __init__(self, collection):
        self._collection = collection

    def add(self, data) -> None:
        _manifest = data.manifest
        if not _manifest.get("_id"):
            _manifest["_id"] = data.id()
        try:
            self._collection.insert_one(_manifest)
        except pymongo.errors.DuplicateKeyError:
            raise exceptions.AlreadyExists(
                "cannot add data with id " '"%s": the id is already in use' % data.id()
            ) from None

    def update(self, data) -> None:
        _manifest = data.manifest
        if not _manifest.get("_id"):
            _manifest["_id"] = data.id()
        result = self._collection.replace_one({"_id": _manifest["_id"]}, _manifest)
        if result.matched_count == 0:
            raise exceptions.DoesNotExist(
                "cannot update data with id " '"%s": data does not exist' % data.id()
            )

    def fetch(self, id: str):
        manifest = self._collection.find_one({"_id": id})
        if manifest:
            return self.DomainClass(manifest=manifest)
        else:
            raise exceptions.DoesNotExist(
                "cannot fetch data with id " '"%s": data does not exist' % id
            )


class ChangesStore(interfaces.ChangesDataStore):
    """Implementação de `interfaces.ChangesDataStore` para armazenamento em 
    MongoDB.
    """

    def __init__(self, collection):
        self._collection = collection

    def add(self, change: dict):
        change["_id"] = change["timestamp"]
        try:
            self._collection.insert_one(change)
        except pymongo.errors.DuplicateKeyError:
            raise exceptions.AlreadyExists(
                "cannot add data with id "
                '"%s": the id is already in use' % change["_id"]
            ) from None

    def filter(self, since: str = "", limit: int = 500):
        return self._collection.find(
            {"_id": {"$gte": since}},
            sort=[("_id", pymongo.ASCENDING)],
            projection={"_id": False},
        ).limit(limit)


class DocumentStore(BaseStore):
    DomainClass = domain.Document


class DocumentsBundleStore(BaseStore):
    DomainClass = domain.DocumentsBundle


class JournalStore(BaseStore):
    DomainClass = domain.Journal
