from typing import Callable

from .interfaces import Session
from .domain import Article

__all__ = ["get_handlers"]


class StoreArticleCommandHandler:
    def __init__(self, Session: Callable[[], Session]):
        self.Session = Session

    def __call__(self, id: str, data_url: str) -> None:
        session = self.Session()
        article = Article(doc_id=id)
        article.new_version(data_url)
        session.articles.add(article)


def get_handlers(Session: Callable[[], Session]) -> dict:
    return {"store_article": StoreArticleCommandHandler(Session)}
