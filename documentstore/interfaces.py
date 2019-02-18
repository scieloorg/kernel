import abc
import functools
import logging


LOGGER = logging.getLogger(__name__)


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


class ChangesDataStore(abc.ABC):
    """Interface manipulação de dados de mudanças.
    """

    @abc.abstractmethod
    def add(self, data: dict) -> None:
        pass

    @abc.abstractmethod
    def filter(self, since: str = "", limit: int = 500) -> list:
        pass


class Session(abc.ABC):
    """Concentra os pontos de acesso aos repositórios de dados.

    Classes `Session` implementam o padrão Observable com a finalidade de
    suportar um sistema de eventos.
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

    @property
    @abc.abstractmethod
    def changes(self) -> ChangesDataStore:
        """Ponto de acesso à instância de ``ChangesDataStore``.
        """
        pass

    def observe(self, event, callback):
        """Registra `callback` para ser executado na ocorrência de `event`.
        """
        observers = getattr(self, "_observers", None)
        if observers is None:
            self._observers = {}
            observers = self._observers

        observers.setdefault(event, []).append(callback)

    def notify(self, event, data):
        """Notifica a ocorrência de `event`.
        """
        observers = getattr(self, "_observers", {})
        for callback in observers.get(event, []):
            try:
                callback(data, self)
            except:
                LOGGER.exception(
                    'cannot run callback "%s" in response to event "%s"',
                    repr(callback),
                    event,
                )
