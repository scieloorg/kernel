import abc
import functools

from .domain import Document, DocumentsBundle


class DocumentStore(abc.ABC):
    """Banco de dados de documentos.
    """

    @abc.abstractmethod
    def add(self, document: Document) -> None:
        pass

    @abc.abstractmethod
    def update(self, document: Document) -> None:
        pass

    @abc.abstractmethod
    def fetch(self, id: str) -> Document:
        pass


class DocumentsBundleStore(abc.ABC):
    """Banco de dados de conjuntos de documentos.
    """

    @abc.abstractmethod
    def add(self, documents_bundle: DocumentsBundle) -> None:
        pass

    @abc.abstractmethod
    def update(self, documents_bundle: DocumentsBundle) -> None:
        pass

    @abc.abstractmethod
    def fetch(self, id: str) -> DocumentsBundle:
        pass


class Session(abc.ABC):
    """Concentra os pontos de acesso aos repositórios de dados.
    """

    @classmethod
    def partial(cls, *args, **kwargs):
        return functools.partial(cls, *args, **kwargs)

    @property
    @abc.abstractmethod
    def documents(self) -> DocumentStore:
        """Ponto de acesso à instância de ``DocumentStore``.
        """
        pass

    @property
    @abc.abstractmethod
    def documents_bundles(self) -> DocumentsBundleStore:
        """Ponto de acesso à instância de ``DocumentsBundleStore``.
        """
        pass
