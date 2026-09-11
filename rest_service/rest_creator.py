import typing, routers


## TIPAGEM para facilitar na identificação de funções
Handler = typing.Callable[
    [dict[str, typing.Any]],
    typing.Any
]

class RestConfig:
    """
    Classe utilizado para configurar
    """
    _port: dict[
        str, # PORTS
        dict[
            str, #T ROUTERS
            dict[
                str, # ROUTERS
                Handler
            ]
        ]
    ] = {}

    def __init__(self, port: str) -> None:
        """
        contrutor do RestConfig

        ARGS:
            port: a porta que estará as rotas (nescessaria para o RestClient)

        """

        self.porta = str(port).strip()
        if self.porta in self._port:
            raise ValueError(f"Existe uma api associada a porta {port}")

        self._port[
            self.porta
            ] = {
                "GET": {},
                "POST": {},
                "PUT": {},
                "PATCH": {},
                "DELETE": {}
            }

    def use(self, route: routers.Router) -> None:
        """
        utiliza uma rota feita com a Classe Router

        route: a classe criada com a rota
        """
        self._port[self.porta][route.type][route.route] = route()

    def _generator_dec(self, t_route: str, route: str):
        def decorator(exec: Handler):
            self._port[self.porta][t_route][route] = exec
            return exec
        return decorator

    def get(self, route: str):
        """
        decorator nescessario para criar rotas sem usar a classe Router

        ARGS:
            route: a rota que será salva
        """
        return self._generator_dec("GET", route)

    def post(self, route: str):
        """
        decorator nescessario para criar rotas sem usar a classe Router

        ARGS:
            route: a rota que será salva
        """
        return self._generator_dec("POST", route)

    def put(self, route: str):
        """
        decorator nescessario para criar rotas sem usar a classe Router

        ARGS:
            route: a rota que será salva
        """
        return self._generator_dec("PUT", route)

    def patch(self, route: str):
        """
        decorator nescessario para criar rotas sem usar a classe Router

        ARGS:
            route: a rota que será salva
        """
        return self._generator_dec("PATCH", route)

    def delete(self, route: str):
        """
        decorator nescessario para criar rotas sem usar a classe Router

        ARGS:
            route: a rota que será salva
        """
        return self._generator_dec("DELETE", route)

    def routers(self) -> type[routers.Router]:
        """
        Expõe a classe Router, para criação de rotas alternativas ao decorator.

        Returns:
            A classe Router (não uma instância).
        """
        return routers.Router
