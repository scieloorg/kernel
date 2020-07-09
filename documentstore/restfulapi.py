import logging
import os
import base64
import pkg_resources

from pyramid.settings import asbool
from pyramid.config import Configurator
from pyramid.httpexceptions import (
    HTTPNotFound,
    HTTPNoContent,
    HTTPCreated,
    HTTPBadRequest,
    HTTPGone,
    HTTPUnprocessableEntity,
)
from cornice import Service
from cornice.validators import colander_body_validator, colander_validator
from cornice.service import get_services
import colander
from slugify import slugify
from cornice_swagger import CorniceSwagger
import sentry_sdk
from sentry_sdk.integrations.pyramid import PyramidIntegration

from . import services
from . import adapters
from . import exceptions

LOGGER = logging.getLogger(__name__)

VERSION = pkg_resources.get_distribution("scielo-kernel").version

swagger = Service(
    name="Kernel API", path="/__api__", description="Kernel API documentation"
)

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

bundles_documents = Service(
    name="bundles_documents",
    path="/bundles/{bundle_id}/documents",
    description="Update documents of documents bundle.",
)

changes = Service(
    name="changes", path="/changes", description="Get changes from all entities"
)

change_details = Service(
    name="change_details", path="/changes/{change_id}", description="Get one change."
)

journals = Service(
    name="journals",
    path="/journals/{journal_id}",
    description="Register and retrieve journals' endpoint",
)

journal_issues = Service(
    name="journal_issues",
    path="/journals/{journal_id}/issues",
    description="Issue addition and insertion to journal.",
)

journals_aop = Service(
    name="journals_aop",
    path="/journals/{journal_id}/aop",
    description="Manipulate ahead of print in journal",
)

renditions = Service(
    name="renditions",
    path="/documents/{document_id}/renditions",
    description="All renditions related to the document",
)


class ResponseSchema(colander.MappingSchema):
    body = colander.SchemaNode(colander.String(), missing=colander.drop)


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


class QueryDiffDocumentSchema(colander.MappingSchema):
    """Representa os parâmetros de querystring do schema DiffDocument.
    """

    from_when = colander.SchemaNode(colander.String(), missing=colander.drop)
    to_when = colander.SchemaNode(colander.String(), missing=colander.drop)


class DiffDocumentSchema(colander.MappingSchema):
    """Representa a diferença entre estados do documento
    """

    data = colander.SchemaNode(colander.String(), missing=colander.drop)
    querystring = QueryDiffDocumentSchema()


class AssetSchema(colander.MappingSchema):
    """Representa o schema de dados para registro de ativos do documento.
    """

    asset_url = colander.SchemaNode(colander.String(), validator=colander.url)


class JournalSchema(colander.MappingSchema):
    """Representa o schema de dados para registro de periódicos.
    """

    title = colander.SchemaNode(colander.String(), missing=colander.drop)

    @colander.instantiate(missing=colander.drop)
    class mission(colander.SequenceSchema):
        @colander.instantiate()
        class mission(colander.MappingSchema):
            language = colander.SchemaNode(colander.String())
            value = colander.SchemaNode(colander.String())

    title_iso = colander.SchemaNode(colander.String(), missing=colander.drop)
    short_title = colander.SchemaNode(colander.String(), missing=colander.drop)
    acronym = colander.SchemaNode(colander.String(), missing=colander.drop)
    scielo_issn = colander.SchemaNode(colander.String(), missing=colander.drop)
    print_issn = colander.SchemaNode(colander.String(), missing=colander.drop)
    electronic_issn = colander.SchemaNode(colander.String(), missing=colander.drop)

    @colander.instantiate(missing=colander.drop)
    class status_history(colander.SequenceSchema):
        status = colander.SchemaNode(
            colander.Mapping(unknown="preserve"), missing=colander.drop
        )

    @colander.instantiate(missing=colander.drop)
    class subject_areas(colander.SequenceSchema):
        name = colander.SchemaNode(colander.String())

    @colander.instantiate(missing=colander.drop)
    class sponsors(colander.SequenceSchema):
        sponsor = colander.SchemaNode(colander.Mapping(unknown="preserve"))

    metrics = colander.SchemaNode(
        colander.Mapping(unknown="preserve"), missing=colander.drop
    )

    @colander.instantiate(missing=colander.drop)
    class subject_categories(colander.SequenceSchema):
        name = colander.SchemaNode(colander.String())

    @colander.instantiate(missing=colander.drop)
    class institution_responsible_for(colander.SequenceSchema):
        @colander.instantiate()
        class institution(colander.MappingSchema):
            name = colander.SchemaNode(colander.String())
            city = colander.SchemaNode(colander.String())
            state = colander.SchemaNode(colander.String())
            country_code = colander.SchemaNode(colander.String())
            country = colander.SchemaNode(colander.String())

    online_submission_url = colander.SchemaNode(
        colander.String(), validator=colander.url, missing=colander.drop
    )
    next_journal = colander.SchemaNode(
        colander.Mapping(unknown="preserve"), missing=colander.drop
    )
    previous_journal = colander.SchemaNode(
        colander.Mapping(unknown="preserve"), missing=colander.drop
    )
    contact = colander.SchemaNode(
        colander.Mapping(unknown="preserve"), missing=colander.drop
    )


class JournalAOPSchema(colander.MappingSchema):
    """Representa o schema de dados para a atualização de AOP em periódico
    """

    aop = colander.SchemaNode(colander.String())


class DocumentsBundleSchema(colander.MappingSchema):
    """Representa o schema de dados para registro de Documents Bundle."""

    def combined_validator(node, value):
        if value.get("month") and value.get("range"):
            raise colander.Invalid(
                node, "The month and range fields are mutually exclusive."
            )

    @colander.instantiate(missing=colander.drop, validator=combined_validator)
    class publication_months(colander.MappingSchema):
        month = colander.SchemaNode(colander.Int(), missing=colander.drop)

        @colander.instantiate(missing=colander.drop)
        class range(colander.TupleSchema):
            start_month = colander.SchemaNode(colander.Int(), missing=colander.drop)
            end_month = colander.SchemaNode(colander.Int(), missing=colander.drop)

    publication_year = colander.SchemaNode(colander.Int(), missing=colander.drop)
    supplement = colander.SchemaNode(colander.String(), missing=colander.drop)
    volume = colander.SchemaNode(colander.String(), missing=colander.drop)
    number = colander.SchemaNode(colander.String(), missing=colander.drop)
    pid = colander.SchemaNode(colander.String(), missing=colander.drop)

    @colander.instantiate(missing=colander.drop)
    class titles(colander.SequenceSchema):
        @colander.instantiate()
        class title(colander.MappingSchema):
            language = colander.SchemaNode(
                colander.String(), validator=colander.Length(2, 2)
            )
            value = colander.SchemaNode(colander.String(), validator=colander.Length(1))


class DocumentsBundleDocumentsReplaceSchemaPayload(colander.SequenceSchema):
    """Representa o schema de dados para registro o relacionamento de documento no
    Documents Bundle."""

    @colander.instantiate(missing=colander.drop)
    class document(colander.MappingSchema):
        id = colander.SchemaNode(colander.String())
        order = colander.SchemaNode(colander.String())


class DocumentsBundleDocumentsReplaceSchema(colander.MappingSchema):
    """A partir da versão 4.0 o Cornice passou a operar apenas com instâncias
    de `colander.MappingSchema`, e é por isso que este *wrapper* teve que ser
    implementado. Mais detalhes em:
      * https://github.com/scieloorg/kernel/issues/221
      * https://cornice.readthedocs.io/en/latest/upgrading.html?highlight=colander_validator#x-to-4-x
      * https://cornice.readthedocs.io/en/latest/upgrading.html?highlight=colander_validator#complex-colander-validation
    """

    body = DocumentsBundleDocumentsReplaceSchemaPayload()


class QueryChangeSchema(colander.MappingSchema):
    """Representa os parâmetros de querystring do schema change.
    """

    limit = colander.SchemaNode(colander.String(), missing=colander.drop)
    since = colander.SchemaNode(colander.String(), missing=colander.drop)


class ChangeSchema(colander.MappingSchema):
    """Representa o schema de dados para registro de mudança.
    """

    id = colander.SchemaNode(colander.String())
    timestamp = colander.SchemaNode(colander.String())
    deleted = colander.SchemaNode(colander.Boolean())
    querystring = QueryChangeSchema()


class ChangeDetailsSchema(colander.MappingSchema):
    """Representa o schema de dados para os detalhes de um registro de mudança.
    """

    data = colander.SchemaNode(colander.String(), missing=colander.drop)


class ManifestSchema(colander.MappingSchema):
    """Representa o schema de dados do registro de Manifest
    """

    data = colander.SchemaNode(colander.String(), missing=colander.drop)


class QueryDocumentSchema(colander.MappingSchema):
    """Representa os parâmetros de querystring do schema document.
    """

    when = colander.SchemaNode(colander.String(), missing=colander.drop)


class DocumentSchema(colander.MappingSchema):
    """Representa o schema de dados do documento.
    """

    data = colander.SchemaNode(colander.String(), missing=colander.drop)
    assets = Assets()
    querystring = QueryDocumentSchema()


class DeleteDocumentSchema(colander.MappingSchema):
    """Representa o schema de dados front do documento.
    """

    data = colander.SchemaNode(colander.String(), missing=colander.drop)


class FrontDocumentSchema(colander.MappingSchema):
    """Representa o schema de dados front do documento.
    """

    data = colander.SchemaNode(colander.String(), missing=colander.drop)


class JournalIssueItem(colander.MappingSchema):
    """Schema que representa uma Issue como item a ser relacionado
    com um Journal"""

    id = colander.SchemaNode(colander.String())
    order = colander.SchemaNode(colander.String(), missing=colander.drop)
    year = colander.SchemaNode(colander.String())
    volume = colander.SchemaNode(colander.String(), missing=colander.drop)
    number = colander.SchemaNode(colander.String(), missing=colander.drop)
    supplement = colander.SchemaNode(colander.String(), missing=colander.drop)


class JournalIssuesSchema(colander.MappingSchema):
    """Representa o schema de dados de atualização de fascículos de periódico.
    """

    issue = JournalIssueItem()
    index = colander.SchemaNode(colander.Int(), missing=colander.drop)


class JournalIssuesReplaceSchemaPayload(colander.SequenceSchema):
    """Representa o schema de dados utilizado durante a atualização
    da lista completa de fascículos de um periódico"""

    issue = JournalIssueItem()


class JournalIssuesReplaceSchema(colander.MappingSchema):
    """A partir da versão 4.0 o Cornice passou a operar apenas com instâncias
    de `colander.MappingSchema`, e é por isso que este *wrapper* teve que ser
    implementado. Mais detalhes em:
      * https://github.com/scieloorg/kernel/issues/221
      * https://cornice.readthedocs.io/en/latest/upgrading.html?highlight=colander_validator#x-to-4-x
      * https://cornice.readthedocs.io/en/latest/upgrading.html?highlight=colander_validator#complex-colander-validation
    """

    body = JournalIssuesReplaceSchemaPayload()


class DeleteJournalIssuesSchema(colander.MappingSchema):
    """Representa o schema de dados de deleção de fascículos de periódico.
    """

    issue = colander.SchemaNode(colander.String())


class DocumentRenditionsSchema(colander.MappingSchema):
    """Representa o schema de dados da manifestação do documento.
    """

    data = colander.SchemaNode(colander.String(), missing=colander.drop)
    querystring = QueryDocumentSchema()


class RegisterDocumentRenditionSchema(colander.MappingSchema):
    """Representa o schema de dados para registro de manifestações do documento.
    """

    filename = colander.SchemaNode(colander.String())
    data_url = colander.SchemaNode(colander.String(), validator=colander.url)
    mimetype = colander.SchemaNode(colander.String())
    lang = colander.SchemaNode(colander.String())
    size_bytes = colander.SchemaNode(colander.Int())


@documents.get(
    schema=DocumentSchema(),
    response_schemas={
        "200": DocumentSchema(description="Obtém o documento"),
        "404": DocumentSchema(description="Documento não encontrado"),
    },
    accept="text/xml",
    renderer="xml",
)
def fetch_document_data(request):
    """Obtém o conteúdo do documento representado em XML com todos os
    apontamentos para seus ativos digitais contextualizados de acordo com a
    versão do documento. Produzirá uma resposta com o código HTTP 404 caso o
    documento solicitado não seja conhecido pela aplicação.
    """
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
    except exceptions.DeletedVersion as exc:
        raise HTTPGone(exc)


@documents.put(
    schema=RegisterDocumentSchema(),
    validators=(colander_body_validator,),
    response_schemas={
        "201": RegisterDocumentSchema(description="Documento criado com sucesso"),
        "204": RegisterDocumentSchema(description="Documento atualizado com sucesso"),
    },
)
def put_document(request):
    """Adiciona ou atualiza registro de documento. A atualização do documento é
    idempotente.

    A semântica desta view-function está definida conforme a especificação:
    https://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html#sec9.6

    Em resumo, ``PUT /documents/:doc_id`` com o payload válido de acordo com o
    schema documentado, e para um ``:doc_id`` inédito, resultará no registro do
    documento e produzirá uma resposta com o código HTTP 201 Created. Qualquer
    requisição subsequente para o mesmo recurso produzirá respostas com o código
    HTTP 204 No Content.
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


@documents.delete(
    schema=DeleteDocumentSchema(),
    response_schemas={
        "204": DeleteDocumentSchema(description="Documento excluído com sucesso"),
        "404": DeleteDocumentSchema(description="Documento não encontrado"),
    },
)
def delete_document(request):
    """Adiciona uma nova versão ao documento indicando que o mesmo foi excluído.
    """
    try:
        request.services["delete_document"](id=request.matchdict["document_id"])
    except exceptions.DoesNotExist as exc:
        raise HTTPNotFound(exc)
    except exceptions.VersionAlreadySet as exc:
        LOGGER.info(
            'skipping request to add deleted version to "%s": %s',
            request.matchdict["document_id"],
            exc,
        )
    raise HTTPNoContent("document deleted successfully")


@manifest.get(
    schema=ManifestSchema(),
    response_schemas={
        "200": ManifestSchema(description="Obtém o manifesto do documento"),
        "404": ManifestSchema(description="Manifesto não encontrado"),
    },
    accept="application/json",
    renderer="json",
)
def get_manifest(request):
    """Obtém o manifesto do documento. Produzirá uma resposta com o código
    HTTP 404 caso o documento não seja conhecido pela aplicação.
    """
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


@assets_list.get(
    accept="application/json",
    renderer="json",
    response_schemas={
        "200": Assets(description="Lista de ativos"),
        "404": Assets(description="Documento não encontrado"),
    },
)
def get_assets_list(request):
    """Obtém relação dos ativos associados ao documento em determinada
    versão. Produzirá uma resposta com o código HTTP 404 caso o documento não
    seja conhecido pela aplicação.
    """
    try:
        assets = request.services["fetch_assets_list"](
            id=request.matchdict["document_id"]
        )
    except exceptions.DoesNotExist as exc:
        raise HTTPNotFound(exc)

    assets["assets"] = slugify_assets_ids(assets["assets"])
    return assets


@assets.put(
    schema=AssetSchema(),
    validators=(colander_body_validator,),
    response_schemas={
        "204": AssetSchema(
            description="Adicionado ou atualizado o ativo digital com sucesso"
        ),
        "404": AssetSchema(description="Ativo não encontrado"),
    },
)
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


@diff.get(
    schema=DiffDocumentSchema(),
    response_schemas={
        "200": DiffDocumentSchema(
            description="Retorna a diferança do documento, recebe os argumentos `from_when` e `to_when`"
        ),
        "400": DiffDocumentSchema(
            description="Erro ao tentar processar a requisição, verifique o valor do parâmetro `from_when`"
        ),
        "404": DiffDocumentSchema(description="Documento não encontrado"),
    },
    renderer="text",
)
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
    except exceptions.DeletedVersion as exc:
        raise HTTPGone(exc)


@front.get(
    schema=FrontDocumentSchema(),
    response_schemas={
        "200": FrontDocumentSchema(
            description="Retorna o Front do documento (todo os dados do documento exceto o body)"
        ),
        "404": FrontDocumentSchema(description="Front do documento não encontrado"),
    },
    renderer="json",
)
def fetch_document_front(request):
    data = fetch_document_data(request)
    return request.services["sanitize_document_front"](data)


@bundles.get(
    response_schemas={
        "200": DocumentsBundleSchema(
            description="Retorna os dados do bundle  solicitado"
        ),
        "404": DocumentsBundleSchema(description="Recurso não encontrado"),
        "400": DocumentsBundleSchema(
            description="Erro ao processar a requisição. Verifique o parâmetro `bundle_id`"
        ),
    },
    renderer="json",
)
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
    response_schemas={
        "201": DocumentsBundleSchema(
            description="Documents Bundle criado com sucesso."
        ),
        "204": DocumentsBundleSchema(
            description="Documents Bundle atualizado com sucesso."
        ),
    },
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


@bundles.patch(
    schema=DocumentsBundleSchema(),
    response_schemas={
        "204": DocumentsBundleSchema(
            description="Documents Bundle atualizado com sucesso."
        ),
        "404": DocumentsBundleSchema(description="Documents Bundle não encontrado."),
    },
    validators=(colander_body_validator,),
    accept="application/json",
    renderer="json",
)
def patch_documents_bundle(request):
    try:
        request.services["update_documents_bundle_metadata"](
            request.matchdict["bundle_id"], metadata=request.validated
        )
    except exceptions.DoesNotExist as exc:
        return HTTPNotFound(str(exc))
    else:
        return HTTPNoContent("bundle updated successfully")


@bundles_documents.put(
    schema=DocumentsBundleDocumentsReplaceSchema(),
    validators=(colander_validator,),
    response_schemas={
        "204": DocumentsBundleDocumentsReplaceSchema(
            description="Lista de documentos atualizada com sucesso"
        ),
        "422": DocumentsBundleDocumentsReplaceSchema(
            description="Erro ao atualizar a lista de documetos. Payload com conteúdo inválido."
        ),
        "404": DocumentsBundleDocumentsReplaceSchema(
            description="Fascículo não encontrado"
        ),
    },
    accept="application/json",
    renderer="json",
)
def put_bundles_documents(request):
    try:
        request.services["update_documents_in_documents_bundle"](
            id=request.matchdict["bundle_id"], docs=request.validated["body"]
        )
    except exceptions.DoesNotExist as exc:
        return HTTPNotFound(str(exc))
    except exceptions.AlreadyExists as exc:
        return HTTPUnprocessableEntity(
            explanation="cannot process the request with duplicated items."
        )

    return HTTPNoContent("documents list updated successfully.")


entity_route_map = {
    "Document": {"route": "documents", "marker": "document_id"},
    "DocumentRendition": {"route": "renditions", "marker": "document_id"},
    "Journal": {"route": "journals", "marker": "journal_id"},
    "DocumentsBundle": {"route": "bundles", "marker": "bundle_id"},
}


def _format_change(c, request):
    """Transforma um registro de mudança em algo mais *palatável* para ser
    retornado por uma interface restful.
    """
    entity = entity_route_map[c["entity"]]
    result = {
        "id": request.route_path(entity["route"], **{entity["marker"]: c["id"]}),
        "timestamp": c["timestamp"],
    }
    if "_id" in c:
        result["change_id"] = str(c["_id"])
    if "deleted" in c:
        result["deleted"] = c["deleted"]
    if "content_gz" in c:
        result["content_gz_b64"] = base64.b64encode(c["content_gz"]).decode("ascii")
    if "content_type" in c:
        result["content_type"] = c["content_type"]

    return result


@changes.get(
    schema=ChangeSchema(),
    response_schemas={
        "200": AssetSchema(description="Retorna a lista de mudanças"),
        "400": AssetSchema(
            description="Erro ao processar a requisição, verifique o parâmetro `limit`"
        ),
    },
    accept="application/json",
    renderer="json",
)
def fetch_changes(request):
    """Obtém a lista de mudanças, recebe os argumentos `since` e `limit`.
    """
    since = request.GET.get("since", "")

    try:
        limit = int(request.GET.get("limit", 500))
    except ValueError:
        raise HTTPBadRequest("limit must be integer")

    return {
        "since": since,
        "limit": limit,
        "results": [
            _format_change(c, request)
            for c in request.services["fetch_changes"](since=since, limit=limit)
        ],
    }


@change_details.get(
    schema=ChangeDetailsSchema(),
    response_schemas={
        "200": ChangeDetailsSchema(description="Retorna o registro da mudança"),
        "404": ChangeDetailsSchema(description="Registro não encontrado"),
    },
    accept="application/json",
    renderer="json",
)
def fetch_change(request):
    """Obtém um único registro de mudança.

    Este endpoint é capaz de retornar o `snapshot` dos dados no momento
    imediatamente após sua mudança.
    """
    try:
        return _format_change(
            request.services["fetch_change"](id=request.matchdict["change_id"]), request
        )
    except exceptions.DoesNotExist as exc:
        return HTTPNotFound(exc)


@journals.put(
    schema=JournalSchema(),
    validators=(colander_body_validator,),
    response_schemas={
        "201": JournalSchema(description="Periódico criado com sucesso"),
        "204": JournalSchema(
            description="Não foi realizada alteração para o periódico informado"
        ),
        "400": JournalSchema(
            description="Erro ao processar a requisição, por favor verifique os dados informados"
        ),
    },
    accept="application/json",
    renderer="json",
)
def put_journal(request):
    """Registra um periódico a partir de dados submetidos e
    validados por meio do JournalSchema."""
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


@journals.get(
    schema=JournalSchema(),
    response_schemas={
        "200": JournalSchema(description="Retorna um periódico"),
        "404": JournalSchema(description="Periódico não encontrado"),
    },
    accept="application/json",
    renderer="json",
)
def get_journal(request):
    """Recupera um periódico por meio de seu identificador
    """

    try:
        return request.services["fetch_journal"](id=request.matchdict["journal_id"])
    except exceptions.DoesNotExist:
        return HTTPNotFound(
            'cannot fetch journal with id "%s"' % request.matchdict["journal_id"]
        )


@journals.patch(
    schema=JournalSchema,
    validators=(colander_body_validator,),
    response_schemas={
        "204": JournalSchema(description="Periódico atualizado com sucesso"),
        "400": JournalSchema(
            description="Erro ao tentar processar a requisição, verifique os dados submetidos"
        ),
        "404": JournalSchema(description="Periódico não encontrado"),
    },
    accept="application/json",
    renderer="json",
)
def patch_journal(request):
    """Atualiza um periódico a partir dos dados fornecidos e
    validados por meio do JournalSchema.
    """

    try:
        request.services["update_journal_metadata"](
            id=request.matchdict["journal_id"], metadata=request.validated
        )
    except (TypeError, ValueError) as exc:
        return HTTPBadRequest(str(exc))
    except exceptions.DoesNotExist:
        return HTTPNotFound(
            'cannot fetch journal with id "%s"' % request.matchdict["journal_id"]
        )

    return HTTPNoContent("journal updated successfully")


@journal_issues.patch(
    schema=JournalIssuesSchema(),
    validators=(colander_body_validator,),
    response_schemas={
        "204": JournalIssuesSchema(
            description="Fascículo adicionado ou inserido em periódico com sucesso"
        ),
        "404": JournalIssuesSchema(description="Periódico não encontrado"),
    },
    accept="application/json",
    renderer="json",
)
def patch_journal_issues(request):
    try:
        if request.validated.get("index") is not None:
            request.services["insert_issue_to_journal"](
                id=request.matchdict["journal_id"],
                index=request.validated["index"],
                issue=request.validated["issue"],
            )
        else:
            request.services["add_issue_to_journal"](
                id=request.matchdict["journal_id"], issue=request.validated["issue"]
            )
    except exceptions.DoesNotExist as exc:
        return HTTPNotFound(str(exc))
    except exceptions.AlreadyExists as exc:
        return HTTPNoContent("issue added to journal successfully.")
    else:
        return HTTPNoContent("issue added to journal successfully.")


@journal_issues.put(
    schema=JournalIssuesReplaceSchema(),
    validators=(colander_validator,),
    response_schemas={
        "204": JournalIssuesReplaceSchema(
            description="Lista de fascículos atualizada com sucesso"
        ),
        "422": JournalIssuesReplaceSchema(
            description="Erro ao atualizar a lista de issues. Payload com conteúdo inválido."
        ),
        "404": JournalIssuesReplaceSchema(description="Periódico não encontrado"),
    },
    accept="application/json",
    renderer="json",
)
def put_journal_issues(request):
    try:
        request.services["update_issues_in_journal"](
            id=request.matchdict["journal_id"], issues=request.validated["body"]
        )
    except exceptions.DoesNotExist as exc:
        return HTTPNotFound(str(exc))
    except exceptions.AlreadyExists as exc:
        return HTTPUnprocessableEntity(
            explanation="cannot process the request with duplicated items."
        )

    return HTTPNoContent("issues list updated successfully.")


@journals_aop.patch(
    schema=JournalAOPSchema,
    validators=(colander_body_validator,),
    response_schemas={
        "204": JournalAOPSchema(
            description="Ahead of Print adicionado ao periódico com sucesso ao periódico"
        ),
        "404": JournalAOPSchema(description="Periódico não encontrado"),
    },
    accept="application/json",
    renderer="json",
)
def patch_journal_aop(request):
    try:
        request.services["set_ahead_of_print_bundle_to_journal"](
            id=request.matchdict["journal_id"], aop=request.validated["aop"]
        )
    except exceptions.DoesNotExist:
        return HTTPNotFound(
            'cannot find journal with id "%s"' % request.matchdict["journal_id"]
        )

    return HTTPNoContent("aop added to journal successfully")


@journals_aop.delete(
    validators=(colander_body_validator,),
    response_schemas={
        "204": ResponseSchema(
            description="Ahead of Print removido do periódico com sucesso"
        ),
        "404": ResponseSchema(description="Periódico não encontrado"),
    },
    accept="application/json",
    renderer="json",
)
def delete_journal_aop(request):
    try:
        request.services["remove_ahead_of_print_bundle_from_journal"](
            id=request.matchdict["journal_id"]
        )
    except exceptions.DoesNotExist as exc:
        return HTTPNotFound(str(exc))
    return HTTPNoContent()


@journal_issues.delete(
    schema=DeleteJournalIssuesSchema(),
    validators=(colander_body_validator,),
    response_schemas={
        "204": DeleteJournalIssuesSchema(
            description="Fascículo removido em periódico com sucesso"
        ),
        "404": DeleteJournalIssuesSchema(
            description="Periódico ou fascículo não encontrado"
        ),
    },
    accept="application/json",
    renderer="json",
)
def delete_journal_issues(request):
    try:
        request.services["remove_issue_from_journal"](
            id=request.matchdict["journal_id"], issue=request.validated["issue"]
        )
    except exceptions.DoesNotExist as exc:
        return HTTPNotFound(str(exc))
    else:
        return HTTPNoContent("issue removed from journal successfully.")


@renditions.get(
    schema=DocumentRenditionsSchema(),
    response_schemas={
        "200": DocumentRenditionsSchema(
            description="Obtém a lista das manifestações do documento"
        ),
        "404": DocumentRenditionsSchema(description="Documento não encontrado"),
    },
    accept="application/json",
    renderer="json",
)
def fetch_document_renditions(request):
    """Obtém uma lista das manifestações associadas à versão do documento.
    Produzirá uma resposta com o código HTTP 404 caso o documento solicitado
    não exista.
    """
    when = request.GET.get("when", None)
    if when:
        version = {"version_at": when}
    else:
        version = {}
    try:
        return request.services["fetch_document_renditions"](
            id=request.matchdict["document_id"], **version
        )
    except (exceptions.DoesNotExist, ValueError) as exc:
        raise HTTPNotFound(exc)


@renditions.patch(
    schema=RegisterDocumentRenditionSchema(),
    validators=(colander_body_validator,),
    response_schemas={
        "204": RegisterDocumentRenditionSchema(
            description="Manifestação registrada com sucesso"
        ),
        "404": RegisterDocumentRenditionSchema(description="Documento não encontrado"),
    },
    accept="application/json",
    renderer="json",
)
def register_rendition_version(request):
    try:
        request.services["register_rendition_version"](
            request.matchdict["document_id"],
            request.validated["filename"],
            request.validated["data_url"],
            request.validated["mimetype"],
            request.validated["lang"],
            request.validated["size_bytes"],
        )
    except exceptions.DoesNotExist as exc:
        return HTTPNotFound(exc)
    except exceptions.VersionAlreadySet as exc:
        LOGGER.info(
            'skipping request to add new version of rendition "%s" to "%s": %s',
            request.validated["filename"],
            request.matchdict["document_id"],
            exc,
        )

    return HTTPNoContent("journal updated successfully")


@swagger.get()
def openAPI_spec(request):
    doc = CorniceSwagger(get_services())
    doc.summary_docstrings = True
    return doc.generate("Kernel", "0.1")


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


def split_dsn(dsns):
    """Produz uma lista de DSNs a partir de uma string separada de DSNs separados
    por espaços ou quebras de linha. A escolha dos separadores se baseia nas
    convenções do framework Pyramid.
    """
    return [dsn.strip() for dsn in str(dsns).split() if dsn]


DEFAULT_SETTINGS = [
    (
        "kernel.app.mongodb.dsn",
        "KERNEL_APP_MONGODB_DSN",
        split_dsn,
        "mongodb://db:27017/",
    ),
    ("kernel.app.mongodb.replicaset", "KERNEL_APP_MONGODB_REPLICASET", str, ""),
    (
        "kernel.app.mongodb.readpreference",
        "KERNEL_APP_MONGODB_READPREFERENCE",
        str,
        "secondaryPreferred",
    ),
    ("kernel.app.mongodb.dbname", "KERNEL_APP_MONGODB_DBNAME", str, "document-store"),
    ("kernel.app.prometheus.enabled", "KERNEL_APP_PROMETHEUS_ENABLED", asbool, True),
    ("kernel.app.prometheus.port", "KERNEL_APP_PROMETHEUS_PORT", int, 8087),
    ("kernel.app.sentry.enabled", "KERNEL_APP_SENTRY_ENABLED", asbool, False),
    ("kernel.app.sentry.dsn", "KERNEL_APP_SENTRY_DSN", str, ""),
    ("kernel.app.sentry.environment", "KERNEL_APP_SENTRY_ENVIRONMENT", str, ""),
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
    config.include("cornice_swagger")
    config.include("documentstore.pyramid_prometheus")
    config.scan()
    config.add_renderer("xml", XMLRenderer)
    config.add_renderer("text", PlainTextRenderer)

    mongo = adapters.MongoDB(
        settings["kernel.app.mongodb.dsn"],
        settings["kernel.app.mongodb.dbname"],
        options={
            "replicaSet": settings["kernel.app.mongodb.replicaset"],
            "readPreference": settings["kernel.app.mongodb.readpreference"],
        },
    )
    Session = adapters.Session.partial(mongo)

    config.add_request_method(
        lambda request: services.get_handlers(Session), "services", reify=True
    )

    if settings["kernel.app.sentry.enabled"]:
        if settings["kernel.app.sentry.dsn"]:
            sentry_sdk.init(
                dsn=settings["kernel.app.sentry.dsn"],
                integrations=[PyramidIntegration(transaction_style="route_pattern")],
                release=f"scielo-kernel@{VERSION}",
                environment=settings["kernel.app.sentry.environment"],
            )
        else:
            LOGGER.info("cannot setup Sentry: the dsn was not provided")

    return config.make_wsgi_app()
