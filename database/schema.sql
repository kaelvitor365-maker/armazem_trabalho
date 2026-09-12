
--
-- tipos de produtos 1-n | id_user id_tipo id_produto quant| n-1 |produtos preco|
--

DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS tipos_produtos;
DROP TABLE IF EXISTS produtos;
DROP TABLE IF EXISTS armazem;

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    token TEXT UNIQUE
);


CREATE TABLE tipos_produtos (
    id INTEGER PRIMARY KEY,
    id_user INTEGER NOT NULL,
    tipo TEXT NOT NULL,

    FOREIGN KEY (id_user) REFERENCES users(id)
);

CREATE TABLE produtos (
    id INTEGER PRIMARY KEY,
    id_user INTEGER NOT NULL,
    name_produto TEXT NOT NULL,
    preco INTEGER DEFAULT 0,

    UNIQUE (id_user, name_produto),
    FOREIGN KEY (id_user) REFERENCES users(id)
);


CREATE TABLE armazem (
    id INTEGER PRIMARY KEY,
    id_tipo_de_produto INTEGER  NOT NULL,
    id_produto INTEGER  NOT NULL,
    quantidade INTEGER NOT NULL DEFAULT 0,

    UNIQUE (id_produto, id_tipo_de_produto),
    FOREIGN KEY (id_tipo_de_produto) REFERENCES tipos_produtos (id),
    FOREIGN KEY (id_produto) REFERENCES produtos (id)
);

