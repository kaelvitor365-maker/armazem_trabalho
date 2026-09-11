# REST Service (DSL interna)

Este módulo simula o funcionamento de uma API REST **localmente**, sem precisar de um servidor de verdade rodando numa porta de rede. A ideia é organizar a comunicação entre a interface (Flet) e a camada de dados (banco/API) do mesmo jeito que um back-end real faria: por rotas, métodos HTTP e handlers.

## Peças principais

| Classe | Papel |
|---|---|
| `RestConfig` | Registra rotas (define o que existe) |
| `Router` | Representa uma rota isolada, criada fora do `RestConfig` |
| `RestClient` | Consome as rotas já registradas (chama o que existe) |

## Conceito de "porta"

Como não existe rede de verdade aqui, a "porta" é só um identificador de string usado para agrupar um conjunto de rotas — como se fosse o endereço de uma API específica dentro do mesmo programa. Isso permite, teoricamente, ter mais de um conjunto de rotas isolado ao mesmo tempo (ex: uma porta para itens, outra para usuários), embora o projeto atual normalmente use apenas uma.

```python
config = RestConfig("8000")
```

Se você tentar criar duas configurações com a mesma porta, um `ValueError` é lançado — cada porta só pode ter um dono.

## 1. Registrando rotas com `RestConfig`

### Estilo decorator (recomendado)

```python
config = RestConfig("8000")

@config.get("/itens")
def listar_itens(req: dict):
    return {"itens": []}, 200

@config.post("/itens")
def criar_item(req: dict):
    novo_item = {"nome": req["nome"], "quantidade": req["quantidade"]}
    return novo_item, 201
```

Toda função de rota recebe **um único parâmetro**, `req: dict`, que carrega os dados enviados (parâmetros ou corpo da requisição simulada).

Métodos disponíveis: `.get()`, `.post()`, `.put()`, `.patch()`, `.delete()`.

### Estilo `Router` + `use()`

Alternativa para quem prefere declarar a rota separadamente antes de registrar (útil ao organizar rotas em outro arquivo, sem precisar de acesso direto ao `config`):

```python
from routers import Router

@Router.get("/produtos")
def listar_produtos(req: dict):
    return {"produtos": []}, 200

config.use(listar_produtos)
```

Repare que, após o decorator `@Router.get(...)`, a variável `listar_produtos` deixa de ser uma função comum e passa a ser uma instância de `Router` — ela guarda o método HTTP, a rota e a função original internamente, prontas para serem registradas com `.use()`.

## 2. Consumindo rotas com `RestClient`

O `RestClient` se conecta a uma porta **já configurada** e permite chamar as rotas registradas:

```python
client = RestClient("8000")

resultado, status = client.get("/itens")
resultado, status = client.post("/itens", {"nome": "Parafuso", "quantidade": 100})
```

Por baixo dos panos, todos os métodos (`get`, `post`, `put`, `patch`, `delete`) são atalhos que chamam `use()`:

```python
client.use("GET", "/itens", {})
```

## 3. Tratamento de erros

O sistema lança `ValueError` (não retorna silenciosamente `None` ou um dicionário de erro) nos seguintes casos:

| Situação | Mensagem |
|---|---|
| Criar `RestConfig` com uma porta já existente | `Existe uma api associada a porta {port}` |
| Criar `RestClient` com uma porta que não existe | `A PORTA {port} NÃO EXISTE` |
| Chamar `use()`/atalho com um método HTTP inválido | `METODO {t_route} INVALIDO` |
| Chamar uma rota que não foi registrada nesse método | `NÃO EXISTE A ROTA {t_route} {route}` |

Recomenda-se sempre tratar essas exceções na camada que consome o `RestClient` (ex: na interface Flet), evitando que o app quebre inesperadamente:

```python
try:
    resultado, status = client.get("/itens-que-nao-existe")
except ValueError as erro:
    print("Erro ao chamar a rota:", erro)
```

## Por que essa arquitetura (herança + sobrescrita)

`RestClient` herda de `RestConfig` apenas para compartilhar o dicionário interno `_port` (atributo de classe, comum a todas as instâncias). Os métodos `get`, `post`, `put`, `patch`, `delete` e `use` são **sobrescritos** no `RestClient`, mudando completamente de propósito:

- Em `RestConfig`: **registram** uma nova rota (decorators)
- Em `RestClient`: **chamam** uma rota já registrada

Essa não é uma relação de herança "clássica" (o `RestClient` não é conceitualmente um "tipo de" `RestConfig`), mas sim um atalho prático para reaproveitar o armazenamento de rotas sem duplicar estruturas de dados.

## Exemplo completo de ponta a ponta

```python
from rest_creator import RestConfig
from rest_client import RestClient

# 1. Configuração (normalmente feita uma vez, ao iniciar o app)
config = RestConfig("8000")

@config.get("/itens")
def listar_itens(req: dict):
    return {"itens": ["Parafuso", "Porca"]}, 200

# 2. Consumo (feito pela interface, sempre que precisar dos dados)
client = RestClient("8000")
resultado, status = client.get("/itens")

print(resultado, status)
# ({'itens': ['Parafuso', 'Porca']}, 200)
```