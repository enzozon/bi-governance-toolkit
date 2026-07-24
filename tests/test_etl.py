import sqlite3
from datetime import date

from bi_toolkit.etl.carregar import carregar_dataset
from bi_toolkit.etl.gerar_dados import gerar_dataset


def test_gerar_dataset_retorna_todas_as_tabelas():
    dataset = gerar_dataset(date(2024, 1, 1), date(2024, 1, 7))

    assert set(dataset.keys()) == {
        "dim_tempo",
        "dim_posto",
        "dim_produto",
        "dim_forma_pagamento",
        "fato_vendas",
    }
    assert len(dataset["dim_tempo"]) == 7
    assert not dataset["fato_vendas"].empty


def test_fato_vendas_referencia_chaves_validas_das_dimensoes():
    dataset = gerar_dataset(date(2024, 1, 1), date(2024, 1, 7))
    fato = dataset["fato_vendas"]

    assert set(fato["posto_id"]).issubset(set(dataset["dim_posto"]["posto_id"]))
    assert set(fato["produto_id"]).issubset(set(dataset["dim_produto"]["produto_id"]))
    assert set(fato["data_id"]).issubset(set(dataset["dim_tempo"]["data_id"]))


def test_fato_vendas_nao_tem_valores_negativos():
    dataset = gerar_dataset(date(2024, 1, 1), date(2024, 1, 31))
    fato = dataset["fato_vendas"]

    assert (fato["quantidade"] >= 0).all()
    assert (fato["valor_total"] >= 0).all()


def test_gerar_dataset_e_deterministico_com_mesma_seed():
    a = gerar_dataset(date(2024, 1, 1), date(2024, 1, 10), seed=7)
    b = gerar_dataset(date(2024, 1, 1), date(2024, 1, 10), seed=7)

    assert a["fato_vendas"]["valor_total"].sum() == b["fato_vendas"]["valor_total"].sum()


def test_carregar_dataset_popula_banco_sqlite():
    dataset = gerar_dataset(date(2024, 1, 1), date(2024, 1, 7))
    conn = sqlite3.connect(":memory:")

    carregar_dataset(conn, dataset)

    total_linhas = conn.execute("SELECT COUNT(*) FROM fato_vendas").fetchone()[0]
    assert total_linhas == len(dataset["fato_vendas"])

    receita = conn.execute("SELECT SUM(valor_total) FROM fato_vendas").fetchone()[0]
    assert receita > 0


def test_view_margem_por_bandeira_agrega_corretamente():
    dataset = gerar_dataset(date(2024, 1, 1), date(2024, 1, 14))
    conn = sqlite3.connect(":memory:")
    carregar_dataset(conn, dataset)

    linhas = conn.execute(
        "SELECT bandeira, margem_pct FROM vw_margem_por_bandeira"
    ).fetchall()

    assert len(linhas) > 0
    for _, margem_pct in linhas:
        assert 0 <= margem_pct <= 100
