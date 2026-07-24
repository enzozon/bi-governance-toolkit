"""Gerador de dados sintéticos de vendas para uma rede de postos de combustível.

Não usa nenhum dado real da Ipiranga ou de qualquer empresa — é um dataset
fabricado, com seed fixa, para dar suporte ao esquema estrela em sql/schema.sql
e ao dashboard do projeto.
"""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

SEED = 42

POSTOS = [
    ("Posto Matriz Vitória", "Vitória", "ES", "Sudeste", "Ipiranga", "Matriz"),
    ("Posto Vila Velha Centro", "Vila Velha", "ES", "Sudeste", "Ipiranga", "Franquia"),
    ("Posto Serra Norte", "Serra", "ES", "Sudeste", "Ipiranga", "Franquia"),
    ("Posto Cariacica BR-262", "Cariacica", "ES", "Sudeste", "Bandeira Branca", "Franquia"),
    ("Posto Linhares Rodovia", "Linhares", "ES", "Sudeste", "Ipiranga", "Franquia"),
    ("Posto BH Savassi", "Belo Horizonte", "MG", "Sudeste", "Ipiranga", "Franquia"),
    ("Posto Contagem Industrial", "Contagem", "MG", "Sudeste", "Bandeira Branca", "Franquia"),
    ("Posto Rio Barra", "Rio de Janeiro", "RJ", "Sudeste", "Ipiranga", "Franquia"),
    ("Posto Curitiba Batel", "Curitiba", "PR", "Sul", "Ipiranga", "Franquia"),
    ("Posto Salvador Orla", "Salvador", "BA", "Nordeste", "Ipiranga", "Franquia"),
]

PRODUTOS = [
    ("Gasolina Comum", "Combustível", "litro"),
    ("Gasolina Aditivada", "Combustível", "litro"),
    ("Etanol", "Combustível", "litro"),
    ("Diesel S10", "Combustível", "litro"),
    ("GNV", "Combustível", "litro"),
    ("Loja de Conveniência", "Conveniência", "unidade"),
]

# (nome, preço médio de venda, custo médio) — ordem casada com PRODUTOS.
PRECOS = {
    "Gasolina Comum": (5.89, 5.10),
    "Gasolina Aditivada": (6.09, 5.25),
    "Etanol": (4.29, 3.55),
    "Diesel S10": (6.15, 5.40),
    "GNV": (4.79, 3.90),
    "Loja de Conveniência": (12.50, 8.00),
}

FORMAS_PAGAMENTO = ["Dinheiro", "Débito", "Crédito", "PIX", "Frota/Convênio"]

DIAS_SEMANA_PT = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]


def gerar_dim_tempo(data_inicio: date, data_fim: date) -> pd.DataFrame:
    dias = pd.date_range(data_inicio, data_fim, freq="D")
    return pd.DataFrame(
        {
            "data_id": [int(d.strftime("%Y%m%d")) for d in dias],
            "data": [d.strftime("%Y-%m-%d") for d in dias],
            "ano": dias.year,
            "trimestre": dias.quarter,
            "mes": dias.month,
            "nome_mes": [d.strftime("%B") for d in dias],
            "dia": dias.day,
            "dia_semana": [DIAS_SEMANA_PT[d.weekday()] for d in dias],
            "fim_de_semana": [1 if d.weekday() >= 5 else 0 for d in dias],
        }
    )


def gerar_dim_posto() -> pd.DataFrame:
    df = pd.DataFrame(
        POSTOS, columns=["nome", "cidade", "uf", "regiao", "bandeira", "tipo"]
    )
    df.insert(0, "posto_id", range(1, len(df) + 1))
    df["data_abertura"] = "2018-01-01"
    return df


def gerar_dim_produto() -> pd.DataFrame:
    df = pd.DataFrame(PRODUTOS, columns=["nome", "categoria", "unidade"])
    df.insert(0, "produto_id", range(1, len(df) + 1))
    return df


def gerar_dim_forma_pagamento() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "forma_pagamento_id": range(1, len(FORMAS_PAGAMENTO) + 1),
            "nome": FORMAS_PAGAMENTO,
        }
    )


def gerar_fato_vendas(
    dim_tempo: pd.DataFrame,
    dim_posto: pd.DataFrame,
    dim_produto: pd.DataFrame,
    dim_forma_pagamento: pd.DataFrame,
    seed: int = SEED,
) -> pd.DataFrame:
    """Simula uma venda por (posto, produto, dia) com quantidade e forma de
    pagamento aleatórias, aplicando sazonalidade simples de fim de semana."""
    rng = np.random.default_rng(seed)
    linhas = []

    for _, dia in dim_tempo.iterrows():
        fator_fds = 1.25 if dia["fim_de_semana"] else 1.0
        for _, posto in dim_posto.iterrows():
            for _, produto in dim_produto.iterrows():
                # nem todo posto vende conveniência todo dia; simula ausência de venda
                if rng.random() < 0.05:
                    continue

                preco, custo = PRECOS[produto["nome"]]
                base_qtd = 350 if produto["unidade"] == "litro" else 40
                quantidade = max(0.0, rng.normal(base_qtd, base_qtd * 0.2) * fator_fds)
                variacao_preco = rng.normal(1.0, 0.02)
                valor_unitario = round(preco * variacao_preco, 3)
                custo_unitario = round(custo * rng.normal(1.0, 0.015), 3)
                valor_total = round(quantidade * valor_unitario, 2)
                margem_total = round(quantidade * (valor_unitario - custo_unitario), 2)
                forma_pagamento_id = int(
                    rng.choice(dim_forma_pagamento["forma_pagamento_id"])
                )

                linhas.append(
                    {
                        "data_id": int(dia["data_id"]),
                        "posto_id": int(posto["posto_id"]),
                        "produto_id": int(produto["produto_id"]),
                        "forma_pagamento_id": forma_pagamento_id,
                        "quantidade": round(quantidade, 2),
                        "valor_unitario": valor_unitario,
                        "custo_unitario": custo_unitario,
                        "valor_total": valor_total,
                        "margem_total": margem_total,
                    }
                )

    return pd.DataFrame(linhas)


def gerar_dataset(
    data_inicio: date = date(2024, 1, 1),
    data_fim: date = date(2025, 12, 31),
    seed: int = SEED,
) -> dict[str, pd.DataFrame]:
    """Gera o conjunto completo de dimensões + fato pronto para carga."""
    dim_tempo = gerar_dim_tempo(data_inicio, data_fim)
    dim_posto = gerar_dim_posto()
    dim_produto = gerar_dim_produto()
    dim_forma_pagamento = gerar_dim_forma_pagamento()
    fato_vendas = gerar_fato_vendas(
        dim_tempo, dim_posto, dim_produto, dim_forma_pagamento, seed=seed
    )
    return {
        "dim_tempo": dim_tempo,
        "dim_posto": dim_posto,
        "dim_produto": dim_produto,
        "dim_forma_pagamento": dim_forma_pagamento,
        "fato_vendas": fato_vendas,
    }
