# Runbook de administração

Procedimentos operacionais do dia a dia do suporte Power BI, no formato que
um analista júnior consultaria antes de agir.

## 1. Onboarding de um novo usuário num workspace

1. Confirmar a área e o papel necessário (ver tabela de papéis em `docs/governanca.md`).
2. No Power BI Service: `Workspace > Acesso > Adicionar pessoas`, selecionar o papel mínimo suficiente (evitar dar Admin por padrão).
3. Registrar a concessão (data, quem pediu, quem aprovou) — se o time usa um ticket/planilha de controle, referenciar o número aqui.
4. Na próxima auditoria trimestral (`docs/governanca.md`), confirmar que o acesso ainda é necessário.

## 2. Publicar um novo relatório

1. Desenvolver no Dev workspace, seguindo `docs/nomenclatura.md`.
2. Validar em Homologação com pelo menos uma pessoa da área de negócio.
3. Rodar o checklist de promoção para Produção (`docs/governanca.md`).
4. Publicar no workspace de Produção correspondente e comunicar o público-alvo.

## 3. Solicitação de novo workspace

1. Verificar se já existe um workspace da mesma área que atenda a necessidade (evitar duplicidade).
2. Criar seguindo o padrão `BI - <Área> - <Descrição>`.
3. Definir pelo menos dois Admins.
4. Rodar a auditoria (`auditoria_workspaces.py`) depois da criação para confirmar que passa em todas as regras.

## 4. Rodar a auditoria de governança

```bash
python -c "
from bi_toolkit.governanca.powerbi_client import PowerBIClient, PowerBICredenciais
from bi_toolkit.governanca.auditoria_workspaces import auditar_workspaces

client = PowerBIClient(PowerBICredenciais.do_ambiente())
for achado in auditar_workspaces(client):
    print(achado.severidade, achado.workspace_nome, achado.regra, achado.descricao)
"
```

Requer as variáveis de ambiente em `.env` (ver `.env.example`) apontando
para um App Registration com permissão de leitura na Power BI Admin API
(`Tenant.Read.All` ou superior, consentida por um Global Admin).

## 5. Gerar o relatório de acessos

Mesma ideia, usando `bi_toolkit.governanca.relatorio_acessos.gerar_relatorio_acessos(client, dominio_organizacao="suaempresa.com")` — retorna um DataFrame que pode ser exportado com `.to_csv(...)` para compartilhar com gestão.

## 6. Rotacionar o client secret do App Registration

1. No Azure AD, gerar um novo secret com validade definida (nunca "nunca expira").
2. Atualizar `POWERBI_CLIENT_SECRET` no cofre de segredos usado em produção (nunca no `.env` versionado).
3. Validar que a auditoria (passo 4) ainda autentica com o novo secret.
4. Revogar o secret antigo só depois da validação.

## 7. Gerar os dados de exemplo localmente

```bash
python -m bi_toolkit.etl.carregar
streamlit run src/bi_toolkit/dashboard/app.py
```
