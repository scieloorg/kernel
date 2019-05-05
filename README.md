# Kernel

Kernel é o componente central da nova arquitetura de sistemas de informação da
Metodologia SciELO, ainda em fase de desenvolvimento. É responsável pela gestão,
preservação e desempenha o papel de fonte autoritativa dos dados de uma coleção
de periódicos científicos.

```
                            +------------+  +--------------------+
                            | Public     |  | OAI-PMH            |
                            | website    |  | data provider, etc |
                            +------------+  +--------------------+
                                    ^              ^
                                    |              |
+-------------------+       +------------------------------+      +--------------+
|  Data ingestion   |       |                              |      |              |
|  workflow         |------>|            Kernel            |----->| Integrations |
|                   |       |                              |      |              |
+-------------------+       +------------------------------+      +--------------+
```

Principais características:

* Opera como um serviço Web, por meio de interface RESTful;
* Suporta a representação de fascículos ou qualquer outro grupo de documentos
por meio de uma abstração chamada *Documents bundle*;
* Preservação das versões dos metadados de Periódicos e *Documents bundle*;
* Preservação dos documentos XML e seus ativos digitais em múltiplas versões;
* Garantia da integridade referencial entre o documento em XML e seus ativos
digitais;
* Replicação por meio de log de mudanças e notificação em barramento de eventos.

Para mais informação sobre a nova arquitetura de sistemas de informação da Metodologia SciELO consulte https://docs.google.com/document/d/14YBl7--4ouaWBQhxzUYWRuhmegwnSYrDgupsED6rhvM/edit?usp=sharing

## Requisitos

* Python 3.7+
* MongoDB


## Implantação local

Configurando a aplicação:


diretiva no arquivo .ini | variável de ambiente   | valor padrão
-------------------------|------------------------|--------------------
kernel.app.mongodb.dsn   | KERNEL_APP_MONGODB_DSN | mongodb://db:27017


Configurações avançadas:


variável de ambiente      | valor padrão
--------------------------|-------------
KERNEL_LIB_MAX_RETRIES    | 4
KERNEL_LIB_BACKOFF_FACTOR | 1.2


Executando a aplicação:

```docker-compose up -d```

Testando o registro de um documento de exemplo:

```
curl -X PUT -H 'Accept: application/json' -H 'Content-Type: application/json' http://0.0.0.0:6543/documents/0034-8910-rsp-48-2-0347 -d '{"data": "https://raw.githubusercontent.com/scieloorg/packtools/master/tests/samples/0034-8910-rsp-48-2-0347.xml", "assets": [{"asset_id":"0034-8910-rsp-48-2-0347-gf01", "asset_url":"http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf01.jpg"},{"asset_id":"0034-8910-rsp-48-2-0347-gf01-en", "asset_url":"http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf01-en.jpg"},{"asset_id":"0034-8910-rsp-48-2-0347-gf02", "asset_url":"http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf02.jpg"},{"asset_id":"0034-8910-rsp-48-2-0347-gf02-en","asset_url":"http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf02-en.jpg"},{"asset_id":"0034-8910-rsp-48-2-0347-gf03", "asset_url":"http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf03.jpg"},{"asset_id":"0034-8910-rsp-48-2-0347-gf03-en","asset_url":"http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf03-en.jpg"},{"asset_id":"0034-8910-rsp-48-2-0347-gf04", "asset_url":"http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf04.jpg"},{"asset_id":"0034-8910-rsp-48-2-0347-gf04-en","asset_url":"http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf04-en.jpg"}]}'
```

e em seguida:

```
curl -X GET -H 'Accept: text/xml' http://0.0.0.0:6543/documents/0034-8910-rsp-48-2-0347
```

## Licença de uso

Copyright 2018 SciELO <scielo-dev@googlegroups.com>. Licensed under the terms
of the BSD license. Please see LICENSE in the source code for more
information.

https://github.com/scieloorg/document-store/blob/master/LICENSE
