"""Carrega o dataset sintético (gerar_dados.gerar_dataset) num banco SQLite,
aplicando o esquema estrela definido em sql/schema.sql.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from bi_toolkit.etl.gerar_dados import gerar_dataset

RAIZ_PROJETO = Path(__file__).resolve().parents[3]
SCHEMA_SQL = RAIZ_PROJETO / "sql" / "schema.sql"

TABELAS_NA_ORDEM = [
    "dim_tempo",
    "dim_posto",
    "dim_produto",
    "dim_forma_pagamento",
    "fato_vendas",
]


def aplicar_schema(conn: sqlite3.Connection, schema_path: Path = SCHEMA_SQL) -> None:
    conn.executescript(schema_path.read_text(encoding="utf-8"))


def carregar_dataset(
    conn: sqlite3.Connection, dataset: dict[str, pd.DataFrame] | None = None
) -> None:
    """Popula o banco. Idempotente: limpa as tabelas antes de inserir de novo."""
    dataset = dataset or gerar_dataset()

    aplicar_schema(conn)
    cursor = conn.cursor()
    for tabela in reversed(TABELAS_NA_ORDEM):
        cursor.execute(f"DELETE FROM {tabela}")

    for tabela in TABELAS_NA_ORDEM:
        df = dataset[tabela]
        colunas = [c for c in df.columns if not (tabela == "fato_vendas" and c == "venda_id")]
        df[colunas].to_sql(tabela, conn, if_exists="append", index=False)

    conn.commit()


def criar_banco(caminho_db: str | Path) -> None:
    caminho_db = Path(caminho_db)
    caminho_db.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(caminho_db) as conn:
        carregar_dataset(conn)


if __name__ == "__main__":
    import os

    destino = os.environ.get("BI_TOOLKIT_DB_PATH", "data/bi_toolkit.db")
    criar_banco(destino)
    print(f"Banco criado em: {destino}")
