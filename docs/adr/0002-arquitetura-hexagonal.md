# 2. Arquitetura hexagonal

Data: 2019-03-07

## Status

Aceito

## Contexto

Nós devemos organizar o código, abstrações e dependências deste projeto de
forma que seja possível focar na implementação do que é inerente ao négocio e
postergar decisões e implementação relativas ao que é acessório. Aqui,
consideramos acessório: interfaces externas, bancos de dados, brokers de
mensagens, interfaces de usuário etc.

## Decisão

Utilizaremos a Arquitetura hexagonal, conforme descrita por Alistair Cockburn,
para obtermos e mantermos uma base de código com fronteiras de responsabilidades
entre camadas e componentes bem definidas.

Foram criadas as seguintes fronteiras:

1. *domain*: Contém implementações dos tipos de entidade do negócio (*Journal,
  Document etc*) e de classes que implementam regras de negócios;
2. *interfaces*: Contém as definições das interfaces, também chamadas de *ports*,
  que devem ser implementadas pelos adaptadores. Componentes externos, como por
  exemplo bancos de dados, devem ter suas interfaces definidas;
3. *services*: Define uma fronteira da aplicação e seu conjunto de operações
  pela perspectiva de quem faz interface com clientes. Encapsula lógica de negócios
  e transações;
4. *adapters*: Contém classes que implementam as interfaces definidas em
  `interfaces`.

## Consequências

Uma base de código facilmente testável, de baixa complexidade na manutenção e
que nos permita a troca de componentes externos -- como banco de dados,
framework web, sistemas de caching, barramento de eventos etc -- quando desejado
e com uma quantidade de esforço razoável.

Para mais informação sugiro as fontes:

* https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html
* https://blog.cleancoder.com/uncle-bob/2016/01/04/ALittleArchitecture.html
