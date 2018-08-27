from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPNotFound
from cornice import Service

from . import services
from . import adapters
from . import exceptions

articles = Service(
    name="articles",
    path="/articles/{article_id}",
    description="Get article at its latest version.",
)


@articles.get(accept="text/xml", renderer="xml")
def fetch_article_data(request):
    try:
        return request.services["fetch_article_data"](
            id=request.matchdict["article_id"]
        )
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
