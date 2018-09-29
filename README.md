# SciELO Document Store


Trata-se de uma implementação experimental de um pacote Python que busca 
tratar da persistência de documentos XML em multiplas versões.

A abstração básica se apoia no conceito do *manifesto do documento*:

```javascript
{
  "id": "S0034-89102014000200347",
  "versions": [
    {
      "assets": {
        "0034-8910-rsp-48-2-0347-gf01": [
          [
            "2018-08-05T23:03:44.971230Z",
            "http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf01.jpg"
          ]
        ],
        "0034-8910-rsp-48-2-0347-gf01-en": [
          [
            "2018-08-05T23:08:41.590174Z",
            "http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf01-en.jpg"
          ]
        ],
        "0034-8910-rsp-48-2-0347-gf02": [
          [
            "2018-08-05T23:04:43.323527Z",
            "http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf02.jpg"
          ]
        ],
        "0034-8910-rsp-48-2-0347-gf02-en": [
          [
            "2018-08-05T23:08:50.331687Z",
            "http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf02-en.jpg"
          ]
        ],
        "0034-8910-rsp-48-2-0347-gf03": [
          [
            "2018-08-05T23:05:14.882129Z",
            "http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf03.jpg"
          ]
        ],
        "0034-8910-rsp-48-2-0347-gf03-en": [
          [
            "2018-08-05T23:08:59.691924Z",
            "http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf03-en.jpg"
          ]
        ],
        "0034-8910-rsp-48-2-0347-gf04": [
          [
            "2018-08-05T23:05:42.016837Z",
            "http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf04.jpg"
          ]
        ],
        "0034-8910-rsp-48-2-0347-gf04-en": [
          [
            "2018-08-05T23:09:09.569312Z",
            "http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf04-en.jpg"
          ]
        ]
      },
      "data": "https://raw.githubusercontent.com/scieloorg/packtools/master/tests/samples/0034-8910-rsp-48-2-0347.xml",
      "timestamp": "2018-08-05T23:02:29.392990Z"
    }
  ]
}
```

O *manifesto do documento* é um objeto JSON que representa as relações entre
a identidade de um documento e seus estados. A identidade do documento é 
representada por meio da chave ``id``, que deve ser única. Os estados do
documento são representados pela chave ``versions``, que está associada a uma
coleção de objetos que representam versões. A coleção ``versions`` é ordenada
da versão mais antiga para a mais recente. Cada versão contém uma URI para o 
artigo codificado em XML segundo a especificação SciELO PS na chave ``data``,
o *timestamp* UTC datando sua criação e a coleção ``assets``, composta pelo
mapeamento dos ativos digitais referenciados pelo documento em XML e pares
*timestamp* e URI.


## Requisitos

* Python 3.6+
* MongoDB


## Implantação local

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

