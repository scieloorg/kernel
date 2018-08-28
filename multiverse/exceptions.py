class RetryableError(Exception):
    """Erro recuperável sem que seja necessário modificar o estado dos dados
    na parte cliente, e.g., timeouts, erros advindos de particionamento de rede 
    etc.
    """


class NonRetryableError(Exception):
    """Erro do qual não pode ser recuperado sem modificar o estado dos dados 
    na parte cliente, e.g., recurso solicitado não exite, URI inválida etc.
    """


class ArticleAlreadyExists(NonRetryableError):
    """Erro que representa a tentativa de registro de um artigo cujo
    identificador está associado a outro artigo no sistema.
    """


class ArticleDoesNotExist(NonRetryableError):
    """Erro que representa a tentativa de recuperar um artigo à partir
    de um identificador que não está associado a nenhum artigo.
    """


class VersionAlreadySet(RetryableError):
    """Erro que representa a tentativa de definir uma nova versão idêntica a 
    anterior. 
    """
