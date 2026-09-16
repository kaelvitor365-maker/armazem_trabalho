

DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS tipo_produtos;
DROP TABLE IF EXISTS produtos;
DROP TABLE IF EXISTS armazem;
DROP TABLE IF EXISTS log;

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    token TEXT UNIQUE NOT NULL
);

CREATE TABLE tipo_produtos (
    id INTEGER PRIMARY KEY,
    id_user INTEGER NOT NULL,
    typename TEXT NOT NULL,

    UNIQUE (id_user, typename),
    FOREIGN KEY (id_user) REFERENCES users (id)
);

CREATE TABLE produtos (
    id INTEGER PRIMARY KEY,
    id_user INTEGER NOT NULL,
    name_produto TEXT NOT NULL,
    price INTEGER NOT NULL,

    CHECK (price > 0),
    UNIQUE (id_user, name_produto),
    FOREIGN KEY (id_user) REFERENCES users (id)
);

CREATE TABLE armazem (
    id INTEGER PRIMARY KEY,
    id_tipo_produto INTEGER NOT NULL,
    id_produto INTEGER NOT NULL,
    quantidade INTEGER NOT NULL DEFAULT 0,

    CHECK (quantidade >= 0),
    UNIQUE (id_produto, id_tipo_produto),
    FOREIGN KEY (id_produto) REFERENCES produtos (id),
    FOREIGN KEY (id_tipo_produto) REFERENCES tipo_produtos (id)
);

CREATE TABLE log (
    id INTEGER PRIMARY KEY,
    id_user INTEGER NOT NULL,
    id_produto INTEGER NOT NULL,
    quant_transacao INTEGER NOT NULL,
    transacao INTEGER NOT NULL,
    data TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CHECK (quant_transacao > 0),
    CHECK (transacao IN (0, 1)),
    FOREIGN KEY (id_user) REFERENCES users (id),
    FOREIGN KEY (id_produto) REFERENCES produtos (id)
);