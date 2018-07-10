import itertools
from copy import deepcopy
from io import BytesIO

import requests
from lxml import etree

from . import manifest as _manifest


class BaseHTTPError(Exception):
    """A raíz das exceções relacionadas à HTTP"""


class HTTPConnectionError(BaseHTTPError):
    """Equivalente a ``requests.exceptions.ConnectionError``"""


class HTTPTimeout(BaseHTTPError):
    """Equivalente a ``requests.exceptions.Timeout``"""


class HTTPError(BaseHTTPError):
    """Equivalente a ``requests.exceptions.HTTPError``"""


class HTTPURLError(BaseHTTPError):
    """Equivalente a ``requests.exceptions.InvalidSchema``,
    ``requests.exceptions.InvalidURL`` e ``requests.exceptions.MissingSchema``
    """


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
        element.attrib["{http://www.w3.org/1999/xlink}href"] for element in elements
    ]


def assets_from_remote_xml(url: str, timeout: float = 2) -> list:
    try:
        response = requests.get(url, timeout=timeout)
    except requests.exceptions.ConnectionError as exc:
        raise HTTPConnectionError(exc) from None
    except requests.exceptions.Timeout as exc:
        raise HTTPTimeout(exc) from None
    except (
        requests.exceptions.InvalidSchema,
        requests.exceptions.MissingSchema,
        requests.exceptions.InvalidURL,
    ) as exc:
        raise HTTPURLError(exc) from None
    else:
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            raise HTTPError(exc) from None

    return get_static_assets(etree.parse(BytesIO(response.content)))


class Article:
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
        """Adiciona `data_url` como uma nova versão do artigo.

        :param data_url: é a URL para a nova versão do artigo.
        :param assets_getter: (optional) função que recebe 2 argumentos: a)
        a URL do XML do artigo e b) o timeout para a requisição. Deve ainda
        levantar as seguintes exceções: ``HTTPConnectionError`` quando não
        for possível estabelecer uma conexão, ``HTTPError`` quando a requisição
        retornar com código HTTP indicando falha, ``HTTPTimeout`` quando
        ``timeout`` for excedido e ``HTTPURLError``` quando a URL não for
        válida.
        """
        assets = assets_getter(data_url, timeout=timeout)
        self.manifest = _manifest.add_version(self._manifest, data_url, assets)

    def version(self, index=None) -> dict:
        index = index if index is not None else -1
        version = self.manifest["versions"][index]

        def _latest(uris):
            try:
                return uris[-1]
            except IndexError:
                return ""

        assets = {a: _latest(u) for a, u in version["assets"].items()}
        version["assets"] = assets
        return version

    def new_asset_version(self, asset_id, data) -> None:
        """Adiciona `data` como uma nova versão do ativo `asset_id` vinculado 
        a versão mais recente do artigo.

        :param asset_id: string identificando o ativo conforme aparece no XML.
        :param data: file-object de um ativo digital.
        """
