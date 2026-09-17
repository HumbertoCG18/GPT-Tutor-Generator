# Dossiê de triagem — sujeira ES2-Tutor (46) / IA-Tutor (48)

data: 2026-08-06 · coleta READ-ONLY (git status/diff/show + stat + manifest JSON-diff; zero
escrita nos repos). Item 4 da ordem aprovada; destrava rollouts ES2/IA.

## VEREDITO CENTRAL

**Não é lixo de build.** Os dois worktrees carregam **sessões de trabalho válidas nunca
commitadas** (import de material + poda + reprocess). `git checkout -- .` / `git clean -fd`
destruiria conteúdo real do tutor. A ação certa é COMMITAR (com exclusão dos backups), não
limpar.

## ES2-Tutor (HEAD `abc8ee2`, 46 dirty)

Uma única história em 3 camadas de mtime:

| camada | o quê | classificação |
|---|---|---|
| **01/07 (42 arquivos)** | Sessão de import+reprocess: manifest 25→**35 entries** (+10: `azure`, `devops`, `kubernetes`, `microsservicos`, `microsservicos4`, `roteiro3-gateway`, `roteiro4`, `revisao-p2`, `revisao-p1-respostas`, `revisao-p2-respostas`); 6 curated .md novos (12-85KB) **TODOS referenciados no manifest** (`approved_markdown`); backfill Moodle S0 nos 25 antigos (`posting_date`/`moodle_label` — 25 entries); regeneração completa (índices, CRONOGRAMA_*, code/professor churn +3/-3) | **CONTEÚDO VÁLIDO — commitar** |
| **04/08 20:11 (2)** | `manifest.json` (+2824/-768 formatação/migração; 1 `manual_timeline_block_id` migrado p/ uuid) + `.block_identity.json` (+14/-14 `last_seen`) — assinatura do write-trap do `retag()` (audit Task 8 rodou com `persist=True`; trap fechado depois no T19) | inócuo, vai junto no commit |
| **backups (3)** | `manifest.json.bak` (01/07, pré-write da própria sessão), `manifest.json.apibak` (18/06), `course/.timeline_index.json.bak` (02/06) | **NÃO commitar** — apagar ou gitignorar (padrão T19 `*.bak`) |

Risco de NÃO commitar: os 10 materiais (Azure/DevOps/K8s/microsserviços/roteiros/revisões
de prova) existem só neste worktree — qualquer rollback/clean futuro os perde de vez.

## IA-Tutor (HEAD `33e2477`, 48 dirty)

Quatro sessões empilhadas, nunca commitadas:

| camada | o quê | classificação |
|---|---|---|
| **23/06 (8)** | **PODA EXECUTADA em worktree**: manifest 50→62 no líquido, mas com **−14 entries removidas** (os 13 stale byte-dup catalogados + `como-analisar-resultados-sse-comcorrecoes`); 2 curated .md tracked DELETADOS (`artigo-usando-agrupamento`, `aula-29-...medidas-de-avaliacao`, ~26KB cada); +4 novos (curated `introducao-a-agentes` REFERENCIADO, 3 exams past-exams, 1 lista respondida); 2 manifest .bak pré/pós-poda | poda planejada (pendência "IA: poda de 13 stale") — **confirmar e commitar** |
| **25/06 (23)** | Import dos notebooks: **21 `code/professor/*.md`** (k-NN, MLP, perceptron, árvores, agrupamento — o stash `.ipynb` catalogado) + `code_curation.json` +833 linhas; manifest +26 entries no total da pilha | **CONTEÚDO VÁLIDO — commitar** |
| **01/07 (13)** | Reprocess/regeneração (manifest M grande, índices, CRONOGRAMA_*, FILE_MAP) | vai junto |
| **04/08 (1)** | `.block_identity.json` `last_seen` (mesmo write-trap do audit) | inócuo |
| **backups (4)** | `manifest.json.bak`, `.prepoda-55...bak` (979KB), `.postpoda-42...bak` (630KB), `.before-pinfix...bak` (688KB) | **NÃO commitar** — padrão T19 |

### Ponto de atenção único (IA): `aula-29`

A pendência (as-of mundo-63) dizia "aula-29 é órfão byte-único — tratar à parte, NÃO podar",
mas a poda de 23/06 removeu a entry e deletou o curated. **Mitigação verificada**: o gêmeo de
versão `como-analisar-resultados-acc-pr-re-e-f1` NÃO está na lista de removidos — o conteúdo
sobrevive pelo par (foi a variante `sse-comcorrecoes` que caiu). Consequências se confirmar:
gold IA tem rows keyed no id antigo (remap old→live, mesmo protocolo dos 13) e o caso-vivo
"IA-aula-29 fallback-sem-cobertura" da pendência de calibração perde o exemplar — citar o
gêmeo. Se NÃO confirmar: restaurar só esses 2 curated + entries é cirúrgico (`git checkout --
<paths>` + revert das rows do manifest).

## DECISÕES PEDIDAS (3)

1. **ES2**: commitar o estado 01/07 como está (10 materiais entram oficialmente)? Backups:
   apagar ou gitignorar?
2. **IA**: confirmar a poda de 14 (incluindo aula-29-via-gêmeo) e commitar a pilha
   23/06→01/07? Backups idem?
3. Pós-commit dos dois: worktrees limpos ⇒ pré-requisito "inspeção da sujeira" morre, e os
   rollouts ES2/IA passam a depender só de: gold/medição pré-flip (ES2), swap da flag legada
   (IA) e da campanha de unificação (geradores de índice — decidir se bloqueia ES2/IA ou só
   TCC, já que ES2/IA nunca tiveram rebuild cirúrgico e portanto não têm o conflito
   reprocess-vs-rebuild instalado).

Nota de rito pós-decisão: commit de cada repo-tutor precedido de `audit_gold_freshness`
(hoje: ES2 hard=0, IA hard=0 ✓) e seguido de re-run do audit; suite do projeto não é gate
aqui (repos-tutor são dados, não código).
