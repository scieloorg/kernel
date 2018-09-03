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
            "2018-08-05 23:03:44.971230",
            "http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf01.jpg"
          ]
        ],
        "0034-8910-rsp-48-2-0347-gf01-en": [
          [
            "2018-08-05 23:08:41.590174",
            "http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf01-en.jpg"
          ]
        ],
        "0034-8910-rsp-48-2-0347-gf02": [
          [
            "2018-08-05 23:04:43.323527",
            "http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf02.jpg"
          ]
        ],
        "0034-8910-rsp-48-2-0347-gf02-en": [
          [
            "2018-08-05 23:08:50.331687",
            "http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf02-en.jpg"
          ]
        ],
        "0034-8910-rsp-48-2-0347-gf03": [
          [
            "2018-08-05 23:05:14.882129",
            "http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf03.jpg"
          ]
        ],
        "0034-8910-rsp-48-2-0347-gf03-en": [
          [
            "2018-08-05 23:08:59.691924",
            "http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf03-en.jpg"
          ]
        ],
        "0034-8910-rsp-48-2-0347-gf04": [
          [
            "2018-08-05 23:05:42.016837",
            "http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf04.jpg"
          ]
        ],
        "0034-8910-rsp-48-2-0347-gf04-en": [
          [
            "2018-08-05 23:09:09.569312",
            "http://www.scielo.br/img/revistas/rsp/v48n2/0034-8910-rsp-48-2-0347-gf04-en.jpg"
          ]
        ]
      },
      "data": "https://raw.githubusercontent.com/scieloorg/packtools/master/tests/samples/0034-8910-rsp-48-2-0347.xml",
      "timestamp": "2018-08-05 23:02:29.392990"
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

