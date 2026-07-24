# Governança do ambiente Power BI

Política de referência para administração do Power BI Service — o que este
toolkit automatiza em `src/bi_toolkit/governanca/` é a aplicação prática
destas regras.

## Camadas de workspace

| Camada | Uso | Quem publica |
|---|---|---|
| **Dev** | Desenvolvimento de relatórios novos, dados de teste | Qualquer pessoa do time de dados |
| **Homologação** | Validação com stakeholders antes de ir para produção | Pessoa responsável pelo relatório |
| **Produção** | Relatórios em uso corporativo, com SLA de disponibilidade | Somente após aprovação (ver checklist abaixo) |

`My Workspace` (pessoal) é só para rascunho individual — nunca para
conteúdo consumido por outra pessoa. É a primeira coisa que
`auditoria_workspaces.py` sinaliza (regra `workspace_pessoal`, severidade ALTA).

## Papéis de acesso

| Papel | Pode | Quando usar |
|---|---|---|
| **Admin** | Gerenciar workspace, adicionar/remover pessoas, deletar conteúdo | Só quem é dono do workspace (mínimo 2 por workspace, para cobrir férias/saída) |
| **Member** | Publicar e editar relatórios/datasets | Time de dados responsável pelo conteúdo |
| **Contributor** | Editar sem poder compartilhar para fora do workspace | Colaboradores pontuais |
| **Viewer** | Só consumir relatórios já publicados | Consumidores finais (área de negócio) |

Todo workspace precisa de **pelo menos um Admin** — checado automaticamente (regra `sem_admin`).

## Checklist antes de promover um relatório para Produção

1. Dataset usa nomes de tabela/coluna e medidas seguindo `docs/nomenclatura.md`.
2. Fonte de dados documentada (origem, dono, frequência de atualização).
3. Sem credenciais hardcoded no dataset — usar gateway/credencial gerenciada.
4. Pelo menos duas pessoas revisaram os números antes da publicação.
5. Workspace de destino está na camada Produção, com capacidade adequada.

## Revisão periódica

- **Mensal**: rodar `python -m bi_toolkit.governanca.auditoria_workspaces` (ou o script equivalente) e tratar os achados de severidade ALTA em até 5 dias úteis.
- **Trimestral**: revisar `relatorio_acessos.py` procurando usuários com acesso que não usam mais (saíram da empresa, trocaram de área) e domínios externos inesperados (`acesso_externo = True`).

## Acesso externo

Compartilhamento com domínios fora da organização exige aprovação explícita
do Admin do workspace e é sempre registrado — é o que a coluna
`acesso_externo` do relatório de acessos sinaliza para revisão.
