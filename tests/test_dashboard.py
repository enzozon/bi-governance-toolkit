import sqlite3
from datetime import date

from bi_toolkit.dashboard.app import carregar_vendas, formatar_moeda
from bi_toolkit.etl.carregar import carregar_dataset
from bi_toolkit.etl.gerar_dados import gerar_dataset


def test_formatar_moeda_usa_padrao_brasileiro():
    assert formatar_moeda(1234.5) == "R$ 1.234,50"
    assert formatar_moeda(0) == "R$ 0,00"


def test_carregar_vendas_junta_dimensoes_e_fato(tmp_path):
    caminho_db = tmp_path / "teste.db"
    dataset = gerar_dataset(date(2024, 1, 1), date(2024, 1, 7))
    conn = sqlite3.connect(caminho_db)
    carregar_dataset(conn, dataset)
    conn.close()

    df = carregar_vendas(str(caminho_db))

    colunas_esperadas = {
        "data", "ano", "mes", "nome_mes", "posto", "bandeira", "uf", "regiao",
        "produto", "categoria", "forma_pagamento", "quantidade", "valor_total",
        "margem_total",
    }
    assert colunas_esperadas.issubset(df.columns)
    assert len(df) == len(dataset["fato_vendas"])
    assert df["valor_total"].sum() > 0
