# Backlog de Melhorias — branch new-features

last_updated: 2026-06-04

Itens propostos durante o thread de precisão de atribuição (jun/2026). Cada um tem
contexto suficiente pra retomar sem reabrir a discussão. Ordem = prioridade sugerida.

## Estado atual

**Entregue nesta branch:**
- **#1 Harness de avaliação** — `scripts/eval_assignments.py` + gate `tests/test_eval_assignments.py`. Mede acurácia arquivo→bloco pelo scorer real contra gold set.
- **#2 Sinal de sequência** — `src/builder/routing/sequence.py`. "Aula 03" → boost +0.20 no 3º bloco `kind=class`. Só marcadores `aula`/`encontro`.

**Em implementação:**
- **Referências como contexto do tutor** — spec aprovado em `docs/superpowers/specs/2026-06-04-referencias-contexto-tutor-design.md`. (Próximo: plano + execução.)

---

## Parados — retomar após a spec de referências

### #3 — Decay de distância de data + fix de virada de ano
**Status:** desenhado, NÃO implementado. Valor medido ≈ 0 nos dados reais.
**Resumo:** trocar o boost binário de data (`_score_block_date_match`, `file_map.py`) por decay linear: in-range = 0.30; fora = `0.10 * (1 − dist/30)`, clamp 0, `max` sobre as datas do material. Distância real em dias mata o bug `start.month <= dt.month <= end.month` (quebra na virada de ano). Virada de ano vira **propriedade de segurança** (data com ano errado → distância enorme → 0, nunca boost espúrio), não feature.
**Por que parou:** investigação nos 5 repos reais mostrou ~98% dos materiais já em band "alta", 1 media + 1 baixa em ~127. O decay ataca a faixa media/baixa (vão entre blocos), que quase não existe. Reabrir só se aparecer reposição/data-fora-da-grade que erre.
**Calibração já decidida:** linear, horizonte 30 dias (vão semanal cabe folgado).

### #4 — Piso de winner absoluto na confidence band
**Status:** proposto, não desenhado em detalhe.
**Resumo:** `confidence_band` (thresholds.py) deriva a faixa só da margem (`margin_confidence`). Dois "média" podem ter qualidade diferente. Misturar a magnitude absoluta do winner na band força revisão de matches fracos-mas-não-ambíguos.
**Por que parou:** baixa prioridade — dados reais quase todos "alta".

### Horário (cadência de aula) — processar o field do gerenciador
**Status:** investigado, valor real menor que o esperado.
**Resumo:** `SubjectProfile.schedule` ("Seg/Qua 10:15-11:55", `core.py:160`) é só texto de exibição (prompts + README), nunca parseado. Parsear → dias de aula destravaria: validar datas extraídas, horizonte adaptativo pro #3, distinguir aula vs reposição.
**Por que parou:** a killer-app (gerar a sequência canônica de datas) está **bloqueada por dados** — não há calendário acadêmico estruturado (feriados só vêm do texto do cronograma; `semester` é string livre) — **e é redundante**: o cronograma já carrega as datas reais das aulas. Ganho restante é modesto. Campo `schedule` está vazio em todos os 5 repos reais.

### Conserto do clone completo de repo GitHub
**Status:** bug confirmado nos dados reais. Contornado pela spec de referências.
**Resumo:** `process_github_repo` (`source_importers.py:235`) força branch `main` → repos com default `master`/outro falham (`Remote branch main not found`). Repos grandes falham no checkout por long-path do Windows (`Filename too long`). Resultado: 8/8 referências com `extracted_files=0`. (Mesmo `main` hardcoded em `prompts.py:484`.)
**Por que parou:** a spec de referências usa README-fetch (API GitHub, sem clone), que contorna. Clone completo só importa pra **análise de código de verdade** (não contexto de referência). Vira issue quando precisar disso.
**Fix esperado:** detectar branch default (não hardcode); `git config core.longpaths true` ou clone shallow/sparse.

### Token GitHub (rate limit)
**Status:** follow-up da spec de referências.
**Resumo:** API anônima do GitHub = 60 req/h por IP. v1 vai sem token (cache por hash protege, volume normal por matéria é baixo). Adicionar token opcional (config) sobe pra 5.000/h — necessário só se processar muitas matérias em lote.

### Referências — Approach C (injeção no contexto do tutor)
**Status:** extensão futura da spec atual.
**Resumo:** além da `BIBLIOGRAPHY.md`, fiar as referências no contexto de unidade/tópico que o tutor carrega, pra a referência aparecer sozinha quando o aluno está naquele tópico. Mais ambicioso, mais arquivos. Depois do v1 (que só surfacea + mapeia).

### Medição de correção com ground-truth
**Status:** proposto como forma de validar se mais precisão vale a pena.
**Resumo:** band = confiança, não correção verificada. "alta" pode estar confiante e errado. Rotular ground-truth de 1 repo real (ex.: IA) e rodar o harness contra ele mediria correção de fato, não só confiança. Diz se há trabalho de precisão que ainda valha.
