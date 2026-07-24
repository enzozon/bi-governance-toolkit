"""Dashboard Streamlit — o equivalente code-first do relatório que seria
publicado no Power BI Service. Um .pbix não é revisável em code review nem
roda em CI; este app lê o mesmo banco SQLite (sql/schema.sql) e reproduz os
mesmos KPIs e gráficos, para manter tudo testável e versionado em texto.

Rodar: streamlit run src/bi_toolkit/dashboard/app.py
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

RAIZ_PROJETO = Path(__file__).resolve().parents[3]
DB_PATH_PADRAO = RAIZ_PROJETO / "data" / "bi_toolkit.db"


@st.cache_data(show_spinner=False)
def carregar_vendas(caminho_db: str) -> pd.DataFrame:
    conn = sqlite3.connect(caminho_db)
    try:
        query = """
            SELECT
                t.data, t.ano, t.mes, t.nome_mes,
                p.nome AS posto, p.bandeira, p.uf, p.regiao,
                pr.nome AS produto, pr.categoria,
                fp.nome AS forma_pagamento,
                f.quantidade, f.valor_total, f.margem_total
            FROM fato_vendas f
            JOIN dim_tempo t  ON t.data_id  = f.data_id
            JOIN dim_posto p  ON p.posto_id = f.posto_id
            JOIN dim_produto pr ON pr.produto_id = f.produto_id
            JOIN dim_forma_pagamento fp ON fp.forma_pagamento_id = f.forma_pagamento_id
        """
        df = pd.read_sql_query(query, conn, parse_dates=["data"])
    finally:
        conn.close()
    return df


def formatar_moeda(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def render_kpis(df: pd.DataFrame) -> None:
    receita = df["valor_total"].sum()
    margem = df["margem_total"].sum()
    margem_pct = (margem / receita * 100) if receita else 0
    ticket_medio = df["valor_total"].mean() if not df.empty else 0
    litros = df.loc[df["categoria"] == "Combustível", "quantidade"].sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Receita total", formatar_moeda(receita))
    col2.metric("Margem", formatar_moeda(margem), f"{margem_pct:.1f}%")
    col3.metric("Ticket médio", formatar_moeda(ticket_medio))
    col4.metric("Litros vendidos", f"{litros:,.0f} L".replace(",", "."))


def render_graficos(df: pd.DataFrame) -> None:
    mensal = (
        df.groupby(["ano", "mes", "nome_mes"], as_index=False)["valor_total"]
        .sum()
        .sort_values(["ano", "mes"])
    )
    mensal["periodo"] = mensal["nome_mes"] + "/" + mensal["ano"].astype(str)
    fig_mensal = px.line(mensal, x="periodo", y="valor_total", markers=True, title="Receita mensal")
    st.plotly_chart(fig_mensal, use_container_width=True)

    col_esq, col_dir = st.columns(2)

    por_bandeira = df.groupby("bandeira", as_index=False)["valor_total"].sum()
    fig_bandeira = px.bar(
        por_bandeira.sort_values("valor_total", ascending=False),
        x="bandeira", y="valor_total", title="Receita por bandeira",
    )
    col_esq.plotly_chart(fig_bandeira, use_container_width=True)

    por_produto = df.groupby("produto", as_index=False)["valor_total"].sum()
    fig_produto = px.pie(
        por_produto, names="produto", values="valor_total", title="Receita por produto"
    )
    col_dir.plotly_chart(fig_produto, use_container_width=True)

    top_postos = (
        df.groupby("posto", as_index=False)["valor_total"]
        .sum()
        .nlargest(10, "valor_total")
    )
    fig_postos = px.bar(
        top_postos.sort_values("valor_total"),
        x="valor_total", y="posto", orientation="h", title="Top 10 postos por receita",
    )
    st.plotly_chart(fig_postos, use_container_width=True)


def render_filtros(df: pd.DataFrame) -> pd.DataFrame:
    with st.sidebar:
        st.header("Filtros")
        bandeiras = sorted(df["bandeira"].unique())
        selecionadas = st.multiselect("Bandeira", bandeiras, default=bandeiras)

        data_min, data_max = df["data"].min(), df["data"].max()
        intervalo = st.date_input(
            "Período", (data_min, data_max), min_value=data_min, max_value=data_max
        )

    filtrado = df[df["bandeira"].isin(selecionadas)]
    if isinstance(intervalo, tuple) and len(intervalo) == 2:
        inicio, fim = pd.Timestamp(intervalo[0]), pd.Timestamp(intervalo[1])
        filtrado = filtrado[(filtrado["data"] >= inicio) & (filtrado["data"] <= fim)]
    return filtrado


def main() -> None:
    st.set_page_config(page_title="BI Governance Toolkit — Vendas", layout="wide")
    st.title("⛽ Vendas de Postos — visão executiva")
    st.caption(
        "Dados sintéticos gerados por src/bi_toolkit/etl. Reproduz em código o "
        "que um relatório Power BI mostraria, para manter o dashboard testável e versionado."
    )

    caminho_db = os.environ.get("BI_TOOLKIT_DB_PATH", str(DB_PATH_PADRAO))
    if not Path(caminho_db).exists():
        st.warning(
            f"Banco não encontrado em `{caminho_db}`. Rode "
            "`python -m bi_toolkit.etl.carregar` para gerar os dados de exemplo."
        )
        st.stop()

    df = carregar_vendas(caminho_db)
    df_filtrado = render_filtros(df)

    render_kpis(df_filtrado)
    st.divider()
    render_graficos(df_filtrado)


if __name__ == "__main__":
    main()
