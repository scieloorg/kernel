from typing import Callable

from .interfaces import Session
from .domain import Article

__all__ = ["get_handlers"]


class CommandHandler:
    def __init__(self, Session: Callable[[], Session]):
        self.Session = Session


class RegisterArticle(CommandHandler):
    """Registra um novo artigo.

    :param id: Identificador alfanumérico para o artigo. Deve ser único.
    :param data_url: URL válida e publicamente acessível para o artigo em XML 
    SciELO PS.
    """

    def __call__(self, id: str, data_url: str) -> None:
        session = self.Session()
        article = Article(doc_id=id)
        article.new_version(data_url)
        session.articles.add(article)


class FetchArticleData(CommandHandler):
    """Recupera o artigo em XML à partir de seu identificador.

    :param id: Identificador único do artigo.
    :param version_index: (opcional) Número inteiro correspondente a versão do 
    artigo. Por padrão retorna a versão mais recente.
    """

    def __call__(self, id: str, version_index: int = -1) -> bytes:
        session = self.Session()
        article = session.articles.fetch(id)
        return article.data(version_index=version_index)


def get_handlers(Session: Callable[[], Session]) -> dict:
    return {
        "register_article": RegisterArticle(Session),
        "fetch_article_data": FetchArticleData(Session),
    }
