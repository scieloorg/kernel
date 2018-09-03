class RetryableError(Exception):
    """Erro recuperável sem que seja necessário modificar o estado dos dados
    na parte cliente, e.g., timeouts, erros advindos de particionamento de rede 
    etc.
    """


class NonRetryableError(Exception):
    """Erro do qual não pode ser recuperado sem modificar o estado dos dados 
    na parte cliente, e.g., recurso solicitado não exite, URI inválida etc.
    """


class DocumentAlreadyExists(NonRetryableError):
    """Erro que representa a tentativa de registro de um documento cujo
    identificador está associado a outro documento no sistema.
    """


class DocumentDoesNotExist(NonRetryableError):
    """Erro que representa a tentativa de recuperar um documento à partir
    de um identificador que não está associado a nenhum documento.
    """


class VersionAlreadySet(RetryableError):
    """Erro que representa a tentativa de definir uma nova versão idêntica a 
    anterior. 
    """
