# Handoff: frente "regime cru" do motor de atribuição (17/09/2026)

Continuação de `2026-09-16-handoff-regime-cru.md`. Escrito pelo Claude (Fable) no fim da madrugada de 17/09, com o
usuário indo dormir. "Medido" = rodado, com log no repositório. "Hipótese" = não medido. Artefato citado sem pasta mora em
`docs/reports/_harness-2026-09-04/c1-3/` (`c1-3/`).

## 0. Leia nesta ordem

1. `.mex/AGENTS.md`, `.mex/ROUTER.md`, `.workflow/README.md` e `.workflow/workflow.md` (Fable executa; Astra revisa
   read-only, uma chamada por tarefa; Gate 1 antes de código, Gate 2 antes do commit).
2. Este arquivo inteiro.
3. `2026-09-16-handoff-regime-cru.md` §3–§6 e `2026-09-15-handoff-regime-cru.md` §3–§11 sob demanda; nada deles é repetido aqui.
4. Estado vivo: `docs/reports/pendencias.md`, blocos "(17/09)" no topo; `.workflow-local/active-task.md` (tarefa
   `fix-categoria-prova-20260917`, status `planejando`, Gate 1 pendente).

## 1. Em uma frase

O item 4.2 foi medido em build real e aceito (MF bloco 50 → 53/66 sem perdas; IA controle idêntico), o DeepTutor saiu do
builder, e o próximo passo, `orch-fix-defect` da regra de categoria em `src/utils/helpers.py`, está com o plano de Gate 1
pronto na §5: falta só a aprovação do usuário para escrever o teste vermelho.

## 2. Estado do repositório (medido, 17/09 ~04:05)

- Branch `feat/motor-atribuicao`, HEAD `fd0747a`. Commits do dia: `cedf9cb` (4.2 medido, 9 arquivos) e `fd0747a` (DeepTutor
  fora do builder, 16 arquivos). Sem push. Suíte: 2357 passed / 4 skipped (34 s), igual a 16/09.
- Working tree: só `.workflow/PENDING.md` modificado, por outra sessão (item [DESIGN] de continuação noturna, 03:24; um
  `codex.exe` dessa sessão continuava vivo desde 02:30). Não é desta frente; não commitar nem reverter.
- `src/` desde 16/09: só a remoção do DeepTutor (`artifacts/deeptutor.py`, chamadas em `ops/build_workflow.py` e
  `ops/incremental_build.py`; `.deeptutor/` permanece no `.gitignore` gerado como exclusão de legado).
- Cópias novas em `.frzero/pacote_categoria_17-09/{Metodos-Formais-Tutor,Inteligencia-Artifical-Tutor}` (gitignored).
  Referência `.frzero/pacote_fontes_15-09` intocada: 86 hashes conferidos antes e depois.

## 3. O que 17/09 estabeleceu (medido)

1. **4.2 em build real**: relatório `categoria-prova-copia_17-09.md`, JSON `c1-3/verificacao_pacote_categoria_MF_IA_17-09.json`.
   MF: 3 categorias alteradas (só os alvos `ProvasIndutivas_EspecificaçõesRecursivas{,_Arvores,_Listas}.pdf`,
   `provas` → `material-de-aula`), bloco 50 → 53/66, unidade 61/66, sub 29/58 e 25/58 sem perda, 0 previsões alteradas
   fora dos alvos, controles `revisao-p1` e `revisao-p1-gabarito` invariantes. IA: 0 alterações, 38/42, 39/42, 5/39, 4/39
   idênticos. Derivados, textos, temporal, taxonomia e `options` conferidos; 0 rede.
2. **Onde estão os erros que sobraram** (medido nos builds novos, por eixo e categoria): bloco e unidade perto do teto
   descontando ausentes (entradas do gold sem fonte: 4 MF, 2 IA). Subunidade é o eixo aberto e o gargalo é
   `codigo-professor`: 17–18 dos 29–33 erros de MF, 22–23 dos 34–35 de IA; em MF 17 previsões vêm vazias, em IA vêm erradas.
   Hipótese, não medida: ZIP/código sem texto extraído deixam o casador de subunidade sem material. Categoria não toca
   subunidade.
3. **DeepTutor fora do builder** (decisão do usuário: inspiração, nunca rodado; o ambiente web próprio vem primeiro e o
   substitui). Astra reprovou a primeira versão do diff (1 BLOQUEIA: `.gitignore` gerado expunha o legado; 3 AJUSTE);
   tudo aplicado, cópia em `c1-3/astra_revisao_deeptutor_17-09.md`.
4. **Ideia futura anotada** no tracker (bloco 16/09 → "Ideias adicionadas 2026-09-17"): extração local CPU + GPU para
   quem não tem Datalab (torch instalado é `+cpu`; `marker_torch_device: cuda` inerte; RTX 4050 ociosa).
5. **Sessão `78faa17a` caiu** às 01:15 com "Connection lost mid-response" (socket fechado no streaming; Windows sem evento
   de rede; status page sem incidente) antes de escrever arquivo; zero efeito colateral.

## 4. Decisões em aberto (do usuário)

- 4.1 review do `d495c66`, 4.3 remedir estrito/A/C, 4.4 distância pacote × herdado, 4.5 herdadas de 14/09: inalteradas
  desde 16/09 (ver `2026-09-16-handoff-regime-cru.md` §4).
- 4.2 encerrado como medição; vira a tarefa da §5.
- Nova, sem dono: subunidade em entradas de código (§3.2). Não abrir sem Gate 1 próprio.

## 5. Próximo passo: `orch-fix-defect` da categoria prova (Gate 1 pronto, aguardando aprovação)

Escolha do usuário em 17/09 ("continuar com o principal" → esta opção). Nada foi escrito ainda.

1. **Defeito**: `src/utils/helpers.py:682`, `auto_detect_category`: a cue `"prova"` casa `provasindutivas` e classifica
   material de aula sobre provas matemáticas como avaliação (`provas`), tirando-o do bloco temporal e pondo-o em
   `exams/EXAM_INDEX.md`.
2. **Teste vermelho primeiro**, `tests/test_core.py`, classe nova `TestAutoDetectCategoryProvaMatematica`, sem fixture:
   os 3 nomes MF → `material-de-aula`; `"Provas por indução.pdf"` → `material-de-aula`; as 6 sondas sintéticas
   (`"P1 - "` e `"Prova 1 - "` + cada alvo) → `provas`; `"Prova 2 - indução.pdf"` → `provas`; as 4 provas reais de IA
   (`"P2 2024.01.pdf"`, `"P2 2024.02.pdf"`, `"Prova 1 2024 02.pdf"`, `"Prova 1 2024.02.pdf"`) → `provas`;
   `"revisao_p1.pdf"` → `provas`; `"ExerciciosCorrecaoInducaoMatematica.pdf"` → `listas`; `"provas.thy"` →
   `codigo-professor` (extensão decide antes). Medir vermelho: os 4 primeiros falham hoje.
3. **Correção mínima**, porte literal de `candidate()` (`c1-3/verifica_categoria_prova_15-09.py:21-26`) para dentro de
   `auto_detect_category`, imediatamente antes do `return "provas"` da linha 682: `ascii = NFD sem combinantes de name`;
   `mathematical = re.search(r"provas?[\W_]*(?:indutiv\w*|por[\W_]+induc\w*)", ascii)`;
   `explicit_exam = re.search(r"(?:^|[\W_])(?:p[123]|av[12]|exame|test|avaliacao|prova[\W_]*[123])(?:$|[\W_])", ascii)`;
   `if mathematical and not explicit_exam: return "material-de-aula"`. Equivalente a `candidate()` para todo nome que
   chegaria ao ramo `provas`; não muda imagem, código e ZIP, decididos antes. Sem tocar o motor.
4. **Verificação além do unitário**: script `c1-3/verifica_regra_categoria_helpers_17-09.py` que recalcula
   `auto_detect_category` (com `moodle_label + nome`, `frases_do_plano` do perfil, como `stash_import.py:43-46`) sobre os
   338 inputs dos 7 `.frzero/pacote_fontes_15-09/*/_inputs_15-09.json` e exige exatamente 3 mudanças (os alvos MF) e 0 rede.
   Suíte completa (referência 2357 / 4). Rebuild dos tutores do produto não faz parte desta tarefa.
5. **Fechamento**: Astra read-only no diff (única chamada; brief com diff inline, como em
   `c1-3/astra_revisao_deeptutor_17-09.md`); Gate 2; commit `fix(helpers): prova matematica nao e avaliacao ...`;
   bloco "(17/09)" no tracker; `active-task.md` concluído; o wrapper de `c1-3/pacote_categoria_17-09.py` passa a ser
   redundante com o produto (registrar, não apagar).

Limite a declarar no relatório: 3 positivos sem holdout, 2 cursos reconstruídos; os 338 do item 4 são replay de
classificação, não build.

## 6. Armadilhas

- `.frzero/` é gitignored e local: testes unitários não podem depender dele; o item 5.4 é harness, não teste.
- `auto_detect_category` recebe `name` já em minúsculas mas sem remover acentos; a regex de `candidate()` pressupõe NFD sem
  combinantes ("indução" → "inducao"). Normalizar antes de casar.
- `_wb("p1")` já protege `revisao_p1`; a regra nova não pode abrir exceção para nomes com marcador explícito de avaliação.
- Astra reprovou o diff do DeepTutor por efeito colateral em arquivo gerado (`.gitignore`). Aqui o análogo é
  `exams/EXAM_INDEX.md` e `raw/pdfs/<categoria>`: mudam por construção nos tutores reconstruídos; dizer isso no brief.
- Não reabrir `.workflow-local/active-task.md` concluído; a tarefa nova já tem ID próprio.

## 7. Primeira mensagem sugerida

"Aprovo o Gate 1 da §5 do handoff 17/09; escreve o teste vermelho." Sem isso, nada de código.
