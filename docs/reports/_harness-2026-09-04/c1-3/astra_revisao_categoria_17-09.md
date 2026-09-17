# Revisão Astra do diff: prova matemática não é avaliação (17/09, read-only)

session id: 01a0b080-b95b-7571-9e90-6d06ee10955c | codex exec --profile astra --sandbox read-only | 14:53:40→14:58:01 | rc=0 | árvore inalterada pela chamada.

Brief: scratchpad/brief-astra-categoria.md (não versionado; diff de src/utils/helpers.py + tests/test_core.py inline, patch sha256 3cb6f330…; script de replay inline). Mensagem final consumida via -o.

Consumo pelo Fable (todos verificados na fonte antes de aplicar):

- 1 BLOQUEIA: reproduzido — "Exames - ProvasIndutivas.pdf" e "Prova final - ProvasIndutivas.pdf": HEAD `provas`, patch revisado `material-de-aula`. Causa: porte literal de `candidate()` exigia palavra inteira em `exame`/`prova N`. Correção: em vez de lista de marcadores, remove o tema matemático do nome e reaplica as mesmas cues do ramo (`prova`, `exame`, `_wb test/p1/p2/p3/av1/av2`, mais `avaliac`) ao resíduo; sobrou marcador → `provas`. Fecha a classe, não só as 2 sondas. Sondas de teste ampliadas: prefixos "Exames - " e "Prova final - " sobre os 3 MF, "Exame final - Provas por indução.pdf", "Avaliação 1 - ProvasIndutivas.pdf".
- 2 AJUSTE (ZIP no diálogo): reproduzido — `dialogs.py:3623` chama por nome também para `.zip` (`ProvasIndutivas.zip`: HEAD `provas`, agora `material-de-aula`); só `stash_import.py:99` força `codigo-professor` antes. Contrato corrigido aqui e no tracker; asserção adicionada em `test_fronteiras_decididas_antes_da_regra`.
- 3 NOTA: mantido o isolamento (NFD em variável própria; `name` intacto para os demais ramos).
- 4 AJUSTE (efeito futuro): medido — `bootstrap_ops.py:172` e `pedagogical_regeneration.py:624` só reescrevem `exams/EXAM_INDEX.md` se `exam_entries` não for vazio; `raw/pdfs/<categoria>` deriva da entrada (`entry_processing.py:105`); diálogo preserva `initial.category`. Registrado no tracker: rebuild de entrada antiga não reclassifica; curso que ficar sem avaliação conserva o índice antigo. Wrapper `c1-3/pacote_categoria_17-09.py` redundante com o produto; preservado como histórico.
- 5 NOTA: sondas ampliadas (item 1). Replay com `frases_do_plano` rodado pelo executor: 338 inputs, 3 mudanças (MF), JSON regravado após a correção.

Depois da correção: classe 25/25; suíte 2382 passed / 4 skipped (2357 + 25); replay 338 = 3 mudanças; `git diff --check` limpo.

---

1. [BLOQUEIA] 1/5 — Marcador de avaliação perde prioridade — Medido: em [helpers.py:688](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/utils/helpers.py:688), sondas isoladas reproduziram `Exames - ProvasIndutivas.pdf` e `Prova final - ProvasIndutivas.pdf`: HEAD → `provas`; patch → `material-de-aula`. Nenhum desses nomes aparece nos 338 inputs. / Inferência: avaliações futuras com esses nomes serão rebaixadas. O porte literal reproduz uma lacuna da candidata: `exame` aceita substring no ramo externo, mas exige palavra inteira na proteção. — Ação sugerida: ajustar a proteção e acrescentar regressões com tema matemático + esses marcadores; preservar as 3 mudanças do corpus.

2. [AJUSTE] 3/5 — ZIP não está protegido nos dois chamadores — Medido: [stash_import.py:99](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/core/stash_import.py:99) força ZIP para `codigo-professor`; [dialogs.py:3623](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/ui/dialogs.py:3623) chama a heurística também para ZIP novo. Sonda `ProvasIndutivas.zip` retorna `material-de-aula`; `apply()` conserva a categoria selecionada. / Inferência: a afirmação “ZIP decidido antes” vale somente para o stash. A regra é compartilhada, mas entradas diferem: label Moodle pode acrescentar `P1`; `frases_do_plano` não participa desse ramo. — Ação sugerida: corrigir o contrato e cobrir explicitamente ZIP no diálogo.

3. [NOTA] 2 — Normalização confinada; porte fiel — Medido por leitura: NFD usa variável separada; `name` permanece intacto. Imagens e código retornam antes; demais ramos não foram alterados. Regex equivalentes às de `candidate()`. / Inferência: a normalização nova não muda os ramos posteriores. — Ação sugerida: manter esse isolamento.

4. [AJUSTE] 4 — Efeito futuro exige reclassificação — Medido por leitura: [entry_processing.py:105](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/ops/entry_processing.py:105) deriva `raw/pdfs/<categoria>` da entrada; bootstrap e regeneração filtram avaliações pela categoria existente. O diálogo preserva `initial.category`. O wrapper reaplica a mesma candidata. / Inferência: nova importação corrigida muda os destinos dos 3 PDFs; reconstruir entradas antigas não garante reclassificação. Se não restarem avaliações, a regeneração não reescreve o índice, podendo conservar arquivo antigo. — Ação sugerida: registrar essas condições e a redundância classificatória do wrapper; preservar o artefato histórico.

5. [NOTA] N — Evidência delimitada — Medido: branch/HEAD conferem; SHA-256 do diff = `3cb6f3302fd47bd187d57faadac6f2363ed20dccc3dce96316b4e0bb0bc25aab`; `diff --check` sem erros. Inspeção diferencial das funções extraídas por AST, **sem `frases_do_plano`**, encontrou exatamente 3 mudanças nos 338 inputs, somente MF; JSON persistido concorda. Leitura dos testes confirma 17 casos, mas as 6 sondas de proteção exercitam apenas `P1` e `Prova 1`. / Inferência: o corpus confirma o alvo limitado; não cobre as regressões do item 1. — Ação sugerida: ampliar essas sondas antes do Gate 2.

VEREDITO: REPROVAR

NÃO VERIFIQUEI: pytest vermelho/verde e suíte 2374/4, informados pelo executor; replay integral com frases; GUI; rebuild; ausência de rede nos imports transitivos. Nenhum arquivo alterado.
