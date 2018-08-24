import abc
import functools

from .domain import Article


class ArticleStore(abc.ABC):
    """Banco de dados de artigos.
    """

    @abc.abstractmethod
    def add(self, article: Article) -> None:
        pass

    @abc.abstractmethod
    def update(self, article: Article) -> None:
        pass

    @abc.abstractmethod
    def fetch(self, id: str) -> Article:
        pass


class Session(abc.ABC):
    """Concentra os pontos de acesso aos repositórios de dados.
    """

    @classmethod
    def partial(cls, *args, **kwargs):
        return functools.partial(cls, *args, **kwargs)

    @property
    @abc.abstractmethod
    def articles(self) -> ArticleStore:
        """Ponto de acesso à instância de ``ArticleStore``.
        """
        pass
