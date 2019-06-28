class RetryableError(Exception):
    """Erro recuperável sem que seja necessário modificar o estado dos dados
    na parte cliente, e.g., timeouts, erros advindos de particionamento de rede 
    etc.
    """


class NonRetryableError(Exception):
    """Erro do qual não pode ser recuperado sem modificar o estado dos dados 
    na parte cliente, e.g., recurso solicitado não exite, URI inválida etc.
    """


class AlreadyExists(NonRetryableError):
    """Erro que representa a tentativa de registro de uma entidade cujo
    identificador já está em uso.
    """


class DoesNotExist(NonRetryableError):
    """Erro que representa a tentativa de recuperar uma entidade à partir
    de um identificador que não está associado a nenhuma delas.
    """


class VersionAlreadySet(RetryableError):
    """Erro que representa a tentativa de definir uma nova versão idêntica a 
    anterior. 
    """


class DeletedVersion(NonRetryableError):
    """Erro que representa a tentativa de recuperar o XML de um documento
    em uma versão que foi excluída.
    """
