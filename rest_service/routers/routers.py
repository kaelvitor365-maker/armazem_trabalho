import typing

class Router:
    """
    Cria rotas utilizadas pelo RestConfig
    """
    @staticmethod
    def _new_routers(t_route: str, route: str):
        """
        cria os decorators ao ser chamado

        ARGS:
            t_route: é o tipo de rota (GET, POST...)
            route: é a rota

        """
        def decorator(exec: typing.Callable[
            [dict[str, typing.Any]],
            typing.Any
        ]
        ):
            return Router(t_route, route, exec)
        return decorator

    @staticmethod
    def get(route: str):
        """
        cria uma rota modelo get

        ARGS:
            route: a rota desejada
        """
        return Router._new_routers("GET", route)


    @staticmethod
    def post(route: str):
        """
        cria uma rota modelo post
        
        ARGS:
            route: a rota desejada
            """
        return Router._new_routers("POST", route)

    @staticmethod
    def put(route: str):
        """
        cria uma rota modelo put
        
        ARGS:
            route: a rota desejada
                """
        return Router._new_routers("PUT", route)

    @staticmethod
    def patch(route: str):
        """
        cria uma rota modelo patch
        
        ARGS:
            route: a rota desejada
        """
        return Router._new_routers("PATCH", route)

    @staticmethod
    def delete(route: str):
        """
        cria uma rota modelo delete
        
        ARGS:
            route: a rota desejada
        """
        return Router._new_routers("DELETE", route)

    def __init__(self,type_route: str, route: str, exec: typing.Callable[[dict[str, typing.Any]], typing.Any]):
        """
        contructor do Router

        Args:
            type_route: o tipo de rota (GET, POST, PUT, PATCH. DELETE)
            route: a rota que será chamada no cliente
            exec: recebe a função que será chamada na rota

        
        """
        self._type = type_route.upper()
        self._route = route
        self._exec = exec

    @property
    def route(self) -> str:
        """
        getter para ver a rota

        """
        return self._route

    @property
    def type(self) -> str:
        """
        getter para o tipo de rota

        """
        return self._type
    def __call__(self):
        """
        retorna a função chamável
        """
        return self._exec