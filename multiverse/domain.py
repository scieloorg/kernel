from . import manifest as _manifest


class Article:
    def __init__(self, doc_id=None, manifest=None):
        assert any([doc_id, manifest])
        self.manifest = manifest or _manifest.new(doc_id)

    def new_version(self, data) -> None:
        """Adiciona `data` como uma nova versão do artigo.

        :param data: é o file-object de um artigo em XML.
        """

    def new_asset_version(self, asset_id, data) -> None:
        """Adiciona `data` como uma nova versão do ativo `asset_id` vinculado 
        a versão mais recente do artigo.

        :param asset_id: string identificando o ativo conforme aparece no XML.
        :param data: file-object de um ativo digital.
        """
