# 5. API de mudanças e replicação

Data: 2019-03-11

## Status

Aceito

## Contexto

O Kernel é o componente central da nova arquitetura de sistemas de
informação da Metodologia SciELO. Ele é responsável pela gestão, preservação e
desempenha o papel de fonte autoritativa dos dados de uma coleção de periódicos
científicos. Quando registros forem criados, modificados ou removidos, outros
componentes da arquitetura deverão reagir de acordo, e.g., o site público deverá
publicar documentos novos ou atualizados, e omitir os removidos.


## Decisão

Forneceremos um mecanismo de replicação que deverá retornar uma lista ordenada
dos registros que sofreram mudanças. A ordenação será dada por meio do timestamp
da aplicação. Apenas a versão mais recente de cada registro é garantida de ser
obtida, i.e., no caso de registros atualizados e na sequência removidos a API
poderá não mais fornecer os dados no estado intermediário, antes da remoção.


O serviço aceitará os seguintes parâmetros:

* `since` (string): Inicia a lista de resultados na mudança que segue
ao timestamp informado. Por padrão retornará desde a primeira mudança.
* `limit` (number): Limita o total de resultados obtidos. Deve ser utilizado
com o parâmetro since para iterar sobre os resultados de maneira paginada.
O valor padrão é 500.

Ficará a cargo do cliente a leitura e interpretação da lista de mudanças e
derivação de uma lista de tarefas de obtenção ou remoção de dados. O código
disponível [aqui](https://gist.github.com/gustavofonseca/363272c3745fa73ac32fe5ac673b783e)
usa uma máquina de estados para a lista de mudanças em uma lista de tarefas que
deverá ser executada pelo cliente a fim de replicar o estado final dos registros
do Kernel.

## Consequências

Cada um dos clientes deverá ser responsável por manter-se atualizado junto ao
Kernel por meio de requisições periódicas à API de mudanças. Essa técnica é
chamada de [Polling](https://en.wikipedia.org/wiki/Polling_(computer_science)).
É importante notar que a lista de mudanças **não** é um log de eventos capaz de
reproduzir os estados do Kernel ao longo do tempo. 
