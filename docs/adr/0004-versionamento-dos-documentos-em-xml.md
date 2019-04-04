# 4. Versionamento dos documentos em XML

Data: 2019-03-07

## Status

Aceito

## Contexto

O SciELO utiliza a especificação SciELO PS para representar os documentos
científicos que publica. A especificação se baseia na norma NISO JATS
Publishing DTD mais o Estilo SciELO para a representação dos metadados em XML.

Por vezes é necessário que os documentos sejam modificados, como por exemplo:

* Correção de erros nos metadados;
* Migração de dados;
* Documentos *ahead-of-print* que passaram a integrar números regulares;
* etc


O documento uma vez publicado poderá ser citado (esse é o objetivo) e, portanto,
deverá permanecer disponível naquele estado.

## Decisão

Garantiremos que todas as versões do documento sejam imutáveis no sentido em
que as modificações produzirão novas versões dos documentos e que também sejam
passíveis de serem recuperadas a partir da data da sua citação.

## Consequências

* Teremos que garantir que os arquivos XML, uma vez que publicados, não serão
sobrescritos no *object store* em hipótese alguma;
* Cada modificação efetivada resultará na criação de um novo e completo arquivo
XML ou em novos ativos digitais;
