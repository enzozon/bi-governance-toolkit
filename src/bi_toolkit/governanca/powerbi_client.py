"""Cliente fino para a Power BI REST API (endpoints administrativos).

Autentica via client credentials (service principal) usando MSAL e expõe
apenas as chamadas necessárias para auditoria de workspaces e acessos —
não é um SDK completo, é o recorte que este toolkit de governança usa.

Referência oficial: https://learn.microsoft.com/rest/api/power-bi/admin
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import msal
import requests

AUTHORITY_TEMPLATE = "https://login.microsoftonline.com/{tenant_id}"
SCOPE = ["https://analysis.windows.net/powerbi/api/.default"]
API_BASE = "https://api.powerbi.com/v1.0/myorg"


@dataclass
class PowerBICredenciais:
    tenant_id: str
    client_id: str
    client_secret: str

    @classmethod
    def do_ambiente(cls) -> "PowerBICredenciais":
        """Lê as credenciais de variáveis de ambiente (ver .env.example)."""
        return cls(
            tenant_id=os.environ["POWERBI_TENANT_ID"],
            client_id=os.environ["POWERBI_CLIENT_ID"],
            client_secret=os.environ["POWERBI_CLIENT_SECRET"],
        )


class PowerBIClient:
    """Wrapper de leitura sobre os endpoints admin da Power BI REST API."""

    def __init__(self, credenciais: PowerBICredenciais, sessao: requests.Session | None = None):
        self._credenciais = credenciais
        self._sessao = sessao or requests.Session()
        self._app = msal.ConfidentialClientApplication(
            client_id=credenciais.client_id,
            client_credential=credenciais.client_secret,
            authority=AUTHORITY_TEMPLATE.format(tenant_id=credenciais.tenant_id),
            validate_authority=False,
        )

    def _token(self) -> str:
        resultado = self._app.acquire_token_for_client(scopes=SCOPE)
        if "access_token" not in resultado:
            erro = resultado.get("error_description", resultado.get("error", "erro desconhecido"))
            raise RuntimeError(f"Falha ao autenticar na Power BI API: {erro}")
        return resultado["access_token"]

    def _get(self, caminho: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        resposta = self._sessao.get(
            f"{API_BASE}{caminho}",
            headers={"Authorization": f"Bearer {self._token()}"},
            params=params,
            timeout=30,
        )
        resposta.raise_for_status()
        return resposta.json()

    def listar_workspaces(self) -> list[dict[str, Any]]:
        """Lista todos os workspaces (grupos) do tenant via endpoint admin."""
        return self._get("/admin/groups", params={"$top": 5000}).get("value", [])

    def listar_usuarios_workspace(self, workspace_id: str) -> list[dict[str, Any]]:
        """Lista os usuários (e nível de acesso) de um workspace específico."""
        return self._get(f"/admin/groups/{workspace_id}/users").get("value", [])

    def listar_relatorios_workspace(self, workspace_id: str) -> list[dict[str, Any]]:
        return self._get(f"/admin/groups/{workspace_id}/reports").get("value", [])

    def listar_datasets_workspace(self, workspace_id: str) -> list[dict[str, Any]]:
        return self._get(f"/admin/groups/{workspace_id}/datasets").get("value", [])
