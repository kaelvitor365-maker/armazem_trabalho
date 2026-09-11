from .rest_creator import RestConfig

import typing


class RestClient(RestConfig):
    """
    Consome as rotas já registradas em um RestConfig, a partir de uma porta.

    Herda de RestConfig apenas para ter acesso ao dicionário compartilhado
    de rotas (_port). Sobrescreve get, post, put, patch e delete para que,
    ao invés de registrar rotas, eles chamem as rotas já existentes.
    """

    def __init__(self, port: str):
        """
        Construtor do RestClient.

        ARGS:
            port: a porta associada às rotas que serão consumidas.
                Deve corresponder a uma porta já criada por um RestConfig.

        Raises:
            ValueError: se não existir nenhuma api registrada nessa porta.
        """
        self.porta = str(port).strip()
        if not (self.porta in self._port):
            raise ValueError(f"A PORTA {port} NÃO EXISTE")

        self._routers = self._port[self.porta]

    def use(self, t_route: str, route: str, req: dict[str, typing.Any]) -> typing.Any:
        """
        Sobrescreve o use() de RestConfig: aqui, chama a rota já registrada,
        ao invés de registrar uma nova.

        ARGS:
            t_route: o método HTTP da rota (GET, POST, PUT, PATCH, DELETE).
            route: a rota que será chamada.
            req: o dicionário de parâmetros/corpo enviado para o handler.

        Returns:
            O que a função registrada na rota retornar.

        Raises:
            ValueError: se o método (t_route) não existir na estrutura,
                ou se a rota não estiver registrada nesse método.
        """
        if t_route not in self._routers:
            raise ValueError(f"METODO {t_route} INVALIDO")
        if route not in self._routers[t_route]:
            raise ValueError(f"NÃO EXISTE A ROTA {t_route} {route}")
        return self._routers[t_route][route](req)

    def get(self, route: str, req: dict[str, typing.Any] = None):
        """
        Atalho para use("GET", ...).

        ARGS:
            route: a rota a ser chamada.
            req: parâmetros opcionais para a rota.
        """
        return self.use("GET", route, req or {})

    def post(self, route: str, req: dict[str, typing.Any] = None):
        """
        Atalho para use("POST", ...).

        ARGS:
            route: a rota a ser chamada.
            req: corpo/parâmetros opcionais para a rota.
        """
        return self.use("POST", route, req or {})

    def put(self, route: str, req: dict[str, typing.Any] = None):
        """
        Atalho para use("PUT", ...).

        ARGS:
            route: a rota a ser chamada.
            req: corpo/parâmetros opcionais para a rota.
        """
        return self.use("PUT", route, req or {})

    def patch(self, route: str, req: dict[str, typing.Any] = None):
        """
        Atalho para use("PATCH", ...).

        ARGS:
            route: a rota a ser chamada.
            req: corpo/parâmetros opcionais para a rota.
        """
        return self.use("PATCH", route, req or {})

    def delete(self, route: str, req: dict[str, typing.Any] = None):
        """
        Atalho para use("DELETE", ...).

        ARGS:
            route: a rota a ser chamada.
            req: parâmetros opcionais para a rota.
        """
        return self.use("DELETE", route, req or {})