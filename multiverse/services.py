from typing import NamedTuple

from .interfaces import SessionFactory
from .domain import Article

__all__ = ["get_handlers"]


class StoreArticleCommandHandler:
    def __init__(self, Session: SessionFactory):
        self.Session = Session

    def __call__(self, id: str, data_url: str) -> None:
        session = self.Session()
        article = Article(doc_id=id)
        article.new_version(data_url)
        session.articles.add(article)


def get_handlers(Session: SessionFactory) -> dict:
    return {"store_article": StoreArticleCommandHandler(Session)}
