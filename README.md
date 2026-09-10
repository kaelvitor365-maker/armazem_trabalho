# ARMAZEM

este projeto está sendo criado para auxiliar no gerenciamento de armazéns

## SUMARIO

 - INTEGRANTES
 - FUNCIONAMENTO
 - FERRAMENTAS
 - ARQUITETURA
 - REQUISITOS
 - INSTALAÇÃO

## INTEGRANTES

 - Vitor Kael
 - Fernando Moskven
 - Higor
 - Davi Fideles

## FUNCIONAMENTO

funcionará permitindo você inserir novos itens, deletar novos itens.

além de mostrar a quantidade que tem, permitindo você fazer a incrementação e a decrementação dos itens já existentes no armazem.

o design será de somente uma página principal, e três secundárias, para facilitar a visão do usuário, contendo:

|contém|descrição|
|------|---------|
|`Novo produto`| ele irá para uma página que mostrará uma caixa de texto para inserir o nome, e um botão `inserir` para finalizar a ação|
|`Pesquisar`| ele irá para uma página podendo pesquisar por algum específico, ou todos, e quando você adicionar todos na sua lista de pesquisa, ele irá criar uma lista com os produtos desejados, e se não tiver, ele vai avisar. existirá um botão `Listar Tudo` que ao clicar irá retornar uma pesquisa com todos os produtos|
|`Inserir ou Retirar`| ele irá para uma página contendo um botão que ao clicar muda de inserir para retirar, e vice-versa. Caso o valor de retirada transforme o valor em negativo, essa ação será bloqueada|

## FERRAMENTAS

utilizaremos as lib's publicas:

|ferramenta|descrição|
|----------|---------|
|`flet`|utilizado para gerar uma interface desktop|
|`sqlite3`|utilizado para conectar ao banco de dados|

e criaremos um `rest_service` para simular o funcionamento e criação de backend, além de facilitar, organiza a implementação.

## ARQUITETURA

a arvore de arquivos é:

```
armazem
├─ README.md
├─ __init__.py
├─ __main__.py
├─ api
│  ├─ __init__.py
│  └─ api_client.py
├─ database
│  ├─ __init__.py
│  ├─ client.py
│  ├─ data_functions
│  │  └─ __init__.py
│  └─ schema.sql
├─ docs
│  └─ makefile.md
├─ interface
│  ├─ __init__.py
│  ├─ app.py
│  ├─ style
│  └─ widgets
│     └─ __init__.py
├─ makefile
├─ pyproject.toml
└─ rest_service
   ├─ __init__.py
   ├─ errors
   │  └─ __init__.py
   ├─ rest_creator.py
   └─ routers
      └─ __init__.py

```

|pasta|descrição|
|-----|---------|
|`interface`| esta pasta está reservada para a criação da interface grafica do app|
|`api`| esta pasta está responsável pelo controle de dados do nosso aplicativo (`backend`)|
|`rest_service`| esta pasta estará localizada a implementação da nossa classe que simula o modelo de API REST, porém feito localmente|
|`database`| esta pasta será utilizada para criar e gerenciar o banco de dados|

## REQUISITOS

|requisitos|versão|
|----------|------|
|`python`| 3.10+ |
|`flet`| 0.86.5+ |

## INSTALAÇÃO

para poder executar nosso aplicativo você deve clonar o repositório, e executar o comando `make install`, e então `make run`.
