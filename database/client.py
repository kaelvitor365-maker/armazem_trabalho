from .model import Model
from data_functions import Database
from .config_database import default_database, starting_database


class Client:
    """
    Ponto de entrada do banco de dados: agrupa um Model já configurado
    para cada tabela do schema, evitando que quem for usar o banco precise
    instanciar Database/Model manualmente.
    """

    def __init__(self):
        """
        Construtor do Client.

        Cria a conexão padrão com o banco (via default_database()) e
        inicializa um Model para cada tabela existente no schema.
        """
        self._conn = Database(default_database())
        self.users = Model('users', self._conn)
        self.produtos = Model('produtos', self._conn)
        self.tipo_produtos = Model('tipo_produtos', self._conn)
        self.armazem = Model('armazem', self._conn)
        self.armazem = Model('log'), self._conn)