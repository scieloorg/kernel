Data: 2019-08-09

## Status

Proposto

## Contexto
A estratégia adotada pelo *kernel* para criar e manter o relacionamento 
entre entidades consiste em armazenar os identificadores das entidades em 
uma estrutura de lista no formato 1-N onde o conhecimento sobre o relacionamento 
é obtido de forma unidirecional.

É possível imaginar os relacionamentos de forma hierárquica onde um periódico
possui vários fascículos. Sendo assim a *entidade periódico* é responsável
por armazenar a lista de identificadores dos seus fascículos.

Atualmente a estrutura adotada consiste no armazenamento de uma lista de 
identificadores onde a posição do identificador pode indicar a ordem de 
trabalho ou renderização em uma interface. O código abaixo ilustra a 
estrutura de container utilizada.

```json
{
    "id": "1415-4757",
    "created": "2019-08-01T20:24:01.863522Z",
    "updated": "2019-08-01T20:24:01.863522Z",
    "items": [
        "1415-4757-1998-v21-n1",
        "1415-4757-1998-v21-n2"
    ]

}
```

Por se tratar de uma estrutura simples e que provê apenas o contexto de 
posição do identificador em uma lista, o consumidor pode necessitar 
consultar a entidade indicada a fim de obter mais informações que 
possibilitem o trabalho de renderização (por ex: em uma tela).

## Decisão

Com base no ponto citado no tópico anterior foi proposta a modificação 
dos dados contidos pela lista de *items*. Devemos manter a estrutura de 
lista e substituir a *string* do identificador por uma estrutura de `chave e valor`. 
Esta modificação deve facilitar o armazenamento de informações relevantes 
para o consumidor da lista de relacionamentos, podemos por exemplo armazenar 
a ordem com que um item deve ser renderizado em uma interface `X` ou 
em uma interface `Y`, podemos armazenar regras de agrupamento, regras de namespace e etc.

O código abaixo ilustra a estrutura de container proposta.

```json
{
    "id": "1415-4757",
    "created": "2019-08-01T20:24:01.863522Z",
    "updated": "2019-08-01T20:24:01.863522Z",
    "items": [
        {
            "id": "1415-4757-1998-v21-n1",
            "ns": ["2019", "v21", "n1"]
        },
        {
            "id": "1415-4757-1998-v21-n2",
            "ns": ["2019", "v21", "n2", "..."]
        }
    ]
}
```

Deve ser ressaltado que a chave `id` é obrigatória e será usada para garantir 
que itens não sejam armazenados em duplicidade. A ordem de inserção não 
necessariamente deve ser relevante para a exibição.

# Consequências

Prós:
* Permite mais robustez ao armazenar informações que são relevantes no contexto do relacionamento.
* Permite representar agrupamentos de fascículos por ano de publicação, volume, número e outros.
* Permite derivar a grade de fascículos do periódico.

Contras:
* Obriga o uso de um formato específico para armazenar as informações.