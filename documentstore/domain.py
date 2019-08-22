import itertools
from copy import deepcopy
from io import BytesIO
import re
from typing import Union, Callable, Any, Tuple, List
from datetime import datetime
import time
import os
import functools
import logging

import requests
from lxml import etree
from prometheus_client import Counter, Summary

from . import exceptions

__all__ = ["Document"]

LOGGER = logging.getLogger(__name__)

DEFAULT_XMLPARSER = etree.XMLParser(
    remove_blank_text=False,
    remove_comments=False,
    load_dtd=False,
    no_network=True,
    collect_ids=False,
)

SUBJECT_AREAS = (
    "Agricultural Sciences",
    "Applied Social Sciences",
    "Biological Sciences",
    "Engineering",
    "Exact and Earth Sciences",
    "Health Sciences",
    "Human Sciences",
    "Linguistics, Letters and Arts"
)

MAX_RETRIES = int(os.environ.get("KERNEL_LIB_MAX_RETRIES", "4"))
BACKOFF_FACTOR = float(os.environ.get("KERNEL_LIB_BACKOFF_FACTOR", "1.2"))
OBJECTSTORE_RESPONSE_TIME_SECONDS = Summary(
    "kernel_objectstore_response_time_seconds",
    "Elapsed time between the request for an XML and the response",
)
OBJECTSTORE_REQUEST_FAILURES_TOTAL = Counter(
    "kernel_objectstore_request_failures_total",
    "Total number of exceptions raised when requesting for an XML from the object-store",
)


def utcnow():
    return str(datetime.utcnow().isoformat() + "Z")


class DocumentManifest:
    """Namespace para funções que manipulam o manifesto do documento.
    """

    @staticmethod
    def new(id: str) -> dict:
        return {"id": str(id), "versions": []}

    def _new_version(
        data_uri: str, assets: Union[dict, list], now: Callable[[], str]
    ) -> dict:
        _assets = {str(aid): [] for aid in assets}
        return {
            "data": data_uri,
            "assets": _assets,
            "timestamp": now(),
            "renditions": [],
        }

    @staticmethod
    def add_version(
        manifest: dict,
        data_uri: str,
        assets: Union[dict, list],
        renditions: Union[dict, list] = None,
        now: Callable[[], str] = utcnow,
    ) -> dict:
        _manifest = deepcopy(manifest)
        version = DocumentManifest._new_version(data_uri, assets, now=now)
        for asset_id in assets:
            try:
                asset_uri = assets[asset_id]
            except TypeError:
                break
            else:
                if asset_uri:
                    version = DocumentManifest._new_asset_version(
                        version, asset_id, asset_uri, now=now
                    )
        _manifest["versions"].append(version)
        return _manifest

    def _new_asset_version(
        version: dict, asset_id: str, asset_uri: str, now: Callable[[], str] = utcnow
    ) -> dict:
        _version = deepcopy(version)
        _version["assets"][asset_id].append((now(), asset_uri))
        return _version

    @staticmethod
    def add_asset_version(
        manifest: dict, asset_id: str, asset_uri: str, now: Callable[[], str] = utcnow
    ) -> dict:
        _manifest = deepcopy(manifest)
        _manifest["versions"][-1] = DocumentManifest._new_asset_version(
            _manifest["versions"][-1], asset_id, asset_uri, now=now
        )
        return _manifest

    @staticmethod
    def add_rendition_version(
        manifest: dict,
        filename: str,
        data_uri: str,
        mimetype: str,
        lang: str,
        size_bytes: int,
        now: Callable[[], str] = utcnow,
    ) -> dict:
        _manifest = deepcopy(manifest)
        latest_renditions = _manifest["versions"][-1]["renditions"]
        try:
            selected_rendition = [
                r
                for r in latest_renditions
                if r["filename"] == filename
                and r["lang"] == lang
                and r["mimetype"] == mimetype
            ][0]
        except IndexError:
            selected_rendition = {
                "filename": filename,
                "data": [],
                "mimetype": mimetype,
                "lang": lang,
            }
            latest_renditions.append(selected_rendition)

        selected_rendition["data"].append(
            {"timestamp": now(), "url": data_uri, "size_bytes": size_bytes}
        )
        return _manifest

    @staticmethod
    def add_deleted_version(manifest: dict, now: Callable[[], str] = utcnow) -> dict:
        _manifest = deepcopy(manifest)
        _manifest["versions"].append({"deleted": True, "timestamp": now()})
        return _manifest


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


class retry_gracefully:
    """Produz decorador que torna o objeto decorado resiliente às exceções dos
    tipos informados em `exc_list`. Tenta no máximo `max_retries` vezes com
    intervalo exponencial entre as tentativas.
    """

    def __init__(
        self,
        max_retries=MAX_RETRIES,
        backoff_factor=BACKOFF_FACTOR,
        exc_list=(exceptions.RetryableError,),
    ):
        self.max_retries = int(max_retries)
        self.backoff_factor = float(backoff_factor)
        self.exc_list = tuple(exc_list)

    def _sleep(self, seconds):
        time.sleep(seconds)

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retry = 1
            while True:
                try:
                    return func(*args, **kwargs)
                except self.exc_list as exc:
                    if retry <= self.max_retries:
                        wait_seconds = self.backoff_factor ** retry
                        LOGGER.info(
                            'could not get the result for "%s" with *args "%s" '
                            'and **kwargs "%s". retrying in %s seconds '
                            "(retry #%s): %s",
                            func.__qualname__,
                            args,
                            kwargs,
                            str(wait_seconds),
                            retry,
                            exc,
                        )
                        self._sleep(wait_seconds)
                        retry += 1
                    else:
                        raise

        return wrapper


@retry_gracefully()
@OBJECTSTORE_REQUEST_FAILURES_TOTAL.count_exceptions()
@OBJECTSTORE_RESPONSE_TIME_SECONDS.time()
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

    def __init__(self, id=None, manifest=None):
        assert any([id, manifest])
        self.manifest = manifest or DocumentManifest.new(id)

    @property
    def manifest(self):
        return deepcopy(self._manifest)

    @manifest.setter
    def manifest(self, value):
        self._manifest = value

    def id(self):
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
        latest_version = self._latest_or_default()
        if latest_version.get("data") == data_url:
            raise exceptions.VersionAlreadySet(
                "could not add version: the version is equal to the latest one"
            )

        _, data_assets = assets_getter(data_url, timeout=timeout)
        data_assets_keys = [asset_key for asset_key, _ in data_assets]
        assets = self._link_assets(data_assets_keys)
        self.manifest = DocumentManifest.add_version(self._manifest, data_url, assets)

    def _link_assets(self, tolink: list) -> dict:
        """Retorna um mapa entre as chaves dos ativos em `tolink` e as
        referências já existentes na última versão.
        """
        latest_version = self._latest_or_default()
        assets = latest_version.get("assets", {})
        return {asset_key: assets.get(asset_key, "") for asset_key in tolink}

    def version(self, index=-1) -> dict:
        try:
            version = self.manifest["versions"][index]
        except IndexError:
            raise ValueError("missing version for index: %s" % index) from None

        if version.get("deleted"):
            return version

        def _latest(uris):
            try:
                return uris[-1][1]
            except IndexError:
                return ""

        def _safe_eval(expr, default=""):
            try:
                return expr()
            except (KeyError, IndexError):
                return default

        def _latest_renditions(r):
            return {
                "filename": _safe_eval(lambda: r["filename"]),
                "url": _safe_eval(lambda: r["data"][-1]["url"]),
                "mimetype": _safe_eval(lambda: r["mimetype"]),
                "lang": _safe_eval(lambda: r["lang"]),
                "size_bytes": _safe_eval(lambda: r["data"][-1]["size_bytes"]),
            }

        assets = {a: _latest(u) for a, u in version["assets"].items()}
        version["assets"] = assets
        renditions = [_latest_renditions(r) for r in version["renditions"]]
        version["renditions"] = renditions
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
                key=lambda version: version.get("timestamp", ""),
            )
        except ValueError:
            raise ValueError("missing version for timestamp: %s" % timestamp) from None

        if target_version.get("deleted"):
            return target_version

        def _at_time(uris):
            try:
                target = max(
                    itertools.takewhile(lambda asset: asset[0] <= timestamp, uris),
                    key=lambda asset: asset[0],
                )
            except ValueError:
                return ""
            return target[1]

        def _rendition_at_time(r):
            try:
                target_data = max(
                    itertools.takewhile(
                        lambda r_data: r_data["timestamp"] <= timestamp, r["data"]
                    ),
                    key=lambda r_data: r_data["timestamp"],
                )
            except ValueError:
                return {}
            rendition = {
                "filename": r["filename"],
                "mimetype": r["mimetype"],
                "lang": r["lang"],
                "url": target_data["url"],
                "size_bytes": target_data["size_bytes"],
            }
            return rendition

        target_assets = {a: _at_time(u) for a, u in target_version["assets"].items()}
        target_version["assets"] = target_assets
        target_renditions = [
            _rendition_at_time(r) for r in target_version["renditions"]
        ]
        target_version["renditions"] = target_renditions
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

        if version.get("deleted"):
            raise exceptions.DeletedVersion("cannot get data: the document was deleted")

        xml_tree, data_assets = assets_getter(version["data"], timeout=timeout)

        version_assets = version["assets"]
        for asset_key, target_node in data_assets:
            version_href = version_assets.get(asset_key, "")
            target_node.attrib["{http://www.w3.org/1999/xlink}href"] = version_href

        return etree.tostring(xml_tree, encoding="utf-8", pretty_print=False)

    def _latest_or_default(self):
        try:
            return self.version()
        except ValueError:
            return {}

    def _latest_if_not_deleted(self, exception):
        latest_version = self._latest_or_default()

        if latest_version.get("deleted"):
            raise exception
        else:
            return latest_version

    def new_asset_version(self, asset_id, data_url) -> None:
        """Adiciona `data_url` como uma nova versão do ativo `asset_id` vinculado
        a versão mais recente do documento. É importante notar que nenhuma validação
        será executada em `data_url`.
        """
        latest_version = self._latest_if_not_deleted(
            exceptions.DeletedVersion("cannot add version: the document is deleted")
        )

        if latest_version.get("assets", {}).get(asset_id) == data_url:
            raise exceptions.VersionAlreadySet(
                "could not add version: the version is equal to the latest one"
            )

        try:
            self.manifest = DocumentManifest.add_asset_version(
                self._manifest, asset_id, data_url
            )
        except KeyError:
            raise ValueError(
                'cannot add version for "%s": unknown asset_id' % asset_id
            ) from None

    def new_rendition_version(
        self, filename, data_url, mimetype, lang, size_bytes
    ) -> None:
        """Adiciona `data_url` como uma nova versão da manifestação identificada
        por `filename`, `mimetype` e `lang`, vinculada a versão mais recente do
        documento. É importante notar que nenhuma validação será executada em
        `data_url`, `mimetype` ou `size_bytes`.
        """
        latest_version = self._latest_if_not_deleted(
            exceptions.DeletedVersion("cannot add version: the document is deleted")
        )

        selected_rendition = [
            r
            for r in latest_version.get("renditions", [])
            if r["filename"] == filename
            and r["url"] == data_url
            and r["mimetype"] == mimetype
            and r["lang"] == lang
            and r["size_bytes"] == size_bytes
        ]
        if len(selected_rendition):
            raise exceptions.VersionAlreadySet(
                "could not add version: the version is equal to the latest one"
            )

        self.manifest = DocumentManifest.add_rendition_version(
            self._manifest, filename, data_url, mimetype, lang, size_bytes
        )

    def new_deleted_version(self) -> None:
        """Adiciona uma nova versão que indica que o documento foi removido.
        """
        latest_version = self._latest_if_not_deleted(
            exceptions.VersionAlreadySet(
                "could not add deleted version: the document is already deleted"
            )
        )

        self.manifest = DocumentManifest.add_deleted_version(self._manifest)


class BundleManifest:
    """Namespace para funções que manipulam maços.
    """

    @staticmethod
    def new(bundle_id: str, now: Callable[[], str] = utcnow) -> dict:
        timestamp = now()
        return {
            "id": str(bundle_id),
            "created": timestamp,
            "updated": timestamp,
            "items": [],
            "metadata": {},
        }

    @staticmethod
    def set_metadata(
        bundle: dict,
        name: str,
        value: Union[dict, str],
        now: Callable[[], str] = utcnow,
    ) -> dict:
        _bundle = deepcopy(bundle)
        _now = now()
        metadata = _bundle["metadata"].setdefault(name, [])
        metadata.append((_now, value))
        _bundle["updated"] = _now
        return _bundle

    @staticmethod
    def get_metadata(bundle: dict, name: str, default="") -> Any:
        try:
            return bundle["metadata"].get(name, [])[-1][1]
        except IndexError:
            return default

    @staticmethod
    def get_metadata_all(bundle: dict, name: str) -> Any:
        return bundle["metadata"].get(name, [])

    @staticmethod
    def get_item(bundle: dict, id: str) -> dict:
        """Recupera um item a partir de um identificador"""

        for item in bundle["items"]:
            if id == item["id"]:
                return item

    @staticmethod
    def add_item(bundle: dict, item: dict, now: Callable[[], str] = utcnow) -> dict:

        try:
            _item = dict(item)
            _id = _item["id"]
        except ValueError:
            raise ValueError(
                "cannot add this item " '"%s": item must be dict' % item
            ) from None
        except KeyError:
            raise KeyError(
                "cannot add this item " '"%s": item must contain id key' % item
            ) from None

        if BundleManifest.get_item(bundle, _id) is not None:
            raise exceptions.AlreadyExists(
                'cannot add item "%s" in bundle: ' "the item id already exists" % _id
            )

        _bundle = deepcopy(bundle)
        _bundle["items"].append(_item)
        _bundle["updated"] = now()
        return _bundle

    @staticmethod
    def insert_item(
        bundle: dict, index: int, item: dict, now: Callable[[], str] = utcnow
    ) -> dict:

        try:
            _item = dict(item)
            _id = _item["id"]
        except ValueError:
            raise ValueError(
                "cannot insert this item " '"%s": item must be dict' % item
            ) from None
        except KeyError:
            raise KeyError(
                "cannot insert this item " '"%s": item must contain id key' % item
            ) from None

        if BundleManifest.get_item(bundle, _id) is not None:
            raise exceptions.AlreadyExists(
                'cannot insert item id "%s" in bundle: '
                "the item id already exists" % _id
            )
        _bundle = deepcopy(bundle)
        _bundle["items"].insert(index, _item)
        _bundle["updated"] = now()
        return _bundle

    @staticmethod
    def remove_item(
        bundle: dict, item_id: str, now: Callable[[], str] = utcnow
    ) -> dict:

        item = BundleManifest.get_item(bundle, item_id)

        if item is None:
            raise exceptions.DoesNotExist(
                "cannot remove item from bundle: "
                'the item id "%s" does not exist' % item_id
            )
        _bundle = deepcopy(bundle)
        _bundle["items"].remove(item)
        _bundle["updated"] = now()
        return _bundle

    @staticmethod
    def set_component(
        components_bundle: dict, name: str, value: Any, now: Callable[[], str] = utcnow
    ) -> None:
        _components_bundle = deepcopy(components_bundle)
        _components_bundle[name] = value
        _components_bundle["updated"] = now()
        return _components_bundle

    @staticmethod
    def get_component(components_bundle: dict, name: str, default: str = "") -> Any:
        return components_bundle.get(name, default)

    @staticmethod
    def remove_component(components_bundle: dict, name: str) -> dict:
        _components_bundle = deepcopy(components_bundle)
        try:
            del _components_bundle[name]
        except KeyError:
            raise exceptions.DoesNotExist(
                f'cannot remove component "{name}" from bundle: '
                "the component does not exist"
            ) from None
        else:
            return _components_bundle


class DocumentsBundle:
    """
    DocumentsBundle representa um conjunto de documentos agnóstico ao modelo de
    publicação. Exemplos de publicação que são DocumentsBundle: Fascículos fechados
    e abertos, Ahead of Print, Documentos Provisórios, Erratas e Retratações.
    """

    def __init__(self, id: str = None, manifest: dict = None):
        assert any([id, manifest])
        self.manifest = manifest or BundleManifest.new(id)

    def id(self):
        return self.manifest.get("id", "")

    def data(self):
        _manifest = self.manifest
        _manifest["metadata"] = {
            attr: value[-1][-1] for attr, value in _manifest["metadata"].items()
        }
        return _manifest

    @property
    def manifest(self):
        return deepcopy(self._manifest)

    @manifest.setter
    def manifest(self, value: dict):
        self._manifest = value

    @property
    def publication_year(self):
        return BundleManifest.get_metadata(self.manifest, "publication_year")

    @publication_year.setter
    def publication_year(self, value: Union[str, int]):
        _value = str(value)
        if not re.match(r"^\d{4}$", _value):
            raise ValueError(
                "cannot set publication_year with value "
                f'"{_value}": the value is not valid'
            )
        self.manifest = BundleManifest.set_metadata(
            self._manifest, "publication_year", _value
        )

    @property
    def volume(self):
        return BundleManifest.get_metadata(self.manifest, "volume")

    @volume.setter
    def volume(self, value: Union[str, int]):
        _value = str(value)
        self.manifest = BundleManifest.set_metadata(self._manifest, "volume", _value)

    @property
    def number(self):
        return BundleManifest.get_metadata(self.manifest, "number")

    @number.setter
    def number(self, value: Union[str, int]):
        _value = str(value)
        self.manifest = BundleManifest.set_metadata(self._manifest, "number", _value)

    @property
    def supplement(self):
        return BundleManifest.get_metadata(self.manifest, "supplement")

    @supplement.setter
    def supplement(self, value: Union[str, int]):
        _value = str(value)
        self.manifest = BundleManifest.set_metadata(
            self._manifest, "supplement", _value
        )

    @property
    def titles(self):
        return BundleManifest.get_metadata(self.manifest, "titles", [])

    @titles.setter
    def titles(self, value: dict):
        try:
            _value = list([dict(title) for title in value])
        except (TypeError, ValueError):
            raise TypeError(
                "cannot set titles with value "
                '"%s": value must be list of dict' % value
            ) from None
        self.manifest = BundleManifest.set_metadata(self._manifest, "titles", _value)

    def add_document(self, document: str):
        self.manifest = BundleManifest.add_item(self._manifest, document)

    def insert_document(self, index: int, document: str):
        self.manifest = BundleManifest.insert_item(self._manifest, index, document)

    def remove_document(self, document: str):
        self.manifest = BundleManifest.remove_item(self._manifest, document)

    @property
    def documents(self):
        return self.manifest["items"]


class Journal:
    """
    Journal representa um periodico cientifico que contem um conjunto de documentos
    DocumentsBundle.
    """

    def __init__(self, id: str = None, manifest: dict = None):
        assert any([id, manifest])
        self.manifest = manifest or BundleManifest.new(id)

    def id(self):
        return self.manifest.get("id", "")

    def created(self):
        return self.manifest.get("created", "")

    def updated(self):
        return self.manifest.get("updated", "")

    @property
    def manifest(self):
        return deepcopy(self._manifest)

    @manifest.setter
    def manifest(self, value: dict):
        self._manifest = value

    def data(self):
        """Retorna o manifesto completo de um Journal com os
        metadados em sua última versão"""
        _manifest = self.manifest

        for key, value in _manifest["metadata"].items():
            _manifest["metadata"][key] = value[-1][-1]

        return _manifest

    @property
    def mission(self):
        return BundleManifest.get_metadata(self.manifest, "mission", [])

    @mission.setter
    def mission(self, value: List[dict]):
        try:
            value = list([dict(mission) for mission in value])
        except (TypeError, ValueError):
            raise TypeError(
                "cannot set mission with value "
                '"%s": value must be list of dict' % value
            ) from None
        self.manifest = BundleManifest.set_metadata(self._manifest, "mission", value)

    @property
    def title(self):
        return BundleManifest.get_metadata(self.manifest, "title")

    @title.setter
    def title(self, value: str):
        _value = str(value)
        self.manifest = BundleManifest.set_metadata(self._manifest, "title", _value)

    @property
    def title_iso(self):
        return BundleManifest.get_metadata(self.manifest, "title_iso")

    @title_iso.setter
    def title_iso(self, value: str):
        _value = str(value)
        self.manifest = BundleManifest.set_metadata(self._manifest, "title_iso", _value)

    @property
    def short_title(self):
        return BundleManifest.get_metadata(self.manifest, "short_title")

    @short_title.setter
    def short_title(self, value: str):
        _value = str(value)
        self.manifest = BundleManifest.set_metadata(
            self._manifest, "short_title", _value
        )

    @property
    def acronym(self):
        return BundleManifest.get_metadata(self.manifest, "acronym")

    @acronym.setter
    def acronym(self, value: str):
        _value = str(value)
        self.manifest = BundleManifest.set_metadata(self._manifest, "acronym", _value)

    @property
    def scielo_issn(self):
        return BundleManifest.get_metadata(self.manifest, "scielo_issn")

    @scielo_issn.setter
    def scielo_issn(self, value: str):
        _value = str(value)
        self.manifest = BundleManifest.set_metadata(
            self._manifest, "scielo_issn", _value
        )

    @property
    def print_issn(self):
        return BundleManifest.get_metadata(self.manifest, "print_issn")

    @print_issn.setter
    def print_issn(self, value: str):
        _value = str(value)
        self.manifest = BundleManifest.set_metadata(
            self._manifest, "print_issn", _value
        )

    @property
    def electronic_issn(self):
        return BundleManifest.get_metadata(self.manifest, "electronic_issn")

    @electronic_issn.setter
    def electronic_issn(self, value: str):
        _value = str(value)
        self.manifest = BundleManifest.set_metadata(
            self._manifest, "electronic_issn", _value
        )

    @property
    def status(self):
        return BundleManifest.get_metadata(self.manifest, "status")

    @status.setter
    def status(self, value: dict):
        try:
            value = dict(value)
        except (TypeError, ValueError):
            raise TypeError(
                "cannot set status with value " '"%s": value must be dict' % repr(value)
            ) from None
        self.manifest = BundleManifest.set_metadata(self._manifest, "status", value)

    @property
    def subject_areas(self):
        return BundleManifest.get_metadata(self.manifest, "subject_areas")

    @subject_areas.setter
    def subject_areas(self, value: tuple):
        try:
            value = tuple(value)
        except (TypeError, ValueError):
            raise TypeError(
                "cannot set subject_areas with value "
                '"%s": value must be tuple' % repr(value)
            ) from None
        invalid = [item for item in value if item not in SUBJECT_AREAS]
        if invalid:
            raise ValueError(
                "cannot set subject_areas with value %s: " % repr(value)
                + "%s are not valid" % repr(invalid)
            )
        self.manifest = BundleManifest.set_metadata(
            self._manifest, "subject_areas", value
        )

    @property
    def sponsors(self) -> Tuple[dict]:
        return BundleManifest.get_metadata(self.manifest, "sponsors")

    @sponsors.setter
    def sponsors(self, value: Tuple[dict]) -> None:
        try:
            value = tuple([dict(sponsor) for sponsor in value])
        except TypeError:
            raise TypeError("cannot set sponsors this type %s" % repr(value)) from None

        self.manifest = BundleManifest.set_metadata(self._manifest, "sponsors", value)

    @property
    def metrics(self):
        return BundleManifest.get_metadata(self.manifest, "metrics", {})

    @metrics.setter
    def metrics(self, value: dict):
        try:
            value = dict(value)
        except (TypeError, ValueError):
            raise TypeError(
                "cannot set metrics with value " '"%s": value must be dict' % value
            ) from None
        self.manifest = BundleManifest.set_metadata(self._manifest, "metrics", value)

    @property
    def subject_categories(self):
        return BundleManifest.get_metadata(self.manifest, "subject_categories")

    @subject_categories.setter
    def subject_categories(self, value: Union[list, tuple]):
        try:
            value = list(value)
        except TypeError:
            raise TypeError(
                "cannot set subject_categories with value "
                '"%s": value must be list like object' % value
            ) from None

        self.manifest = BundleManifest.set_metadata(
            self._manifest, "subject_categories", list(value)
        )

    @property
    def institution_responsible_for(self):
        return BundleManifest.get_metadata(
            self.manifest, "institution_responsible_for", ()
        )

    @institution_responsible_for.setter
    def institution_responsible_for(self, value: tuple):
        try:
            value = tuple(value)
        except (TypeError, ValueError):
            raise TypeError(
                "cannot set institution_responsible_for with value "
                '"%s": value must be tuple' % repr(value)
            ) from None

        self.manifest = BundleManifest.set_metadata(
            self.manifest, "institution_responsible_for", value
        )

    @property
    def online_submission_url(self):
        return BundleManifest.get_metadata(self.manifest, "online_submission_url")

    @online_submission_url.setter
    def online_submission_url(self, value: str):
        _value = str(value)
        self.manifest = BundleManifest.set_metadata(
            self._manifest, "online_submission_url", _value
        )

    @property
    def next_journal(self):
        return BundleManifest.get_metadata(self.manifest, "next_journal", {})

    @next_journal.setter
    def next_journal(self, value: dict):
        try:
            value = dict(value)
        except (TypeError, ValueError):
            raise TypeError(
                "cannot set next_journal with value "
                '"%s": value must be dict' % repr(value)
            ) from None
        self.manifest = BundleManifest.set_metadata(
            self._manifest, "next_journal", value
        )

    @property
    def previous_journal(self):
        return BundleManifest.get_metadata(self.manifest, "previous_journal", {})

    @previous_journal.setter
    def previous_journal(self, value: dict):
        try:
            value = dict(value)
        except (TypeError, ValueError):
            raise TypeError(
                "cannot set previous_journal with value "
                '"%s": value must be dict' % repr(value)
            ) from None
        self.manifest = BundleManifest.set_metadata(
            self._manifest, "previous_journal", value
        )

    @property
    def status_history(self):
        return BundleManifest.get_metadata_all(self.manifest, "status")

    @property
    def contact(self) -> dict:
        return BundleManifest.get_metadata(self.manifest, "contact", {})

    @contact.setter
    def contact(self, value: dict) -> None:
        try:
            value = dict(value)
        except (TypeError, ValueError) as ex:
            raise type(ex)(
                "cannot set contact with value "
                "%s"
                ": value must be dict" % repr(value)
            ) from None

        self.manifest = BundleManifest.set_metadata(self._manifest, "contact", value)

    def add_issue(self, issue: str) -> None:
        self.manifest = BundleManifest.add_item(self._manifest, issue)

    def insert_issue(self, index: int, issue: str) -> None:
        self.manifest = BundleManifest.insert_item(self._manifest, index, issue)

    def remove_issue(self, issue: str) -> None:
        self.manifest = BundleManifest.remove_item(self._manifest, issue)

    @property
    def issues(self) -> List[str]:
        return self.manifest["items"]

    @property
    def provisional(self):
        return BundleManifest.get_component(self.manifest, "provisional")

    @provisional.setter
    def provisional(self, provisional: str) -> None:
        self.manifest = BundleManifest.set_component(
            self._manifest, "provisional", str(provisional)
        )

    @property
    def ahead_of_print_bundle(self) -> str:
        return BundleManifest.get_component(self.manifest, "aop", "")

    @ahead_of_print_bundle.setter
    def ahead_of_print_bundle(self, value: str) -> None:
        self.manifest = BundleManifest.set_component(self._manifest, "aop", str(value))

    def remove_ahead_of_print_bundle(self) -> None:
        self.manifest = BundleManifest.remove_component(self._manifest, "aop")
