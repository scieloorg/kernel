import logging
import os

from pyramid.config import Configurator
from pyramid.httpexceptions import (
    HTTPNotFound,
    HTTPNoContent,
    HTTPCreated,
    HTTPBadRequest,
)
from cornice import Service
from cornice.validators import colander_body_validator
import colander
from slugify import slugify

from . import services
from . import adapters
from . import exceptions

LOGGER = logging.getLogger(__name__)

documents = Service(
    name="documents",
    path="/documents/{document_id}",
    description="Get document at its latest version.",
)

manifest = Service(
    name="manifest",
    path="/documents/{document_id}/manifest",
    description="Get the document's manifest.",
)

assets_list = Service(
    name="assets_list",
    path="/documents/{document_id}/assets",
    description="Get the document's assets.",
)

assets = Service(
    name="assets",
    path="/documents/{document_id}/assets/{asset_slug}",
    description="Set the URL for an document's asset.",
)

diff = Service(
    name="diff",
    path="/documents/{document_id}/diff",
    description="Compare two versions of the same document.",
)

front = Service(
    name="front",
    path="/documents/{document_id}/front",
    description="Front-matter of the document in a normalized schema.",
)

bundles = Service(
    name="bundles",
    path="/bundles/{bundle_id}",
    description="Get documents bundle data.",
)

changes = Service(
    name="changes", path="/changes", description="Get changes from all entities"
)

journals = Service(
    name="journals",
    path="/journals/{journal_id}",
    description="Register and retrieve journals' endpoint",
)


class Asset(colander.MappingSchema):
    asset_id = colander.SchemaNode(colander.String())
    asset_url = colander.SchemaNode(colander.String(), validator=colander.url)


class Assets(colander.SequenceSchema):
    asset = Asset()


class RegisterDocumentSchema(colander.MappingSchema):
    """Representa o schema de dados para registro de documentos.
    """

    data = colander.SchemaNode(colander.String(), validator=colander.url)
    assets = Assets()


class AssetSchema(colander.MappingSchema):
    """Representa o schema de dados para registro de ativos do documento.
    """

    asset_url = colander.SchemaNode(colander.String(), validator=colander.url)


class RegisterJournalSchema(colander.MappingSchema):
    """Representa o schema de dados para registro de periódicos.
    """

    title = colander.SchemaNode(colander.String())
    mission = colander.SchemaNode(colander.Mapping(unknown="preserve"))
    title_iso = colander.SchemaNode(colander.String())
    short_title = colander.SchemaNode(colander.String())
    title_slug = colander.SchemaNode(colander.String())
    acronym = colander.SchemaNode(colander.String())
    scielo_issn = colander.SchemaNode(colander.String())
    print_issn = colander.SchemaNode(colander.String())
    electronic_issn = colander.SchemaNode(colander.String())
    status = colander.SchemaNode(colander.Mapping(unknown="preserve"))
    subject_areas = colander.SchemaNode(colander.List())
    sponsors = colander.SchemaNode(colander.List())
    metrics = colander.SchemaNode(colander.Mapping(unknown="preserve"))
    subject_categories = colander.SchemaNode(colander.List())
    institution_responsible_for = colander.SchemaNode(colander.List())
    online_submission_url = colander.SchemaNode(
        colander.String(), validator=colander.url
    )
    next_journal = colander.SchemaNode(colander.Mapping(unknown="preserve"))
    logo_url = colander.SchemaNode(colander.String(), validator=colander.url)
    previous_journal = colander.SchemaNode(colander.Mapping(unknown="preserve"))
    contact = colander.SchemaNode(colander.Mapping(unknown="preserve"))


class DocumentsBundleSchema(colander.MappingSchema):
    """Representa o schema de dados para registro de Documents Bundle."""

    pid = colander.SchemaNode(colander.String(), missing=colander.drop)
    year = colander.SchemaNode(colander.Int(), missing=colander.drop)
    label = colander.SchemaNode(colander.String(), missing=colander.drop)
    volume = colander.SchemaNode(colander.String(), missing=colander.drop)
    number = colander.SchemaNode(colander.String(), missing=colander.drop)

    @colander.instantiate(missing=colander.drop)
    class titles(colander.SequenceSchema):
        @colander.instantiate()
        class title(colander.MappingSchema):
            language = colander.SchemaNode(
                colander.String(), validator=colander.Length(2, 2)
            )
            title = colander.SchemaNode(colander.String(), validator=colander.Length(1))


@documents.get(accept="text/xml", renderer="xml")
def fetch_document_data(request):
    when = request.GET.get("when", None)
    if when:
        version = {"version_at": when}
    else:
        version = {}
    try:
        return request.services["fetch_document_data"](
            id=request.matchdict["document_id"], **version
        )
    except (exceptions.DoesNotExist, ValueError) as exc:
        raise HTTPNotFound(exc)


@documents.put(schema=RegisterDocumentSchema(), validators=(colander_body_validator,))
def put_document(request):
    """Adiciona ou atualiza registro de documento. A atualização do documento é
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
        request.services["register_document"](
            id=request.matchdict["document_id"], data_url=data_url, assets=assets
        )
    except exceptions.AlreadyExists:
        try:
            request.services["register_document_version"](
                id=request.matchdict["document_id"], data_url=data_url, assets=assets
            )
        except exceptions.VersionAlreadySet as exc:
            LOGGER.info(
                'skipping request to add version to "%s": %s',
                request.matchdict["document_id"],
                exc,
            )
        return HTTPNoContent("document updated successfully")
    else:
        return HTTPCreated("document created successfully")


@manifest.get(accept="application/json", renderer="json")
def get_manifest(request):
    try:
        return request.services["fetch_document_manifest"](
            id=request.matchdict["document_id"]
        )
    except exceptions.DoesNotExist as exc:
        raise HTTPNotFound(exc)


def slugify_assets_ids(assets, slug_fn=slugify):
    return [
        {"slug": slug_fn(asset_id), "id": asset_id, "url": asset_url}
        for asset_id, asset_url in assets.items()
    ]


@assets_list.get(accept="application/json", renderer="json")
def get_assets_list(request):
    try:
        assets = request.services["fetch_assets_list"](
            id=request.matchdict["document_id"]
        )
    except exceptions.DoesNotExist as exc:
        raise HTTPNotFound(exc)

    assets["assets"] = slugify_assets_ids(assets["assets"])
    return assets


@assets.put(schema=AssetSchema(), validators=(colander_body_validator,))
def put_asset(request):
    """Adiciona ou atualiza registro de ativo do documento. A atualização do
    ativo é idempotente.

    A semântica desta view-function está definida conforme a especificação:
    https://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html#sec9.6
    """
    assets_list = get_assets_list(request)
    assets_map = {asset["slug"]: asset["id"] for asset in assets_list["assets"]}
    asset_slug = request.matchdict["asset_slug"]
    try:
        asset_id = assets_map[asset_slug]
    except KeyError:
        raise HTTPNotFound(
            'cannot fetch asset with slug "%s": asset does not exist' % asset_slug
        )

    asset_url = request.validated["asset_url"]
    try:
        request.services["register_asset_version"](
            id=request.matchdict["document_id"], asset_id=asset_id, asset_url=asset_url
        )
    except exceptions.VersionAlreadySet as exc:
        LOGGER.info(
            'skipping request to add version to "%s/assets/%s": %s',
            request.matchdict["document_id"],
            request.matchdict["asset_slug"],
            exc,
        )
    return HTTPNoContent("asset updated successfully")


@diff.get(renderer="text")
def diff_document_versions(request):
    """Compara duas versões do documento. Se o argumento `to_when` não for
    fornecido, será assumido como alvo a versão mais recente.
    """
    from_when = request.GET.get("from_when", None)
    if from_when is None:
        raise HTTPBadRequest("cannot fetch diff: missing attribute from_when")
    try:
        return request.services["diff_document_versions"](
            id=request.matchdict["document_id"],
            from_version_at=from_when,
            to_version_at=request.GET.get("to_when", None),
        )
    except (exceptions.DoesNotExist, ValueError) as exc:
        raise HTTPNotFound(exc)


@front.get(renderer="json")
def fetch_document_front(request):
    data = fetch_document_data(request)
    return request.services["sanitize_document_front"](data)


@bundles.get(renderer="json")
def fetch_documents_bundle(request):
    try:
        return request.services["fetch_documents_bundle"](
            request.matchdict["bundle_id"]
        )
    except KeyError:
        return HTTPBadRequest("bundle id is mandatory")
    except exceptions.DoesNotExist as exc:
        return HTTPNotFound(str(exc))


@bundles.put(
    schema=DocumentsBundleSchema(),
    validators=(colander_body_validator,),
    accept="application/json",
    renderer="json",
)
def put_documents_bundle(request):
    try:
        request.services["create_documents_bundle"](
            request.matchdict["bundle_id"], metadata=request.validated
        )
    except exceptions.AlreadyExists:
        return HTTPNoContent("bundle updated successfully")
    else:
        return HTTPCreated("bundle created successfully")


@changes.get(accept="application/json", renderer="json")
def fetch_changes(request):
    """Obtém a lista de mudanças, recebe os argumentos `since` e `limit`.
    """

    entity_route_name_map = {"Document": "documents"}

    def _format_change(c):
        result = {
            "id": request.route_path(
                entity_route_name_map[c["entity"]], document_id=c["id"]
            ),
            "timestamp": c["timestamp"],
        }

        if "deleted" in c:
            result["deleted"] = c["deleted"]

        return result

    since = request.GET.get("since", "")

    try:
        limit = int(request.GET.get("limit", 500))
    except ValueError:
        raise HTTPBadRequest("limit must be integer")

    return {
        "since": since,
        "limit": limit,
        "results": [
            _format_change(c)
            for c in request.services["fetch_changes"](since=since, limit=limit)
        ],
    }


@journals.put(
    schema=RegisterJournalSchema(),
    validators=(colander_body_validator,),
    accept="application/json",
    renderer="json",
)
def put_journal(request):
    """Registra um periódico a partir de dados submetidos e
    validados por meio do RegisterJournalSchema."""

    try:
        request.services["create_journal"](
            id=request.matchdict["journal_id"], metadata=request.validated
        )
    except exceptions.AlreadyExists:
        return HTTPNoContent("journal already exists")
    except (TypeError, ValueError) as err:
        return HTTPBadRequest(str(err))
    else:
        return HTTPCreated("journal created successfully")


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


class PlainTextRenderer:
    """Renderizador para dados do tipo ``text/plain``.

    Espera que o retorno da view-function seja uma string de bytes pronta para
    ser transferida para o cliente. Este renderer apenas define o content-type
    da resposta HTTP.
    """

    def __init__(self, info):
        pass

    def __call__(self, value, system):
        request = system.get("request")
        if request is not None:
            request.response.content_type = "text/plain"
        return value


DEFAULT_SETTINGS = [
    ("kernel.app.mongodb.dsn", "KERNEL_APP_MONGODB_DSN", str, "mongodb://db:27017/")
]


def parse_settings(settings, defaults=DEFAULT_SETTINGS):
    """Analisa e retorna as configurações da app com base no arquivo .ini e env.

    As variáveis de ambiente possuem precedência em relação aos valores
    definidos no arquivo .ini.

    O argumento `defaults` deve receber uma lista associativa na forma:
        
      [
        (<diretiva de config>, <variável de ambiente>, <função de conversão>, <valor padrão>),
      ]
    """
    parsed = {}
    cfg = list(defaults)

    for name, envkey, convert, default in cfg:
        value = os.environ.get(envkey, settings.get(name, default))
        if convert is not None:
            value = convert(value)
        parsed[name] = value

    return parsed


def main(global_config, **settings):
    settings.update(parse_settings(settings))
    config = Configurator(settings=settings)
    config.include("cornice")
    config.scan()
    config.add_renderer("xml", XMLRenderer)
    config.add_renderer("text", PlainTextRenderer)

    mongo = adapters.MongoDB(settings["kernel.app.mongodb.dsn"])
    Session = adapters.Session.partial(mongo)

    config.add_request_method(
        lambda request: services.get_handlers(Session), "services", reify=True
    )

    return config.make_wsgi_app()
