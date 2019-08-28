from typing import Callable, Dict, Any, List
import difflib
import functools
from io import BytesIO
from enum import Enum, auto

from clea import join as clea_join, core as clea_core

from .interfaces import Session
from .domain import Document, DocumentsBundle, Journal, utcnow
from .exceptions import DoesNotExist, AlreadyExists

__all__ = ["get_handlers"]


class Events(Enum):
    """Eventos emitidos por instâncias de `CommandHandler`.
    """

    DOCUMENT_REGISTERED = auto()
    DOCUMENT_VERSION_REGISTERED = auto()
    ASSET_VERSION_REGISTERED = auto()
    DOCUMENTSBUNDLE_CREATED = auto()
    DOCUMENTSBUNDLE_METATADA_UPDATED = auto()
    DOCUMENT_ADDED_TO_DOCUMENTSBUNDLE = auto()
    DOCUMENT_INSERTED_TO_DOCUMENTSBUNDLE = auto()
    JOURNAL_CREATED = auto()
    JOURNAL_METATADA_UPDATED = auto()
    ISSUE_ADDED_TO_JOURNAL = auto()
    ISSUE_INSERTED_TO_JOURNAL = auto()
    ISSUE_REMOVED_FROM_JOURNAL = auto()
    ISSUE_DOCUMENTS_UPDATED = auto()
    JOURNAL_ISSUES_UPDATED = auto()
    AHEAD_OF_PRINT_BUNDLE_SET_TO_JOURNAL = auto()
    AHEAD_OF_PRINT_BUNDLE_REMOVED_FROM_JOURNAL = auto()
    RENDITION_VERSION_REGISTERED = auto()
    DOCUMENT_DELETED = auto()


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

    def _notify(self, session: Session, data) -> None:
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
        self._notify(
            session,
            {"document": document, "id": id, "data_url": data_url, "assets": assets},
        )


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

    def _notify(self, session, data):
        session.notify(Events.DOCUMENT_REGISTERED, data)


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

    def _notify(self, session, data):
        session.notify(Events.DOCUMENT_VERSION_REGISTERED, data)


class FetchDocumentData(CommandHandler):
    """Recupera o documento em XML à partir de seu identificador.

    Levanta `documentstore.exceptions.DeletedVersion` caso o documento tenha
    sido excluído.

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


class RegisterAssetVersion(CommandHandler):
    """Registra uma nova versão do ativo digital de documento já registrado.

    Levanta `documentstore.exceptions.DeletedVersion` caso o documento tenha
    sido excluído.

    :param id: Identificador alfanumérico para o documento.
    :param asset_id: Identificador alfanumérico para o ativo.
    :param asset_url: URL válida e publicamente acessível para o ativo digital.
    """

    def __call__(self, id: str, asset_id: str, asset_url: str) -> None:
        session = self.Session()
        document = session.documents.fetch(id)
        document.new_asset_version(asset_id=asset_id, data_url=asset_url)
        result = session.documents.update(document)
        session.notify(
            Events.ASSET_VERSION_REGISTERED,
            {
                "document": document,
                "id": id,
                "asset_id": asset_id,
                "asset_url": asset_url,
            },
        )
        return result


class DiffDocumentVersions(CommandHandler):
    """Compara duas versões do Documento.

    Levanta `documentstore.exceptions.DeletedVersion` caso o documento, em
    alguma das versões, tenha sido excluído.

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
        return {
            **clea_article.data_full,
            "aff_contrib_full": clea_join.aff_contrib_full(clea_article),
        }


class CreateDocumentsBundle(CommandHandler):
    def __call__(self, id: str, docs: list = None, metadata: dict = None) -> None:
        session = self.Session()
        _bundle = DocumentsBundle(id)
        for doc in docs or []:
            _bundle.add_document(doc)
        for name, value in (metadata or {}).items():
            setattr(_bundle, name, value)
        result = session.documents_bundles.add(_bundle)
        session.notify(
            Events.DOCUMENTSBUNDLE_CREATED,
            {"bundle": _bundle, "id": id, "docs": docs, "metadata": metadata},
        )
        return result


class FetchDocumentsBundle(CommandHandler):
    def __call__(self, id: str) -> dict:
        session = self.Session()
        return session.documents_bundles.fetch(id).data()


class UpdateDocumentsBundleMetadata(CommandHandler):
    def __call__(self, id: str, metadata: dict) -> None:
        session = self.Session()
        _bundle = session.documents_bundles.fetch(id)
        for name, value in metadata.items():
            setattr(_bundle, name, value)
        session.documents_bundles.update(_bundle)
        session.notify(
            Events.DOCUMENTSBUNDLE_METATADA_UPDATED,
            {"bundle": _bundle, "id": id, "metadata": metadata},
        )


class AddDocumentToDocumentsBundle(CommandHandler):
    def __call__(self, id: str, doc: str) -> None:
        session = self.Session()
        _bundle = session.documents_bundles.fetch(id)
        _bundle.add_document(doc)
        session.documents_bundles.update(_bundle)
        session.notify(
            Events.DOCUMENT_ADDED_TO_DOCUMENTSBUNDLE,
            {"bundle": _bundle, "id": id, "doc": doc},
        )


class InsertDocumentToDocumentsBundle(CommandHandler):
    def __call__(self, id: str, index: int, doc: str) -> None:
        session = self.Session()
        _bundle = session.documents_bundles.fetch(id)
        _bundle.insert_document(index, doc)
        session.documents_bundles.update(_bundle)
        session.notify(
            Events.DOCUMENT_INSERTED_TO_DOCUMENTSBUNDLE,
            {"bundle": _bundle, "id": id, "index": index, "doc": doc},
        )


class UpdateDocumentInDocumentsBundle(CommandHandler):
    """Atualiza a lista de documentos de uma Issue removendo todos os itens
    anteriormente associados"""

    def __call__(self, id: str, docs: List[Dict]) -> None:
        session = self.Session()
        _bundle = session.documents_bundles.fetch(id)

        for doc in _bundle.documents:
            _bundle.remove_document(doc["id"])

        for doc in docs:
            _bundle.add_document(doc)

        session.documents_bundles.update(_bundle)
        session.notify(
            Events.ISSUE_DOCUMENTS_UPDATED, {"bundle": _bundle, "id": id, "docs": docs}
        )


class CreateJournal(CommandHandler):
    def __call__(self, id: str, metadata: Dict[str, Any] = None) -> None:
        session = self.Session()
        _journal = Journal(id)
        for name, value in (metadata or {}).items():
            setattr(_journal, name, value)
        result = session.journals.add(_journal)
        session.notify(
            Events.JOURNAL_CREATED,
            {"journal": _journal, "id": id, "metadata": metadata},
        )
        return result


class FetchJournal(CommandHandler):
    """Recupera o Journal a partir do seu identificador.

    :param id: Identificador único do documento."""

    def __call__(self, id: str) -> Journal:
        session = self.Session()
        return session.journals.fetch(id).data()


class UpdateJournalMetadata(CommandHandler):
    def __call__(self, id: str, metadata: Dict[str, Any] = None) -> None:
        session = self.Session()
        _journal = session.journals.fetch(id)
        for name, value in metadata.items():
            setattr(_journal, name, value)
        session.journals.update(_journal)
        session.notify(
            Events.JOURNAL_METATADA_UPDATED,
            {"id": id, "metadata": metadata, "journal": _journal},
        )


class AddIssueToJournal(CommandHandler):
    def __call__(self, id: str, issue: dict) -> None:
        session = self.Session()
        _journal = session.journals.fetch(id)
        _journal.add_issue(issue)
        session.journals.update(_journal)
        session.notify(
            Events.ISSUE_ADDED_TO_JOURNAL,
            {"journal": _journal, "id": id, "issue": issue},
        )


class InsertIssueToJournal(CommandHandler):
    def __call__(self, id: str, index: int, issue: dict) -> None:
        session = self.Session()
        _journal = session.journals.fetch(id)
        _journal.insert_issue(index, issue)
        session.journals.update(_journal)
        session.notify(
            Events.ISSUE_INSERTED_TO_JOURNAL,
            {"journal": _journal, "id": id, "index": index, "issue": issue},
        )


class UpdateIssuesInJournal(CommandHandler):
    """Atualiza a lista de issues de um Journal removendo todos os itens
    anteriormente associados"""

    def __call__(self, id: str, issues: List[Dict]) -> None:
        session = self.Session()
        _journal = session.journals.fetch(id)

        for issue in _journal.issues:
            _journal.remove_issue(issue["id"])

        for issue in issues:
            _journal.add_issue(issue)

        session.journals.update(_journal)
        session.notify(
            Events.JOURNAL_ISSUES_UPDATED,
            {"journal": _journal, "id": id, "issues": issues},
        )


class RemoveIssueFromJournal(CommandHandler):
    def __call__(self, id: str, issue: str) -> None:
        session = self.Session()
        _journal = session.journals.fetch(id)
        _journal.remove_issue(issue)
        session.journals.update(_journal)
        session.notify(
            Events.ISSUE_REMOVED_FROM_JOURNAL,
            {"journal": _journal, "id": id, "issue": issue},
        )


class SetAheadOfPrintBundleToJournal(CommandHandler):
    def __call__(self, id: str, aop: str) -> None:
        session = self.Session()
        _journal = session.journals.fetch(id)
        _journal.ahead_of_print_bundle = aop
        session.journals.update(_journal)
        session.notify(
            Events.AHEAD_OF_PRINT_BUNDLE_SET_TO_JOURNAL,
            {"journal": _journal, "id": id, "aop": aop},
        )


class RemoveAheadOfPrintBundleFromJournal(CommandHandler):
    def __call__(self, id: str) -> None:
        session = self.Session()
        _journal = session.journals.fetch(id)
        _journal.remove_ahead_of_print_bundle()
        session.journals.update(_journal)
        session.notify(
            Events.AHEAD_OF_PRINT_BUNDLE_REMOVED_FROM_JOURNAL,
            {"journal": _journal, "id": id},
        )


class FetchChanges(CommandHandler):
    """Recupera lista de mudanças das entidades.

    :param since: (Opcional) timestamp UTC, inicia a lista de resultados na mudança
    imediatamente posterior ao timestamp informado.
    :param limit: (Opcional) Limita o total de resultados obtidos. O valor padrão é 500.
    """

    def __call__(self, since: str = "", limit: int = 500):
        session = self.Session()
        return session.changes.filter(since=since, limit=limit)


class RegisterRenditionVersion(CommandHandler):
    """Registra uma nova versão de uma manifestação do documento já registrado.

    Levanta a exceção `documentstore.exceptions.VersionAlreadySet` caso a versão
    seja a mesma da última registrada, e `documentstore.exceptions.DeletedVersion`
    caso o documento tenha sido excluído.

    :param id: Identificador alfanumérico para o documento.
    :param filename: Nome do arquivo que corresponde à manifestação.
    :param data_url: URL válida e publicamente acessível para o arquivo.
    :param mimetype: Media type conforme consta na lista da IANA
    https://www.iana.org/assignments/media-types/media-types.xhtml.
    :param lang: Idioma da manifestação conforme a norma ISO 639-1.
    :param size_bytes: Tamanho do arquivo em bytes.
    """

    def __call__(
        self,
        id: str,
        filename: str,
        data_url: str,
        mimetype: str,
        lang: str,
        size_bytes: int,
    ) -> None:
        int_size_bytes = int(size_bytes)
        session = self.Session()
        document = session.documents.fetch(id)
        document.new_rendition_version(
            filename, data_url, mimetype, lang, int_size_bytes
        )
        result = session.documents.update(document)
        session.notify(
            Events.RENDITION_VERSION_REGISTERED,
            {
                "document": document,
                "id": id,
                "filename": filename,
                "data_url": data_url,
                "mimetype": mimetype,
                "lang": lang,
                "size_bytes": int_size_bytes,
            },
        )
        return result


class FetchDocumentRenditions(CommandHandler):
    """Recupera a lista de manifestações associadas ao documento em XML.

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
        version = (
            document.version_at(version_at)
            if version_at
            else document.version(version_index)
        )
        return version.get("renditions", [])


class DeleteDocument(CommandHandler):
    """Adiciona uma nova versão ao documento indicando sua exclusão.

    :param id: Identificador único do documento.
    """

    def __call__(self, id: str) -> None:
        session = self.Session()
        document = session.documents.fetch(id)
        document.new_deleted_version()
        result = session.documents.update(document)
        session.notify(Events.DOCUMENT_DELETED, {"document": document, "id": id})
        return result


def log_change(data, session, now=utcnow, entity="", deleted=False):
    change = {"timestamp": now(), "entity": entity, "id": data["id"]}

    if deleted:
        change["deleted"] = True

    session.changes.add(change)


DEFAULT_SUBSCRIBERS = [
    (Events.DOCUMENT_REGISTERED, functools.partial(log_change, entity="Document")),
    (
        Events.DOCUMENT_VERSION_REGISTERED,
        functools.partial(log_change, entity="Document"),
    ),
    (Events.ASSET_VERSION_REGISTERED, functools.partial(log_change, entity="Document")),
    (
        Events.DOCUMENTSBUNDLE_CREATED,
        functools.partial(log_change, entity="DocumentsBundle"),
    ),
    (
        Events.DOCUMENTSBUNDLE_METATADA_UPDATED,
        functools.partial(log_change, entity="DocumentsBundle"),
    ),
    (
        Events.DOCUMENT_ADDED_TO_DOCUMENTSBUNDLE,
        functools.partial(log_change, entity="DocumentsBundle"),
    ),
    (
        Events.DOCUMENT_INSERTED_TO_DOCUMENTSBUNDLE,
        functools.partial(log_change, entity="DocumentsBundle"),
    ),
    (Events.JOURNAL_CREATED, functools.partial(log_change, entity="Journal")),
    (Events.JOURNAL_METATADA_UPDATED, functools.partial(log_change, entity="Journal")),
    (Events.ISSUE_ADDED_TO_JOURNAL, functools.partial(log_change, entity="Journal")),
    (Events.ISSUE_INSERTED_TO_JOURNAL, functools.partial(log_change, entity="Journal")),
    (
        Events.ISSUE_REMOVED_FROM_JOURNAL,
        functools.partial(log_change, entity="Journal"),
    ),
    (
        Events.AHEAD_OF_PRINT_BUNDLE_SET_TO_JOURNAL,
        functools.partial(log_change, entity="Journal"),
    ),
    (
        Events.AHEAD_OF_PRINT_BUNDLE_REMOVED_FROM_JOURNAL,
        functools.partial(log_change, entity="Journal"),
    ),
    (
        Events.RENDITION_VERSION_REGISTERED,
        functools.partial(log_change, entity="DocumentRendition"),
    ),
    (
        Events.DOCUMENT_DELETED,
        functools.partial(log_change, entity="Document", deleted=True),
    ),
    (Events.JOURNAL_ISSUES_UPDATED, functools.partial(log_change, entity="Journal")),
    (
        Events.ISSUE_DOCUMENTS_UPDATED,
        functools.partial(log_change, entity="DocumentsBundle"),
    ),
]


def get_handlers(
    Session: Callable[[], Session], subscribers=DEFAULT_SUBSCRIBERS
) -> dict:
    """Ponto de acesso aos serviços do Kernel.

    :param Session: factory de instâncias de interfaces.Session.
    :param subscribers (opcional): mapeamento entre eventos e callbacks, na
    forma de lista associativa.
    """

    def SessionWrapper():
        """Produz instância de `Session` inicializada com seus observadores.
        """
        session = Session()
        for event, callback in subscribers:
            session.observe(event, callback)
        return session

    return {
        "register_document": RegisterDocument(SessionWrapper),
        "register_document_version": RegisterDocumentVersion(SessionWrapper),
        "fetch_document_data": FetchDocumentData(SessionWrapper),
        "fetch_document_manifest": FetchDocumentManifest(SessionWrapper),
        "fetch_assets_list": FetchAssetsList(SessionWrapper),
        "register_asset_version": RegisterAssetVersion(SessionWrapper),
        "diff_document_versions": DiffDocumentVersions(SessionWrapper),
        "sanitize_document_front": SanitizeDocumentFront(SessionWrapper),
        "create_documents_bundle": CreateDocumentsBundle(SessionWrapper),
        "fetch_documents_bundle": FetchDocumentsBundle(SessionWrapper),
        "update_documents_bundle_metadata": UpdateDocumentsBundleMetadata(
            SessionWrapper
        ),
        "add_document_to_documents_bundle": AddDocumentToDocumentsBundle(
            SessionWrapper
        ),
        "insert_document_to_documents_bundle": InsertDocumentToDocumentsBundle(
            SessionWrapper
        ),
        "update_documents_in_documents_bundle": UpdateDocumentInDocumentsBundle(
            SessionWrapper
        ),
        "create_journal": CreateJournal(SessionWrapper),
        "fetch_journal": FetchJournal(SessionWrapper),
        "update_journal_metadata": UpdateJournalMetadata(SessionWrapper),
        "add_issue_to_journal": AddIssueToJournal(SessionWrapper),
        "insert_issue_to_journal": InsertIssueToJournal(SessionWrapper),
        "remove_issue_from_journal": RemoveIssueFromJournal(SessionWrapper),
        "update_issues_in_journal": UpdateIssuesInJournal(SessionWrapper),
        "fetch_changes": FetchChanges(SessionWrapper),
        "set_ahead_of_print_bundle_to_journal": SetAheadOfPrintBundleToJournal(
            SessionWrapper
        ),
        "remove_ahead_of_print_bundle_from_journal": RemoveAheadOfPrintBundleFromJournal(
            SessionWrapper
        ),
        "register_rendition_version": RegisterRenditionVersion(SessionWrapper),
        "fetch_document_renditions": FetchDocumentRenditions(SessionWrapper),
        "delete_document": DeleteDocument(SessionWrapper),
    }
