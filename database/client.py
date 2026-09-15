from .model import Model
from data_functions import Database
from .config_database import default_database, starting_database



class Client:
    def __init__(self):
        self._conn = Database(default_database())
        self.users = Model('users', self._conn)
        self.produtos = Model('produtos', self._conn)
        self.tipo_produtos = Model('tipo_produtos', self._conn)
        self.armazem = Model('armazem', self._conn)
