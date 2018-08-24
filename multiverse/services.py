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
    :param data_url: URL válida e publicamente acessível para o artigo em XML SciELO PS.
    """

    def __call__(self, id: str, data_url: str) -> None:
        session = self.Session()
        article = Article(doc_id=id)
        article.new_version(data_url)
        session.articles.add(article)


def get_handlers(Session: Callable[[], Session]) -> dict:
    return {"register_article": RegisterArticle(Session)}
