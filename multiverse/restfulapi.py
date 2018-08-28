import logging

from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPNotFound, HTTPNoContent, HTTPCreated
from cornice import Service
from cornice.validators import colander_body_validator
import colander

from . import services
from . import adapters
from . import exceptions

LOGGER = logging.getLogger(__name__)

articles = Service(
    name="articles",
    path="/articles/{article_id}",
    description="Get article at its latest version.",
)

manifest = Service(
    name="manifest",
    path="/articles/{article_id}/manifest",
    description="Get the article's manifest.",
)

assets_list = Service(
    name="assets_list",
    path="/articles/{article_id}/assets",
    description="Get the article's assets.",
)


class Asset(colander.MappingSchema):
    asset_id = colander.SchemaNode(colander.String())
    asset_url = colander.SchemaNode(colander.String(), validator=colander.url)


class Assets(colander.SequenceSchema):
    asset = Asset()


class RegisterArticleSchema(colander.MappingSchema):
    """Representa o schema de dados para registro de artigos.
    """

    data = colander.SchemaNode(colander.String(), validator=colander.url)
    assets = Assets()


@articles.get(accept="text/xml", renderer="xml")
def fetch_article_data(request):
    try:
        return request.services["fetch_article_data"](
            id=request.matchdict["article_id"]
        )
    except exceptions.ArticleDoesNotExist as exc:
        raise HTTPNotFound(exc)


@articles.put(schema=RegisterArticleSchema(), validators=(colander_body_validator,))
def put_article(request):
    """Adiciona ou atualiza registro de artigo. A atualização do artigo é 
    idempotente.
    
    A semântica desta view-function está definida conforme a especificação:
    https://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html#sec9.6
    """
    data_url = request.validated["data"]
    assets = {
        asset["asset_id"]: asset["asset_url"]
        for asset in request.validated.get("assets", [])
    }
    try:
        request.services["register_article"](
            id=request.matchdict["article_id"], data_url=data_url, assets=assets
        )
    except exceptions.ArticleAlreadyExists:
        try:
            request.services["register_article_version"](
                id=request.matchdict["article_id"], data_url=data_url, assets=assets
            )
        except exceptions.ArticleVersionAlreadySet as exc:
            LOGGER.info(
                'skipping request to add version to "%s": %s',
                request.matchdict["article_id"],
                exc,
            )
        return HTTPNoContent("article updated successfully")
    else:
        return HTTPCreated("article created successfully")


@manifest.get(accept="application/json", renderer="json")
def get_manifest(request):
    try:
        return request.services["fetch_article_manifest"](
            id=request.matchdict["article_id"]
        )
    except exceptions.ArticleDoesNotExist as exc:
        raise HTTPNotFound(exc)


@assets_list.get(accept="application/json", renderer="json")
def get_assets_list(request):
    try:
        return request.services["fetch_assets_list"](id=request.matchdict["article_id"])
    except exceptions.ArticleDoesNotExist as exc:
        raise HTTPNotFound(exc)


class XMLRenderer:
    """Renderizador para dados do tipo ``text/xml``.

    Espera que o retorno da view-function seja uma string de bytes pronta para
    ser transferida para o cliente. Este renderer apenas define o content-type
    da resposta HTTP.
    """

    def __init__(self, info):
        pass

    def __call__(self, value, system):
        request = system.get("request")
        if request is not None:
            request.response.content_type = "text/xml"
        return value


def main(global_config, **settings):
    config = Configurator(settings=settings)
    config.include("cornice")
    config.scan()
    config.add_renderer("xml", XMLRenderer)

    mongo = adapters.MongoDB("mongodb://localhost:27017/")
    Session = adapters.Session.partial(mongo)

    config.add_request_method(
        lambda request: services.get_handlers(Session), "services", reify=True
    )

    return config.make_wsgi_app()
