import responses

from bi_toolkit.governanca.auditoria_workspaces import auditar_workspace, auditar_workspaces
from bi_toolkit.governanca.powerbi_client import (
    API_BASE,
    PowerBIClient,
    PowerBICredenciais,
)
from bi_toolkit.governanca.relatorio_acessos import (
    gerar_relatorio_acessos,
    resumo_por_nivel_acesso,
)

WORKSPACE_CONFORME = {
    "id": "ws-1",
    "name": "BI - Comercial - Vendas Postos",
    "type": "Workspace",
    "isOnDedicatedCapacity": True,
}

WORKSPACE_FORA_DO_PADRAO = {
    "id": "ws-2",
    "name": "Relatorios do Joao",
    "type": "Workspace",
    "isOnDedicatedCapacity": False,
}

WORKSPACE_PESSOAL = {
    "id": "ws-3",
    "name": "My Workspace",
    "type": "PersonalGroup",
    "isOnDedicatedCapacity": False,
}

USUARIO_ADMIN = {"emailAddress": "ana@empresa.com", "groupUserAccessRight": "Admin"}
USUARIO_VIEWER = {"emailAddress": "convidado@fornecedor.com", "groupUserAccessRight": "Viewer"}


class FakePowerBIClient:
    """Dublê de teste: mesma interface pública do PowerBIClient, sem rede."""

    def __init__(self, workspaces, usuarios_por_workspace):
        self._workspaces = workspaces
        self._usuarios_por_workspace = usuarios_por_workspace

    def listar_workspaces(self):
        return self._workspaces

    def listar_usuarios_workspace(self, workspace_id):
        return self._usuarios_por_workspace.get(workspace_id, [])


def test_workspace_conforme_com_admin_nao_gera_achados():
    achados = auditar_workspace(WORKSPACE_CONFORME, [USUARIO_ADMIN])
    assert achados == []


def test_workspace_fora_do_padrao_gera_achado_de_nomenclatura():
    achados = auditar_workspace(WORKSPACE_FORA_DO_PADRAO, [USUARIO_ADMIN])
    regras = {a.regra for a in achados}
    assert "nomenclatura" in regras
    assert "capacidade_compartilhada" in regras


def test_workspace_pessoal_gera_achado_de_alta_severidade():
    achados = auditar_workspace(WORKSPACE_PESSOAL, [])
    achado_pessoal = next(a for a in achados if a.regra == "workspace_pessoal")
    assert achado_pessoal.severidade == "ALTA"


def test_workspace_sem_admin_e_sinalizado():
    achados = auditar_workspace(WORKSPACE_CONFORME, [USUARIO_VIEWER])
    regras = {a.regra for a in achados}
    assert "sem_admin" in regras


def test_auditar_workspaces_percorre_todos_os_workspaces_do_client():
    client = FakePowerBIClient(
        workspaces=[WORKSPACE_CONFORME, WORKSPACE_FORA_DO_PADRAO],
        usuarios_por_workspace={"ws-1": [USUARIO_ADMIN], "ws-2": [USUARIO_ADMIN]},
    )
    achados = auditar_workspaces(client)
    assert any(a.workspace_id == "ws-2" and a.regra == "nomenclatura" for a in achados)


def test_relatorio_acessos_sinaliza_dominio_externo():
    client = FakePowerBIClient(
        workspaces=[WORKSPACE_CONFORME],
        usuarios_por_workspace={"ws-1": [USUARIO_ADMIN, USUARIO_VIEWER]},
    )
    relatorio = gerar_relatorio_acessos(client, dominio_organizacao="empresa.com")

    linha_externa = relatorio[relatorio["usuario"] == "convidado@fornecedor.com"].iloc[0]
    linha_interna = relatorio[relatorio["usuario"] == "ana@empresa.com"].iloc[0]

    assert bool(linha_externa["acesso_externo"]) is True
    assert bool(linha_interna["acesso_externo"]) is False


def test_resumo_por_nivel_acesso_agrega_contagens():
    client = FakePowerBIClient(
        workspaces=[WORKSPACE_CONFORME],
        usuarios_por_workspace={"ws-1": [USUARIO_ADMIN, USUARIO_VIEWER]},
    )
    relatorio = gerar_relatorio_acessos(client, dominio_organizacao="empresa.com")
    resumo = resumo_por_nivel_acesso(relatorio)

    assert set(resumo["nivel_acesso"]) == {"Admin", "Viewer"}
    assert resumo["total_usuarios"].sum() == 2


@responses.activate
def test_powerbi_client_listar_workspaces_via_http_mockado():
    responses.add(
        responses.GET,
        "https://login.microsoftonline.com/tenant-fake/v2.0/.well-known/openid-configuration",
        json={
            "token_endpoint": "https://login.microsoftonline.com/tenant-fake/oauth2/v2.0/token",
            "issuer": "https://login.microsoftonline.com/tenant-fake/v2.0",
            "authorization_endpoint": "https://login.microsoftonline.com/tenant-fake/oauth2/v2.0/authorize",
        },
        status=200,
    )
    responses.add(
        responses.POST,
        "https://login.microsoftonline.com/tenant-fake/oauth2/v2.0/token",
        json={"access_token": "token-fake", "token_type": "Bearer", "expires_in": 3600},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{API_BASE}/admin/groups",
        json={"value": [WORKSPACE_CONFORME]},
        status=200,
    )

    credenciais = PowerBICredenciais(
        tenant_id="tenant-fake", client_id="client-fake", client_secret="segredo-fake"
    )
    client = PowerBIClient(credenciais)

    workspaces = client.listar_workspaces()

    assert workspaces == [WORKSPACE_CONFORME]
