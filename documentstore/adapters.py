"""Este módulo deve conter classes concretas que implementam as interfaces
definidas no módulo `interfaces`, ou seja, adaptadores.

Até o momento atual, há apenas implementações que visam o uso do MongoDB como
banco de dados e não há qualquer perspectiva para que sejam suportados
outros bancos de dados. Essa falta de perspectiva se reflete nos identificadores
das classes `Session`, `BaseStore`, `DocumentStore`, `DocumentsBundleStore` e 
`JournalStore` que carecem de um componente no nome que os diferencie de outras
implementações.
"""
import logging
import json

import pymongo

from . import interfaces
from . import exceptions
from . import domain


LOGGER = logging.getLogger(__name__)


class MongoDB:
    """Abstrai a configuração do MongoDB de maneira que nenhum outro objeto do 
    código necessita conhecer detalhes de conexão, nome do banco de dados ou
    das coleções que armazenam cada tipo de entidade. Caso seja necessário criar
    índices, aqui é o lugar.

    :param options: (opcional) dicionário com opções que serão passadas diretamente
    na instanciação de `pymongo.MongoClient`. Veja as opções em:
    https://api.mongodb.com/python/current/api/pymongo/mongo_client.html
    """

    def __init__(
        self,
        uri,
        dbname="document-store",
        mongoclient=pymongo.MongoClient,
        options=None,
    ):
        self._dbname = dbname
        self._uri = uri
        self._MongoClient = mongoclient
        self._client_instance = None
        self._options = options or {}

    @property
    def _client(self):
        """Posterga a instanciação de `pymongo.MongoClient` até o seu primeiro
        uso.
        """
        options = {k: v for k, v in self._options.items() if v}

        if not self._client_instance:
            self._client_instance = self._MongoClient(self._uri, **options)
            LOGGER.debug(
                "new MongoDB client created: <%s at %s>",
                repr(self._client_instance),
                id(self._client_instance),
            )

        LOGGER.debug(
            "using MongoDB client: <%s at %s>",
            repr(self._client_instance),
            id(self._client_instance),
        )
        return self._client_instance

    def _db(self):
        return self._client[self._dbname]

    def _collection(self, colname):
        return self._db()[colname]

    @property
    def documents(self):
        return self._collection("documents")

    @property
    def documents_bundles(self):
        return self._collection("documents_bundles")

    @property
    def journals(self):
        return self._collection("journals")

    @property
    def changes(self):
        return self._collection("changes")


class Session(interfaces.Session):
    """Implementação de `interfaces.Session` para armazenamento em MongoDB.
    Trata-se de uma classe concreta e não deve ser generalizada.
    """

    def __init__(self, mongodb_client):
        self._mongodb_client = mongodb_client

    @property
    def documents(self):
        return DocumentStore(self._mongodb_client.documents)

    @property
    def documents_bundles(self):
        return DocumentsBundleStore(self._mongodb_client.documents_bundles)

    @property
    def journals(self):
        return JournalStore(self._mongodb_client.journals)

    @property
    def changes(self):
        return ChangesStore(self._mongodb_client.changes)


class BaseStore(interfaces.DataStore):
    """Implementação de `interfaces.DataStore` para armazenamento em MongoDB.
    Trata-se de uma classe abstrata que deve ser estendida por outras que
    implementam/definem o atributo `DomainClass`.
    """

    def __init__(self, collection):
        self._collection = collection

    def _pre_write(self, data) -> dict:
        """Tratamento anterior ao armazenamento do dado no MongoDB."""
        _manifest = data.manifest
        if not _manifest.get("_id"):
            _manifest["_id"] = data.id()
        return _manifest["_id"], _manifest

    def _post_read(self, data: dict) -> dict:
        """Tratamento posterior à leitura do dado no MongoDB."""
        return data

    def add(self, data) -> None:
        try:
            _, _manifest = self._pre_write(data)
            self._collection.insert_one(_manifest)
        except pymongo.errors.DuplicateKeyError:
            raise exceptions.AlreadyExists(
                "cannot add data with id " '"%s": the id is already in use' % data.id()
            ) from None

    def update(self, data) -> None:
        _id, _manifest = self._pre_write(data)
        result = self._collection.replace_one({"_id": _id}, _manifest)
        if result.matched_count == 0:
            raise exceptions.DoesNotExist(
                "cannot update data with id " '"%s": data does not exist' % data.id()
            )

    def fetch(self, id: str):
        manifest = self._collection.find_one({"_id": id})
        if manifest:
            return self.DomainClass(manifest=self._post_read(manifest))
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
            {"_id": {"$gt": since}},
            sort=[("_id", pymongo.ASCENDING)],
            projection={"_id": False, "content_gz": False, "content_type": False},
        ).limit(limit)


class DocumentStore(BaseStore):
    DomainClass = domain.Document

    def _pre_write(self, data) -> dict:
        """Tratamento anterior ao armazenamento do dado no MongoDB. Para Document, o
        dado é armazenado em JSON por conta da presença de caracteres restritos no nome
        de campos (Ex.: "0034-8910-rsp-48-2-0347-gf01.jpg", com a presença de '.').
        Mais infos:
        https://docs.mongodb.com/manual/reference/limits/#Restrictions-on-Field-Names"""
        _id, _manifest = super()._pre_write(data)
        return _id, {"_id": _id, "document": json.dumps(_manifest)}

    def _post_read(self, data: dict) -> dict:
        """Tratamento posterior à leitura do dado no MongoDB. Para Document, o
        dado é armazenado em JSON e precisa ser convertido em dict.
        Mais infos em 'DocumentStore._pre_write' e:
        https://docs.mongodb.com/manual/reference/limits/#Restrictions-on-Field-Names"""
        return json.loads(data["document"])


class DocumentsBundleStore(BaseStore):
    DomainClass = domain.DocumentsBundle


class JournalStore(BaseStore):
    DomainClass = domain.Journal
