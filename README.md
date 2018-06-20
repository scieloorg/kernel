# Multiverse


*Multiverse* é uma implementação experimental de um pacote Python que busca 
tratar da persistência de documentos XML em multiplas versões.

A abstração básica se apoia no conceito do *manifesto do documento*:

```javascript
{
  "id": "0034-8910-rsp-48-2-0275",
  "versions": [
    {"data": "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275.xml",
     "assets": {
         "0034-8910-rsp-48-2-0275-gf01.gif": [
           "/rawfiles/8e644999a8fa4/0034-8910-rsp-48-2-0275-gf01.gif",
           "/rawfiles/bf139b9aa3066/0034-8910-rsp-48-2-0275-gf01.gif"]}
    },
    {"data": "/rawfiles/2d3ad9c6bc656/0034-8910-rsp-48-2-0275.xml",
     "assets": {
         "0034-8910-rsp-48-2-0275-gf01.gif": [
           "/rawfiles/bf139b9aa3066/0034-8910-rsp-48-2-0275-gf01.gif"]}
    },
  ]
}
```


* *versions* e *assets* são listas ordenadas da versão mais antiga para a mais 
  recente;
* O endpoint *rawfiles* representa qualquer object-store de maneira opaca.
  Poderia ser uma URL para um endpoint da própria aplicação ou para a Amazon S3, 
  por exemplo;
* O protótipo do endpoint rawfiles que aparece aqui tem a preocupação de 
  separar o identificador único do arquivo, baseado nos primeiros dígitos da 
  sua soma SHA1, do seu "nome social" legível por pessoas;
* Reduz a solução do problema a um object-store e um manifesto que representa 
  as relações entre a identidade da entidade e seus diferentes estados.

