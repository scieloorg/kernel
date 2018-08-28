from typing import Callable, Dict

from .interfaces import Session
from .domain import Article

__all__ = ["get_handlers"]


class CommandHandler:
    def __init__(self, Session: Callable[[], Session]):
        self.Session = Session


class BaseRegisterArticle(CommandHandler):
    """Implementação abstrata de comando para registrar um novo artigo.

    :param id: Identificador alfanumérico para o artigo. Deve ser único.
    :param data_url: URL válida e publicamente acessível para o artigo em XML 
    SciELO PS.
    """

    def _get_article(self, session: Session, id: str) -> Article:
        raise NotImplementedError()

    def _persist(self, session: Session, article: Article) -> None:
        raise NotImplementedError()

    def __call__(self, id: str, data_url: str, assets: Dict[str, str] = None) -> None:
        try:
            assets = dict(assets)
        except TypeError:
            assets = {}
        session = self.Session()
        article = self._get_article(session, id)
        article.new_version(data_url)
        for asset_id, asset_url in assets.items():
            article.new_asset_version(asset_id, asset_url)
        self._persist(session, article)


class RegisterArticle(BaseRegisterArticle):
    """Registra um novo artigo.

    :param id: Identificador alfanumérico para o artigo. Deve ser único.
    :param data_url: URL válida e publicamente acessível para o artigo em XML 
    SciELO PS.
    """

    def _get_article(self, session, id):
        return Article(doc_id=id)

    def _persist(self, session, article):
        return session.articles.add(article)


class RegisterArticleVersion(BaseRegisterArticle):
    """Registra uma nova versão de um artigo já registrado.

    :param id: Identificador alfanumérico para o artigo.
    :param data_url: URL válida e publicamente acessível para o artigo em XML 
    SciELO PS.
    """

    def _get_article(self, session, id):
        return session.articles.fetch(id)

    def _persist(self, session, article):
        return session.articles.update(article)


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


class FetchArticleManifest(CommandHandler):
    """Recupera o manifesto do artigo à partir de seu identificador.

    :param id: Identificador único do artigo.
    """

    def __call__(self, id: str) -> dict:
        session = self.Session()
        article = session.articles.fetch(id)
        return article.manifest


class FetchAssetsList(CommandHandler):
    """Recupera a lista de ativos do artigo à partir de seu identificador.

    :param id: Identificador único do artigo.
    :param version_index: (opcional) Número inteiro correspondente a versão do 
    artigo. Por padrão retorna a versão mais recente.
    """

    def __call__(self, id: str, version_index: int = -1) -> dict:
        session = self.Session()
        article = session.articles.fetch(id)
        return article.version(index=version_index)


class RegisterAssetVersion(BaseRegisterArticle):
    """Registra uma nova versão do ativo digital de artigo já registrado.

    :param id: Identificador alfanumérico para o artigo.
    :param asset_id: Identificador alfanumérico para o ativo.
    :param asset_url: URL válida e publicamente acessível para o ativo digital.
    """

    def __call__(self, id: str, asset_id: str, asset_url: str) -> None:
        session = self.Session()
        article = session.articles.fetch(id)
        article.new_asset_version(asset_id=asset_id, data_url=asset_url)
        return session.articles.update(article)


def get_handlers(Session: Callable[[], Session]) -> dict:
    return {
        "register_article": RegisterArticle(Session),
        "register_article_version": RegisterArticleVersion(Session),
        "fetch_article_data": FetchArticleData(Session),
        "fetch_article_manifest": FetchArticleManifest(Session),
        "fetch_assets_list": FetchAssetsList(Session),
        "register_asset_version": RegisterAssetVersion(Session),
    }
