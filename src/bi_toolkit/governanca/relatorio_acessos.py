"""Relatório consolidado de quem tem acesso a quê no Power BI Service.

Junta workspace + usuário + nível de acesso numa tabela única, sinalizando
domínios de e-mail fora da organização (possível acesso externo indevido).
"""
from __future__ import annotations

import pandas as pd

from bi_toolkit.governanca.powerbi_client import PowerBIClient

COLUNAS = [
    "workspace_id",
    "workspace_nome",
    "usuario",
    "nivel_acesso",
    "acesso_externo",
]


def gerar_relatorio_acessos(
    client: PowerBIClient, dominio_organizacao: str
) -> pd.DataFrame:
    """Retorna um DataFrame com uma linha por (workspace, usuário)."""
    linhas: list[dict[str, str | bool]] = []

    for ws in client.listar_workspaces():
        usuarios = client.listar_usuarios_workspace(ws["id"])
        for usuario in usuarios:
            identificador = usuario.get("emailAddress") or usuario.get("identifier", "")
            dominio = identificador.split("@")[-1].lower() if "@" in identificador else ""
            linhas.append(
                {
                    "workspace_id": ws["id"],
                    "workspace_nome": ws.get("name", ""),
                    "usuario": identificador,
                    "nivel_acesso": usuario.get("groupUserAccessRight", "Desconhecido"),
                    "acesso_externo": bool(dominio) and dominio != dominio_organizacao.lower(),
                }
            )

    return pd.DataFrame(linhas, columns=COLUNAS)


def resumo_por_nivel_acesso(relatorio: pd.DataFrame) -> pd.DataFrame:
    """Conta quantos usuários existem por nível de acesso — visão rápida para gestão."""
    return (
        relatorio.groupby("nivel_acesso")
        .size()
        .reset_index(name="total_usuarios")
        .sort_values("total_usuarios", ascending=False)
    )
