-- Esquema estrela para vendas de uma rede de postos de combustível.
-- Desenhado para ser aberto tanto por scripts Python (sqlite3) quanto
-- importado como fonte de dados no Power BI Desktop (Get Data > SQLite).

PRAGMA foreign_keys = ON;

-- ===================== DIMENSÕES =====================

CREATE TABLE IF NOT EXISTS dim_tempo (
    data_id      INTEGER PRIMARY KEY,   -- formato AAAAMMDD, ex: 20260115
    data         TEXT NOT NULL,          -- ISO-8601, ex: '2026-01-15'
    ano          INTEGER NOT NULL,
    trimestre    INTEGER NOT NULL,
    mes          INTEGER NOT NULL,
    nome_mes     TEXT NOT NULL,
    dia          INTEGER NOT NULL,
    dia_semana   TEXT NOT NULL,
    fim_de_semana INTEGER NOT NULL       -- 0/1
);

CREATE TABLE IF NOT EXISTS dim_posto (
    posto_id     INTEGER PRIMARY KEY,
    nome         TEXT NOT NULL,
    cidade       TEXT NOT NULL,
    uf           TEXT NOT NULL,
    regiao       TEXT NOT NULL,
    bandeira     TEXT NOT NULL,          -- ex: 'Ipiranga', 'Bandeira Branca'
    tipo         TEXT NOT NULL,          -- 'Matriz' ou 'Franquia'
    data_abertura TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_produto (
    produto_id   INTEGER PRIMARY KEY,
    nome         TEXT NOT NULL,          -- ex: 'Gasolina Comum'
    categoria    TEXT NOT NULL,          -- 'Combustível' ou 'Conveniência'
    unidade      TEXT NOT NULL           -- 'litro' ou 'unidade'
);

CREATE TABLE IF NOT EXISTS dim_forma_pagamento (
    forma_pagamento_id INTEGER PRIMARY KEY,
    nome         TEXT NOT NULL           -- 'Dinheiro', 'Débito', 'Crédito', 'PIX', 'Frota/Convênio'
);

-- ===================== FATO =====================

CREATE TABLE IF NOT EXISTS fato_vendas (
    venda_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    data_id             INTEGER NOT NULL REFERENCES dim_tempo(data_id),
    posto_id            INTEGER NOT NULL REFERENCES dim_posto(posto_id),
    produto_id          INTEGER NOT NULL REFERENCES dim_produto(produto_id),
    forma_pagamento_id  INTEGER NOT NULL REFERENCES dim_forma_pagamento(forma_pagamento_id),
    quantidade          REAL NOT NULL,   -- litros ou unidades, conforme dim_produto.unidade
    valor_unitario       REAL NOT NULL,
    custo_unitario       REAL NOT NULL,
    valor_total          REAL NOT NULL,
    margem_total          REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_fato_vendas_data     ON fato_vendas(data_id);
CREATE INDEX IF NOT EXISTS idx_fato_vendas_posto    ON fato_vendas(posto_id);
CREATE INDEX IF NOT EXISTS idx_fato_vendas_produto  ON fato_vendas(produto_id);

-- ===================== VIEWS DE APOIO =====================

-- Vendas mensais por posto: base para o cartão "Vendas do mês" do dashboard.
CREATE VIEW IF NOT EXISTS vw_vendas_mensais AS
SELECT
    t.ano,
    t.mes,
    t.nome_mes,
    p.posto_id,
    p.nome        AS posto_nome,
    p.bandeira,
    SUM(f.valor_total)  AS receita_total,
    SUM(f.margem_total) AS margem_total,
    SUM(f.quantidade)   AS volume_total
FROM fato_vendas f
JOIN dim_tempo t  ON t.data_id  = f.data_id
JOIN dim_posto p  ON p.posto_id = f.posto_id
GROUP BY t.ano, t.mes, p.posto_id;

-- Margem percentual por bandeira: usada na auditoria de performance por franquia.
CREATE VIEW IF NOT EXISTS vw_margem_por_bandeira AS
SELECT
    p.bandeira,
    SUM(f.valor_total)  AS receita_total,
    SUM(f.margem_total) AS margem_total,
    ROUND(100.0 * SUM(f.margem_total) / NULLIF(SUM(f.valor_total), 0), 2) AS margem_pct
FROM fato_vendas f
JOIN dim_posto p ON p.posto_id = f.posto_id
GROUP BY p.bandeira;
