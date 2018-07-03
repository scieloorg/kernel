import abc


class ArticleStore(abc.ABC):
    """Banco de dados de artigos.
    """

    @abc.abstractmethod
    def add(self, article) -> None:
        pass


class SessionManager(abc.ABC):
    """Retorna novas instâncias de ``Session``.
    """

    @abc.abstractmethod
    def __call__(self):
        pass


class Session(abc.ABC):
    """Implementa o padrão *unit of work*.
    """

    @abc.abstractmethod
    def __enter__(self):
        pass

    @abc.abstractmethod
    def __exit__(self, typ, value, traceback):
        pass

    @abc.abstractmethod
    def commit(self):
        pass

    @abc.abstractmethod
    def rollback(self):
        pass

    @property
    @abc.abstractmethod
    def articles(self):
        """Ponto de acesso à instância de ``ArticleStore``.
        """
        pass
