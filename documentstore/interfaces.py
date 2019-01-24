import abc
import functools


class DataStore(abc.ABC):
    """Interface manipulação de dados.
    """

    @abc.abstractmethod
    def add(self, data) -> None:
        pass

    @abc.abstractmethod
    def update(self, data) -> None:
        pass

    @abc.abstractmethod
    def fetch(self, id: str):
        pass


class Session(abc.ABC):
    """Concentra os pontos de acesso aos repositórios de dados.
    """

    @classmethod
    def partial(cls, *args, **kwargs):
        return functools.partial(cls, *args, **kwargs)

    @property
    @abc.abstractmethod
    def documents(self) -> DataStore:
        """Ponto de acesso à instância de ``DataStore``.
        """
        pass

    @property
    @abc.abstractmethod
    def documents_bundles(self) -> DataStore:
        """Ponto de acesso à instância de ``DataStore``.
        """
        pass
