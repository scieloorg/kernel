# 6. Novo PID do SciELO

Data: 2019-04-12
Atualização: 2019-11-29

## Status

Proposto

## Contexto

O PID é uma string de texto que identifica de maneira única um documento parte
da Rede SciELO. Desde início optou-se pela utilização de chaves naturais, p. ex.,
`S0001-37652000000100002`, que, devido aos avanços recentes da plataforma em
relação aos novos modelos de publicação, não é mais adequado. Os metadados
do documento que formam o PID podem ser alterados ao longo do seu ciclo de vida,
sendo necessário o desenvolvimento de um novo PID.


## Decisão

Utilizaremos uma chave artificial, baseada na implementação do
[RFC 4122](http://tools.ietf.org/html/rfc4122.html), de forma que seja possível
a identificação única dos documentos da Rede sem a necessidade de uma autoridade
central.

O novo PID deverá ser armazenado em um campo exclusivo, diferente do que
é destinado para o PID anterior, que continuará sendo suportado normalmente por
todas as aplicações. O PID no formato anterior não será mais produzido para os novos
documentos.

Durante a migração dos dados da coleção para uma instância do Kernel, todos
os documentos deverão receber o novo PID, que no XML do documento será
representado no elemento
`/article/front/article-meta/article-id[@pub-id-type = "publisher-id" and @specific-use="scielo-v3"]`.

A representação do PID padrão `S0001-37652000000100002` passa a ser:
`/article/front/article-meta/article-id[@pub-id-type = "publisher-id" and @specific-use="scielo-v2"]`.

A representação do PID anterior ao padrão `S0001-37652000000100002` passa a ser:
`/article/front/article-meta/article-id[@pub-id-type = "publisher-id" and @specific-use="scielo-v1"]`.

De maneira resumida, o novo PID do SciELO é o resultado da função
`uuid.uuid4()`, como implementada na linguagem Python, representado em base 48.
A decisão de utilizar base 48 foi motivada pelo desejo de obtermos um identificador
cuja quantidade de dígitos é próxima a do formato anterior, que possui 23. A 
base 48 garante a representação de um valor de 128bits, como é o caso do 
`uuid.uuid4()`, em até 23 dígitos. A escolha dos caracteres da base foi realizada
de forma que os identificadores não formem palavras na língua portuguesa
e não possuam caracteres de difícil leitura, p. ex., `l10O`.

O código abaixo apresenta a implementação de referência que deve ser utilizada
nas aplicações:

```python
from math import log2, ceil
from uuid import UUID, uuid4


digit_chars = "bcdfghjkmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ3456789"
chars_map = {dig: idx for idx, dig in enumerate(digit_chars)}


def uuid2str(value):
    result = []
    unevaluated = value.int
    for unused in range(ceil(128 / log2(len(digit_chars)))):
        unevaluated, remainder = divmod(unevaluated, len(digit_chars))
        result.append(digit_chars[remainder])
    return "".join(result)


def str2uuid(value):
    acc = 0
    mul = 1
    for digit in value:
        acc += chars_map[digit] * mul
        mul *= len(digit_chars)
    return UUID(int=acc)


def generate_scielo_pid():
    return uuid2str(uuid4())
```

O PID retornado pela função `generate_scielo_pid()` poderá ser convertido
novamente em `UUID`, caso seja desejado, por meio do uso da função
`str2uuid(value)`.


## Consequências


Prós:
* Os metadados dos documentos podem ser alterados sem que o identificador pareça
  obsoleto (desacoplamento entre o identificador e metadados do objeto identificado
  por conta o uso de chave artificial). Essa característica é fundamental para
  a publicação de *preprints*, *artigos provisórios* e até *ahead-of-print*;
* Elimina a rigidez estrutural do identificador, que se apoia na relação entre
  *periódico*, *ano de publicação*, *fascículo* e *posição em relação ao fascículo*;
* Garante a identificação única dos documentos de toda a Rede;
* Elimina a dependência que pode ocorrer por parte de usuários e aplicações
  em relação ao formato do identificador para a extração de metadados, p. ex.,
  a data da publicação do documento ou a ordenação na tabela de conteúdos;
* O uso do UUID ([RFC 4122](http://tools.ietf.org/html/rfc4122.html)) nos
  permite a geração descomplicada do identificador e também seu armazenamento em
  bancos de dados que suportam o tipo nativamente, como é o caso do
  [PostgreSQL](https://www.postgresql.org/docs/9.1/datatype-uuid.html).

Contras:
* Todas as aplicações terão que suportar mais um identificador;
* A chave artificial não é inteligível como a natural, o que pode reduzir seu
  reuso em outros contextos, p. ex., no seu identificador DOI ou em URLs.
