"""Auditoria de governança de workspaces do Power BI Service.

Aplica um conjunto de regras simples (nomenclatura, presença de admin,
uso de "My Workspace" pessoal para conteúdo compartilhado) e devolve uma
lista de achados para o time de dados agir — o mesmo tipo de checagem que
uma pessoa analista faria manualmente workspace por workspace.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from bi_toolkit.governanca.powerbi_client import PowerBIClient

PADRAO_NOME_WORKSPACE = re.compile(
    r"^BI - (Comercial|Financeiro|Operações|TI|Estoque|RH|Diretoria) - .+$"
)

SEVERIDADE_ALTA = "ALTA"
SEVERIDADE_MEDIA = "MÉDIA"
SEVERIDADE_BAIXA = "BAIXA"


@dataclass
class AchadoAuditoria:
    workspace_id: str
    workspace_nome: str
    regra: str
    severidade: str
    descricao: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "workspace_id": self.workspace_id,
            "workspace_nome": self.workspace_nome,
            "regra": self.regra,
            "severidade": self.severidade,
            "descricao": self.descricao,
        }


def _checar_nomenclatura(ws: dict[str, Any]) -> AchadoAuditoria | None:
    nome = ws.get("name", "")
    if not PADRAO_NOME_WORKSPACE.match(nome):
        return AchadoAuditoria(
            workspace_id=ws["id"],
            workspace_nome=nome,
            regra="nomenclatura",
            severidade=SEVERIDADE_BAIXA,
            descricao=(
                "Nome fora do padrão 'BI - <Área> - <Descrição>'. "
                "Veja docs/nomenclatura.md."
            ),
        )
    return None


def _checar_workspace_pessoal(ws: dict[str, Any]) -> AchadoAuditoria | None:
    if ws.get("type") == "PersonalGroup":
        return AchadoAuditoria(
            workspace_id=ws["id"],
            workspace_nome=ws.get("name", ""),
            regra="workspace_pessoal",
            severidade=SEVERIDADE_ALTA,
            descricao=(
                "Conteúdo publicado em 'My Workspace' pessoal — sem "
                "controle de acesso em equipe. Migrar para workspace dedicado."
            ),
        )
    return None


def _checar_capacidade_dedicada(ws: dict[str, Any]) -> AchadoAuditoria | None:
    if not ws.get("isOnDedicatedCapacity", False):
        return AchadoAuditoria(
            workspace_id=ws["id"],
            workspace_nome=ws.get("name", ""),
            regra="capacidade_compartilhada",
            severidade=SEVERIDADE_BAIXA,
            descricao="Workspace roda em capacidade compartilhada (sem Premium/Fabric dedicado).",
        )
    return None


def _checar_admins(ws: dict[str, Any], usuarios: list[dict[str, Any]]) -> AchadoAuditoria | None:
    admins = [u for u in usuarios if u.get("groupUserAccessRight") == "Admin"]
    if len(admins) == 0:
        return AchadoAuditoria(
            workspace_id=ws["id"],
            workspace_nome=ws.get("name", ""),
            regra="sem_admin",
            severidade=SEVERIDADE_ALTA,
            descricao="Workspace sem nenhum usuário com papel Admin.",
        )
    return None


def auditar_workspace(
    ws: dict[str, Any], usuarios: list[dict[str, Any]]
) -> list[AchadoAuditoria]:
    checagens = [
        _checar_nomenclatura(ws),
        _checar_workspace_pessoal(ws),
        _checar_capacidade_dedicada(ws),
        _checar_admins(ws, usuarios),
    ]
    return [achado for achado in checagens if achado is not None]


def auditar_workspaces(client: PowerBIClient) -> list[AchadoAuditoria]:
    """Percorre todos os workspaces do tenant e roda as checagens de governança."""
    achados: list[AchadoAuditoria] = []
    for ws in client.listar_workspaces():
        usuarios = client.listar_usuarios_workspace(ws["id"])
        achados.extend(auditar_workspace(ws, usuarios))
    return achados
