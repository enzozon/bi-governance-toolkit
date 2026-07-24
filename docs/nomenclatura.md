# Padrões de nomenclatura — Power BI Service

Convenções aplicadas (e checadas automaticamente por
`src/bi_toolkit/governanca/auditoria_workspaces.py`) para manter o ambiente
navegável à medida que o número de workspaces/relatórios cresce.

## Workspaces

```
BI - <Área> - <Descrição curta>
```

- **Área**: uma de `Comercial`, `Financeiro`, `Operações`, `TI`, `Estoque`, `RH`, `Diretoria`.
- **Descrição curta**: em poucas palavras, sem abreviações ambíguas.

Exemplos válidos: `BI - Comercial - Vendas Postos`, `BI - Financeiro - Fechamento Mensal`.
Exemplos inválidos: `Relatorios do João` (sem área, nome pessoal), `BI-Vendas` (sem separador nem área da lista).

Workspaces pessoais (`My Workspace`) **não devem hospedar relatórios usados por mais de uma pessoa** — ver `docs/governanca.md`.

## Datasets e dataflows

```
DS - <Área> - <Fonte de dados>
```

Exemplo: `DS - Comercial - Vendas Postos (SQLite)`.

## Relatórios (.pbix)

```
RPT - <Área> - <Público-alvo> - <Assunto>
```

Exemplo: `RPT - Comercial - Diretoria - Vendas Mensais`.

## Medidas DAX

- `PascalCase` com espaços, em português, sem prefixo de tabela: `Total de Vendas`, não `fato_vendas Total de Vendas`.
- Medidas de apoio/intermediárias usadas só dentro de outras medidas recebem prefixo `_` e ficam ocultas no modelo: `_Vendas Ano Anterior`.
- Uma pasta de medidas (`Display Folder`) por assunto: `Vendas`, `Margem`, `Governança`.

## Colunas e tabelas no modelo

- Nomes de tabela e coluna em português, sem acentuação problemática para DAX quando possível, seguindo o que já vem de `sql/schema.sql` (`fato_vendas`, `dim_posto`, etc.) — evita renomear na importação e manter dois nomes mentais para a mesma coisa.
