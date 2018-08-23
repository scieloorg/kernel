import abc


class ArticleStore(abc.ABC):
    """Banco de dados de artigos.
    """

    @abc.abstractmethod
    def add(self, article) -> None:
        pass


class SessionFactory(abc.ABC):
    """Retorna novas instâncias de ``Session``.

    ``SessionFactory`` deve ser instanciado durante a inicialização da 
    aplicação. Sua função é concentrar a injeção das dependências relacionadas
    à persistência dos dados.

    >>> Session = SessionFactory(mongodb_client, aws_s3_client)
    >>> my_session = Session()
    """

    @abc.abstractmethod
    def __call__(self) -> Session:
        pass


class Session(abc.ABC):
    """Implementa o padrão *unit of work*.
    """

    @property
    @abc.abstractmethod
    def articles(self) -> ArticleStore:
        """Ponto de acesso à instância de ``ArticleStore``.
        """
        pass
