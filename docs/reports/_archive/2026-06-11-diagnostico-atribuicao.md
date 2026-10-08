# Diagnóstico completo — Sistema de atribuição (unidade × bloco × subunidade)

date: 2026-06-11
método: 4 investigações paralelas (scorer de bloco; matchers unit/subunit + timeline index; sinais upstream; avaliação empírica no repo real Metodos-Formais-Tutor) + verificação cruzada.
gatilho: LogicaDeHoare.pdf → bloco-13 (esperado bloco-10, 27/04–04/05, tópico "logica hoare"), com confiança 1.0 "alta".

## 1. Números (repo real, 49 entries de material avaliadas)

| Métrica | Valor |
|---|---|
| Erros aparentes de bloco | **8/49 (16.3%)** |
| Erro nas entries SEM `source_section` | **8/27 (29.6%)** |
| Erro nas entries COM `source_section` | **0/22 (0%)** |
| Erros com confiança 1.0 "alta" | **7 de 8** |
| Distribuição de confiança (54 entries) | 46× conf=1.0 · 6× 0.85 · 1× 0.95 · 1× 0.244 |
| Acurácia do scorer puro SEM gabarito (re-execução) | **59.2% (29/49)**, 19 confiante-e-errado |

Erros confirmados (todos sem seção): logicadehoare→13 (esp. 10), logicadehoare2→11 (esp. 10),
provas.thy→05 (esp. 06), exemplos.thy→06 (esp. 04), intro.thy→12 (esp. 04, Isabelle≠Dafny),
exercicios_conjuntos.zip→03 (esp. 11), classes_parte1.zip→03 (esp. 15), exerciciosdafny1→15 (esp. 12/13).

## 2. Causa raiz nº1 — a seção Moodle se perde no caminho (o gabarito nunca dispara)

- O stash Moodle É organizado por seção (`...\metodos-formais-para-computacao\Revisão - Lógica e Especificação\...`).
- `scan_stash_cards` extrai `card_name` = 1ª subpasta → `source_section` (stash_import.py:106). Funciona para import via stash.
- MAS: arquivos importados por outros caminhos (raw/pdfs por categoria, import direto, raiz do stash) ficam com `source_section=""`.
- Backfills existem (moodle.py:344 via API; m365.py:301; scripts/backfill_source_section.py) mas são **manuais/condicionais** — nunca rodaram para os 4 PDFs errados.
- `_card_scoped_block` (content_taxonomy.py:845): `if not card: return "", 0.0` → **gabarito (.card_block_map.json) nunca consultado** → cai no scorer léxico.
- Correlação observada: **100% dos erros = source_section vazio**. O gabarito + seção é o que segura a precisão hoje.

## 3. Causa raiz nº2 — o scorer léxico é fraco e confiante

Fórmula (score_entry_against_timeline_block, file_map.py:816-888): ~12 termos somados sem clamp
(anchor row ×1.15 + suporte 0.18/linha + bônus exercício + boost unidade ±0.45/+0.6 + boost tópico
−0.18/+1.15 + topic_text 0.35/0.12/0.05 + card ≤0.45 + data 0.30/0.10 + sequência 0.20).

Fraquezas confirmadas:
- **Overlap absoluto de tokens** (score_text_against_row, entry_signals.py:12-26): exato=1.0, substring=0.45, prefixo5=0.2. Sem TF-IDF/raridade: "logica" (presente em N blocos) vale o mesmo que "hoare" (1 bloco). Tokens genéricos dominam.
- **Sem noção de ferramenta**: intro.thy (Isabelle) → bloco "introducao dafny"; padrão repetido nos .thy/.zip.
- **Título CamelCase não tokeniza**: "LogicaDeHoare" normaliza para UM token "logicadehoare" → só substring 0.45 com "logica"/"hoare"; perde o match exato de frase.
- **Hipótese "tópico curto perde pro verboso" REFUTADA** na fórmula por-token (comparação é simétrica por token da entry), mas o topic_text concatenado dos blocos verbosos (timeline/index.py:569, `" ".join(topic_tokens)`) amplia a superfície de matching: qualquer entry que cite 1 dos 8 conceitos tem overlap.
- **Confiança não-calibrada**: margin_confidence = (best−runner)+best·0.18, clamp [0,1]. Com scores ~4-8, a margem estoura o clamp → quase tudo vira 1.0. Conf 1.0 não significa nada no topo da escala. (O caso "confiante-e-errado" é estrutural, não acidente.)
- Sinal de data quase nunca dispara: o Moodle API não expõe data de publicação (não capturada); datas só de texto do material.

## 4. Bugs pontuais encontrados (verificar/corrigir)

| # | Bug | Onde | Efeito |
|---|---|---|---|
| B1 | Categoria `references` (EN) fura `_NO_TIMELINE_CATEGORIES` (PT: cronograma/bibliografia/referencias) | content_taxonomy.py:961 | referência bibliográfica ganhou bloco-06 conf 1.0 |
| B2 | Card bonus possivelmente somado 2× (dentro de score_timeline_block:795 e de novo em :874) | file_map.py | inflação de score quando há card evidence |
| B3 | `eval_assignments.py` colapsa com índice persistido (espera `rows`; índice tem `sessions`/`source_rows`) | file_map.py:1108 + script | harness de avaliação inutilizável sobre repo real (49/49 "erradas" espúrias) |
| B4 | Entry `formalizacaoalgoritmos-recursao`: computed_unit=u02 + bloco-04 (u01) | manifest real | atribuição incoerente (pré-F1 ou caso de conflito a re-verificar pós-retag) |
| B5 | ids duplicados no manifest (`t1-2026-1`, `introducao` em 2 categorias) | manifest real | colisão de id → code_curation/rationale cruzados |

## 5. O que JÁ funciona (não mexer)

- Gabarito card_block_map quando `source_section` chega: 0 erros em 22.
- review_list_block_for_entry (revisão→prova, 0.95): correto nos casos vistos.
- F1 (reconciliar unit×bloco): herança/reconciliação funcionando nos reasons do manifest real.
- Estrutura do timeline_index (blocos, períodos, kinds) fiel ao cronograma.

## 6. Plano de ataque proposto (ordem de alavancagem)

| Prioridade | Frente | Ganho esperado | Esforço |
|---|---|---|---|
| **P1** | **Propagação automática da seção**: garantir `source_section` em todo caminho de import (stash/raw/moodle), backfill automático no build (não script manual), aviso visível quando vazio | Elimina a classe inteira de erros observada (29.6%→~0 nos com gabarito) | médio |
| **P2** | **Scorer: raridade + ferramenta + CamelCase**: ponderar token por raridade entre blocos (IDF simples), detectar ferramenta (.thy=Isabelle, .dfy/dafny=Dafny) como boost/penalidade, tokenizar CamelCase no título | Sobe o piso do scorer puro (59%→) para os casos sem gabarito | médio-alto |
| **P3** | **Calibrar confiança**: normalizar scores antes da margem (ex.: margem relativa best/runner) para conf 1.0 voltar a significar algo; bands voltam a ser sinal de revisão útil | Confiança honesta; triagem de revisão funciona | baixo-médio |
| **P4** | **Bugs B1-B5** | corrige furos pontuais | baixo |

P1 ataca a causa dominante comprovada pelos dados; P2/P3 tornam o fallback digno de confiança; P4 é higiene.
