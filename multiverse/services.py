from typing import NamedTuple

from .interfaces import SessionManager
from .domain import Article


class StoreArticleCommand(NamedTuple):
    id: str
    data_url: str


class StoreArticleCommandHandler:
    def __init__(self, session_manager: SessionManager):
        self.Session = session_manager

    def __call__(self, command: StoreArticleCommand) -> None:
        with self.Session() as session:
            article = Article(doc_id=command.id)
            article.new_version(command.data_url)
            session.articles.add(article)
            session.commit()
