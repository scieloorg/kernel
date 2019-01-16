from typing import Callable, Dict
import difflib
from io import BytesIO

from clea import join as clea_join, core as clea_core

from .interfaces import Session
from .domain import Document, DocumentsBundle

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
        return Document(id=id)

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


class DiffDocumentVersions(CommandHandler):
    """Compara duas versões do Documento.

    :param id: Identificador único do documento.
    :param from_version_at: string de texto de um timestamp UTC referente a 
    versão do documento que será a base da comparação.
    :param to_version_at: (opcional) string de texto de um timestamp UTC 
    referente a versão final do documento a ser comparada. Se não for informada 
    será utilizada a versão mais recente.
    """

    def __call__(
        self, id: str, from_version_at: str, to_version_at: str = None
    ) -> bytes:
        session = self.Session()
        document = session.documents.fetch(id)
        from_version = document.data(version_at=from_version_at).splitlines()
        if to_version_at:
            _to_version_at = {"version_at": to_version_at}
        else:
            _to_version_at = {}
        to_version = document.data(**_to_version_at).splitlines()
        diff = difflib.diff_bytes(
            difflib.unified_diff,
            from_version,
            to_version,
            fromfile=from_version_at.encode("utf-8"),
            tofile=to_version_at.encode("utf-8") if to_version_at else b"latest",
            lineterm=b"",
        )
        return b"\n".join(diff)


class SanitizeDocumentFront(CommandHandler):
    """Sanitiza o front-matter do documento.

    :param xml_data: string de bytes do conteúdo do documento em XML.
    """

    def __call__(self, xml_data: bytes) -> dict:
        clea_article = clea_core.Article(BytesIO(xml_data))
        front_data = {
            tag_name: [branch.data for branch in clea_article.get(tag_name)]
            for tag_name in ["journal-meta", "article-meta"]
        }
        front_data["contrib"] = clea_join.aff_contrib_inner_join(clea_article)
        return self._rearrange(front_data)

    def _rearrange(self, data):
        def _first(iterable, default=""):
            try:
                return next(iter(iterable))
            except StopIteration:
                return default

        _data = {
            "journal-meta": _first(data["journal-meta"], {}),
            "article-meta": _first(data["article-meta"], {}),
        }
        _data["contrib"] = [
            {
                k: v
                for k, v in contrib.items()
                if k not in _data["journal-meta"] and k not in _data["article-meta"]
            }
            for contrib in data["contrib"]
        ]
        return _data


class CreateDocumentsBundle(CommandHandler):
    def __call__(self, id: str, docs: list = None, metadata: dict = None) -> None:
        session = self.Session()
        _bundle = DocumentsBundle(id)
        for doc in docs or []:
            _bundle.add_document(doc)
        for name, value in (metadata or {}).items():
            setattr(_bundle, name, value)
        return session.documents_bundles.add(_bundle)


class FetchDocumentsBundle(CommandHandler):
    def __call__(self, id: str) -> dict:
        session = self.Session()
        return session.documents_bundles.fetch(id).manifest


def get_handlers(Session: Callable[[], Session]) -> dict:
    return {
        "register_document": RegisterDocument(Session),
        "register_document_version": RegisterDocumentVersion(Session),
        "fetch_document_data": FetchDocumentData(Session),
        "fetch_document_manifest": FetchDocumentManifest(Session),
        "fetch_assets_list": FetchAssetsList(Session),
        "register_asset_version": RegisterAssetVersion(Session),
        "diff_document_versions": DiffDocumentVersions(Session),
        "sanitize_document_front": SanitizeDocumentFront(Session),
        "create_documents_bundle": CreateDocumentsBundle(Session),
        "fetch_documents_bundle": FetchDocumentsBundle(Session),
    }
