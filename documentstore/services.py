from typing import Callable, Dict

from .interfaces import Session
from .domain import Document

__all__ = ["get_handlers"]


class CommandHandler:
    def __init__(self, Session: Callable[[], Session]):
        self.Session = Session


class BaseRegisterDocument(CommandHandler):
    """Implementação abstrata de comando para registrar um novo documento.

    :param id: Identificador alfanumérico para o documento. Deve ser único.
    :param data_url: URL válida e publicamente acessível para o documento em XML 
    SciELO PS.
    """

    def _get_document(self, session: Session, id: str) -> Document:
        raise NotImplementedError()

    def _persist(self, session: Session, document: Document) -> None:
        raise NotImplementedError()

    def __call__(self, id: str, data_url: str, assets: Dict[str, str] = None) -> None:
        try:
            assets = dict(assets)
        except TypeError:
            assets = {}
        session = self.Session()
        document = self._get_document(session, id)
        document.new_version(data_url)
        for asset_id, asset_url in assets.items():
            document.new_asset_version(asset_id, asset_url)
        self._persist(session, document)


class RegisterDocument(BaseRegisterDocument):
    """Registra um novo documento.

    :param id: Identificador alfanumérico para o documento. Deve ser único.
    :param data_url: URL válida e publicamente acessível para o documento em XML 
    SciELO PS.
    """

    def _get_document(self, session, id):
        return Document(doc_id=id)

    def _persist(self, session, document):
        return session.documents.add(document)


class RegisterDocumentVersion(BaseRegisterDocument):
    """Registra uma nova versão de um documento já registrado.

    :param id: Identificador alfanumérico para o documento.
    :param data_url: URL válida e publicamente acessível para o documento em XML 
    SciELO PS.
    """

    def _get_document(self, session, id):
        return session.documents.fetch(id)

    def _persist(self, session, document):
        return session.documents.update(document)


class FetchDocumentData(CommandHandler):
    """Recupera o documento em XML à partir de seu identificador.

    :param id: Identificador único do documento.
    :param version_index: (opcional) Número inteiro correspondente a versão do 
    documento. Por padrão retorna a versão mais recente.
    :param version_at: (opcional) string de texto de um timestamp UTC
    referente a versão do documento no determinado momento. O uso do argumento
    `version_at` faz com que qualquer valor de `version_index` seja ignorado.
    """

    def __call__(
        self, id: str, version_index: int = -1, version_at: str = None
    ) -> bytes:
        session = self.Session()
        document = session.documents.fetch(id)
        return document.data(version_index=version_index, version_at=version_at)


class FetchDocumentManifest(CommandHandler):
    """Recupera o manifesto do documento à partir de seu identificador.

    :param id: Identificador único do documento.
    """

    def __call__(self, id: str) -> dict:
        session = self.Session()
        document = session.documents.fetch(id)
        return document.manifest


class FetchAssetsList(CommandHandler):
    """Recupera a lista de ativos do documento à partir de seu identificador.

    :param id: Identificador único do documento.
    :param version_index: (opcional) Número inteiro correspondente a versão do 
    documento. Por padrão retorna a versão mais recente.
    """

    def __call__(self, id: str, version_index: int = -1) -> dict:
        session = self.Session()
        document = session.documents.fetch(id)
        return document.version(index=version_index)


class RegisterAssetVersion(BaseRegisterDocument):
    """Registra uma nova versão do ativo digital de documento já registrado.

    :param id: Identificador alfanumérico para o documento.
    :param asset_id: Identificador alfanumérico para o ativo.
    :param asset_url: URL válida e publicamente acessível para o ativo digital.
    """

    def __call__(self, id: str, asset_id: str, asset_url: str) -> None:
        session = self.Session()
        document = session.documents.fetch(id)
        document.new_asset_version(asset_id=asset_id, data_url=asset_url)
        return session.documents.update(document)


def get_handlers(Session: Callable[[], Session]) -> dict:
    return {
        "register_document": RegisterDocument(Session),
        "register_document_version": RegisterDocumentVersion(Session),
        "fetch_document_data": FetchDocumentData(Session),
        "fetch_document_manifest": FetchDocumentManifest(Session),
        "fetch_assets_list": FetchAssetsList(Session),
        "register_asset_version": RegisterAssetVersion(Session),
    }
