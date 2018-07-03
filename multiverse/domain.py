from . import manifest as _manifest


class Article:
    def __init__(self, doc_id=None, manifest=None):
        assert any([doc_id, manifest])
        self.manifest = manifest or _manifest.new(doc_id)

    def doc_id(self):
        return self.manifest.get("id", "")

    def new_version(self, data_uri) -> None:
        """Adiciona `data_uri` como uma nova versão do artigo.

        TODO:
        Obtém o conteúdo de `data_uri` com a finalidade de listar seus ativos
        digitais relacionados.

        :param data_uri: é a URI para a nova versão do artigo.
        """
        self.manifest = _manifest.add_version(self.manifest, data_uri, [])

    def new_asset_version(self, asset_id, data) -> None:
        """Adiciona `data` como uma nova versão do ativo `asset_id` vinculado 
        a versão mais recente do artigo.

        :param asset_id: string identificando o ativo conforme aparece no XML.
        :param data: file-object de um ativo digital.
        """
