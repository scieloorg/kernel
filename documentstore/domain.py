import itertools
from copy import deepcopy
from io import BytesIO
import re

import requests
from lxml import etree

from . import manifest as _manifest
from . import exceptions

DEFAULT_XMLPARSER = etree.XMLParser(
    remove_blank_text=False,
    remove_comments=False,
    load_dtd=False,
    no_network=True,
    collect_ids=False,
)


def get_static_assets(xml_et):
    """Retorna uma lista das URIs dos ativos digitais de ``xml_et``.
    """
    paths = [
        "//graphic[@xlink:href]",
        "//media[@xlink:href]",
        "//inline-graphic[@xlink:href]",
        "//supplementary-material[@xlink:href]",
        "//inline-supplementary-material[@xlink:href]",
    ]

    iterators = [
        xml_et.iterfind(path, namespaces={"xlink": "http://www.w3.org/1999/xlink"})
        for path in paths
    ]

    elements = itertools.chain(*iterators)

    return [
        (element.attrib["{http://www.w3.org/1999/xlink}href"], element)
        for element in elements
    ]


def fetch_data(url: str, timeout: float = 2) -> bytes:
    try:
        response = requests.get(url, timeout=timeout)
    except (requests.ConnectionError, requests.Timeout) as exc:
        raise exceptions.RetryableError(exc) from exc
    except (requests.InvalidSchema, requests.MissingSchema, requests.InvalidURL) as exc:
        raise exceptions.NonRetryableError(exc) from exc
    else:
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            if 400 <= exc.response.status_code < 500:
                raise exceptions.NonRetryableError(exc) from exc
            elif 500 <= exc.response.status_code < 600:
                raise exceptions.RetryableError(exc) from exc
            else:
                raise

    return response.content


def assets_from_remote_xml(
    url: str, timeout: float = 2, parser=DEFAULT_XMLPARSER
) -> list:
    data = fetch_data(url, timeout)
    xml = etree.parse(BytesIO(data), parser)
    return xml, get_static_assets(xml)


class Document:
    _timestamp_pattern = (
        r"^[0-9]{4}-[0-9]{2}-[0-9]{2}(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z)?$"
    )

    def __init__(self, doc_id=None, manifest=None):
        assert any([doc_id, manifest])
        self.manifest = manifest or _manifest.new(doc_id)

    @property
    def manifest(self):
        return deepcopy(self._manifest)

    @manifest.setter
    def manifest(self, value):
        self._manifest = value

    def doc_id(self):
        return self.manifest.get("id", "")

    def new_version(
        self, data_url, assets_getter=assets_from_remote_xml, timeout=2
    ) -> None:
        """Adiciona `data_url` como uma nova versão do documento.

        :param data_url: é a URL para a nova versão do documento.
        :param assets_getter: (optional) função que recebe 2 argumentos: 1)
        a URL do XML do documento e 2) o timeout para a requisição e retorna 
        o par ``(xml, [(href, xml_node), ...]`` onde ``xml`` é uma instância
        de *element tree* da *lxml* e ``[(href, xml_node), ...]`` é uma lista
        que associa as URIs dos ativos com os nós do XML onde se encontram.
        Essa função deve ainda lançar as ``RetryableError`` e 
        ``NonRetryableError`` para representar problemas no acesso aos dados
        do XML.
        """
        try:
            latest_version = self.version()
        except ValueError:
            latest_version = {"data": ""}

        if latest_version.get("data") == data_url:
            raise exceptions.VersionAlreadySet(
                "could not add version: the version is equal to the latest one"
            )

        _, data_assets = assets_getter(data_url, timeout=timeout)
        data_assets_keys = [asset_key for asset_key, _ in data_assets]
        assets = self._link_assets(data_assets_keys)
        self.manifest = _manifest.add_version(self._manifest, data_url, assets)

    def _link_assets(self, tolink: list) -> dict:
        """Retorna um mapa entre as chaves dos ativos em `tolink` e as
        referências já existentes na última versão. 
        """
        try:
            latest_version = self.version()
        except ValueError:
            latest_version = {"assets": {}}

        return {
            asset_key: latest_version["assets"].get(asset_key, "")
            for asset_key in tolink
        }

    def version(self, index=-1) -> dict:
        try:
            version = self.manifest["versions"][index]
        except IndexError:
            raise ValueError("missing version for index: %s" % index) from None

        def _latest(uris):
            try:
                return uris[-1][1]
            except IndexError:
                return ""

        assets = {a: _latest(u) for a, u in version["assets"].items()}
        version["assets"] = assets
        return version

    def version_at(self, timestamp: str) -> dict:
        """Obtém os metadados da versão no momento `timestamp`.

        :param timestamp: string de texto do timestamp UTC ISO 8601 no formato
        `YYYY-MM-DDTHH:MM:SSSSSSZ`. A resolução pode variar desde o dia, e.g., 
        `2018-09-17`, dia horas e minutos, e.g., `2018-09-17T14:25Z`, ou dia 
        horas minutos segundos (e frações em até 6 casas decimais). Caso a 
        resolução esteja no nível do dia, a mesma será ajustada automaticamente 
        para o nível dos microsegundos por meio da concatenação da string 
        `T23:59:59:999999Z` ao valor de `timestamp`.
        """
        if not re.match(self._timestamp_pattern, timestamp):
            raise ValueError(
                "invalid format for timestamp: %s: must match pattern: %s"
                % (timestamp, self._timestamp_pattern)
            )

        if re.match(r"^\d{4}-\d{2}-\d{2}$", timestamp):
            timestamp = f"{timestamp}T23:59:59.999999Z"

        try:
            target_version = max(
                itertools.takewhile(
                    lambda version: version.get("timestamp", "") <= timestamp,
                    self.manifest["versions"],
                ),
                key=lambda version: version.get("timestamp"),
            )
        except ValueError:
            raise ValueError("missing version for timestamp: %s" % timestamp) from None

        def _at_time(uris):
            try:
                target = max(
                    itertools.takewhile(lambda asset: asset[0] <= timestamp, uris),
                    key=lambda asset: asset[0],
                )
            except ValueError:
                return ""
            return target[1]

        target_assets = {a: _at_time(u) for a, u in target_version["assets"].items()}
        target_version["assets"] = target_assets
        return target_version

    def data(
        self,
        version_index=-1,
        version_at=None,
        assets_getter=assets_from_remote_xml,
        timeout=2,
    ) -> bytes:
        """Retorna o conteúdo do XML, codificado em UTF-8, já com as 
        referências aos ativos digitais correspondendo às da versão solicitada.

        Por meio dos argumentos `version_index` e `version_at` é possível 
        explicitar a versão desejada a partir de 2 estratégias distintas: 
        `version_index` recebe um valor inteiro referente ao índice da versão
        desejada (pense no acesso a uma lista de versões). Já o argumento
        `version_at` recebe um timestamp UTC, em formato textual, e retorna
        a versão do documento naquele dado momento. Estes argumentos são
        mutuamente exclusivos, e `version_at` anula a presença do outro.

        Note que o argumento `version_at` é muito mais poderoso, uma vez que,
        diferentemente do `version_index`, também recupera o estado desejado 
        no nível dos ativos digitais do documento.
        """
        version = (
            self.version_at(version_at) if version_at else self.version(version_index)
        )
        xml_tree, data_assets = assets_getter(version["data"], timeout=timeout)

        version_assets = version["assets"]
        for asset_key, target_node in data_assets:
            version_href = version_assets.get(asset_key, "")
            target_node.attrib["{http://www.w3.org/1999/xlink}href"] = version_href

        return etree.tostring(xml_tree, encoding="utf-8", pretty_print=False)

    def new_asset_version(self, asset_id, data_url) -> None:
        """Adiciona `data_url` como uma nova versão do ativo `asset_id` vinculado 
        a versão mais recente do documento. É importante notar que nenhuma validação
        será executada em `data_url`.
        """
        try:
            latest_version = self.version()
        except ValueError:
            latest_version = {"assets": {}}

        if latest_version.get("assets", {}).get(asset_id) == data_url:
            raise exceptions.VersionAlreadySet(
                "could not add version: the version is equal to the latest one"
            )

        try:
            self.manifest = _manifest.add_asset_version(
                self._manifest, asset_id, data_url
            )
        except KeyError:
            raise ValueError(
                'cannot add version for "%s": unknown asset_id' % asset_id
            ) from None
