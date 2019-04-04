# 3. Armazenamento dos documentos em XML

Data: 2019-03-07

## Status

Aceito

## Contexto

O SciELO utiliza a especificação SciELO PS para representar os documentos
científicos que publica. Essa especificação se baseia na norma NISO JATS
Publishing DTD mais o Estilo SciELO para a representação dos metadados em XML.

O documento é composto por um arquivo XML, que contém os metadados do
*front-matter*, *body* e *back* do documento e opcionalmente suas traduções, e
os ativos digitais referenciados no XML. Os ativos digitais são referenciados
no XML por meio de URIs relativas ao arquivo XML. Juntos, o XML e seus ativos,
compõem um Pacote SciELO PS que poderá ser depositado e ingerido por uma coleção.

Desde 2015 o fluxo de ingestão de conteúdos da coleção Brasil recebe
exclusivamente documentos codificados desta forma e é esperado que no médio
prazo todas as coleções da Rede passem a operar exclusivamente com a ingestão
de XMLs.

## Decisão

Utilizaremos o XML SciELO PS como formato canônico para a representação dos
documentos no sistema. A integridade referencial entre o documento em XML e
seus ativos digitais será garantida pelo sistema.

O documento em XML é uma estrutura de dados que mistura características dos 
modelos semiestruturado -- onde atributos podem ser opcionais, multivalorados ou
compostos --, e não estruturado como é o caso do conteúdo narrativo do texto
em si. Essas características tornam pouco conveniente a representação do
documento segundo o modelo relacional normalizado, o estruturado ou o
semiestruturado que é implementado pela maioria dos bancos de dados NoSQL. 
Por esses motivos decidimos manter a representação do documento em XML e 
ofereceremos mecanismos convenientes para o acesso às porções semiestruturadas
dos seus dados.

## Consequências

Os documentos em XML e seus ativos digitais serão armazenados em um
*object store*, onde estarão acessíveis por meio de URLs públicas para a internet,
e referenciados por entidades do tipo *Document*, que serão responsáveis por
garantir a integridade referencial com seus ativos digitais.
