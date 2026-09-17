# Handoff: frente "regime cru" do motor de atribuição (15/09/2026)

Continuação de `2026-09-14-handoff-codex-regime-cru.md`. Serve para Claude ou Codex. Escrito pelo Claude no fim de 15/09,
reconstruído dos artefatos da sessão (tracker, relatórios `Feitos/*_15-09.md`, diff de `src/`), não de memória de conversa.
"Medido" = rodado, com log no repositório. "Hipótese" = não medido.

## 0. Leia nesta ordem

1. `.mex/AGENTS.md` e `.mex/ROUTER.md`.
2. Este arquivo inteiro.
3. `2026-09-14-handoff-codex-regime-cru.md` §3–§9 e §16: meta, decisões, leis de processo, alavancas fechadas e as 3 opções
   continuam valendo e **não são repetidas aqui**.
4. Estado vivo: `docs/reports/pendencias.md`, sete blocos "(15/09)" no topo.

Artefato citado sem pasta mora em `docs/reports/_harness-2026-09-04/c1-3/` (`c1-3/`). Relatório citado sem pasta mora em
`docs/reports/Feitos/`.

## 1. Em uma frase

O defeito do teto do glossário foi corrigido em `src/` (não commitado) com 0 ganhos e 0 perdas nos 7 cursos, e a frente virou
**construção desde fontes**: reconstruir os tutores dos documentos originais custa caro (bloco 222 → 169), a captura Moodle local
recupera a maior parte (→ 210), e uma categoria errada de prova matemática explica mais 3 (→ 213, só no replay temporal).

## 2. Estado do repositório

- Branch `feat/motor-atribuicao`, **36 commits locais não enviados**. Push, merge e PR só por ordem explícita.
- **Nada de 15/09 está commitado.** Árvore suja:
  - `src/` e testes (taxonomia direta, §3.1): `src/builder/core/course_vocabulary.py` (novo), `tests/test_glossary_structured.py`
    (novo), `artifacts/repo.py`, `engine.py`, `extraction/content_taxonomy.py`, `facade/file_map.py`, `facade/glossary.py`,
    `routing/file_map.py`; `scripts/ablacao_rapida.py` ganhou `sync_fresh`.
  - Docs: `pendencias.md`, `docs/Overview-Sistema.html` (estágio ⑦), `.mex/patterns/medir-alavanca-ablacao.md` (2 gotchas).
  - 10 relatórios `Feitos/*_15-09.md` e ~150 scripts/logs/JSON/CSV `c1-3/*_15-09.*`.
- Suite: **2357 passed, 4 skipped** registrada em `c1-3/suite_taxonomia_final_15-09.log` (rede bloqueada no processo) e
  reproduzida pelo Claude na árvore suja ao escrever este handoff (`python -m pytest -q`, 87 s).
- Cópias (gitignored):
  - `.motor3eixos/`: **baseline limpa restaurada**, `_CONFIG_ATUAL.txt` = `regua (veto=texto, SEM curadoria do benchmark=puro)`.
    Resíduos de curadoria MF/FR movidos para `.frzero/contaminantes_motor3eixos_15-09/`; idêntica à de 14/09 em todos os materiais
    (`c1-3/compara_restauracao_x_14-09_15-09.log`).
  - `.frzero/<nome>_15-09/`: um destino por medição (`cru_fontes`, `metadados_*_integral`, `pacote_fontes`, `fluxo_base`,
    `fluxo_direto`, `implementacao_taxonomia`). **Os drivers recusam destino existente**; repetir = nome novo.
- `.ablacao/` e tutores-produto intocados.

## 3. O que foi feito em 15/09 (ordem cronológica)

### 3.1 Taxonomia direta: fix do teto do glossário em `src/`

Plano `plano-taxonomia-direta_15-09.md`, Gate 1 aprovado pelo usuário; evidência `taxonomia-direta-implementacao_15-09.md`.

- `course_vocabulary.build_course_terms` monta os termos integrais (plano + evidências + curadoria). Taxonomia e índice de unidades
  recebem os registros direto; catálogo e perfil semântico recebem `course_terms_text` integral. `GLOSSARY.md` segue com o teto de
  apresentação, que deixa de apagar aliases do motor. Assinaturas legadas preservadas (fallback quando `course_terms_fn is None`).
- TDD: 3 vermelhos → 9 verdes; módulo novo 100% de linhas. Ruff: 0 alertas novos nos arquivos alterados.
- Medido em `.frzero/implementacao_taxonomia_15-09` contra `fluxo_base_15-09`: bloco 222, unidade 253, aceito 142, primário 100,
  **0 ganhos / 0 perdas**; CG **51/59 → 59/59** tópicos com alias; tags, perfil semântico e atribuições idênticos; 0 tentativas de rede.
- **Gate 2 (diff confirmado) e commit: pendentes.**
- Não reconciliado: o handoff de 14/09 §8.2 contou **14 de 59** tópicos sem alias no CG do **produto**; a baseline de cópia de 15/09
  tinha **8 de 59**. Populações diferentes (produto × cópia regua); não verifiquei a diferença.

### 3.2 Dependência das heranças do produto (`herancas-cru_15-09.md`, protocolo `protocolo-herancas-cru_15-09.md`)

7 cursos reconstruídos desde fontes locais (`cru_fontes_15-09.py`), 338 entradas, 316 materiais na régua (303 comuns, 13 ausentes
no denominador). Base herdada → cru desde fontes: bloco 222 → 169/237, unidade 253 → 234/284, aceito 142 → 99/251,
primário 100 → 76/251. Nos comuns: 216 → 169/231, 244 → 234/271, 138 → 99/243, 96 → 76/243. **Ausências não explicam a regressão.**

### 3.3 Contraste de metadados Moodle (`metadados-blocos_15-09.md`)

Transplante histórico de estrutura/semana Moodle: bloco 169 → 195 (+29/−3), unidade 234 → 239 (+9/−4), aceito 99 → 105, primário
76 → 81. Datas de cards, braço separado: IA 25 → 38/42, ES2 11 → 19/28. **Braços não somam; combinação não medida.** Mediu
dependência, não aquisição autônoma.

### 3.4 Diagnóstico das perdas (`diagnostico-perdas-metadados_15-09.md`)

Replay read-only, 9 casos. Retirar o sinal devolve o bloco anterior nos 9. Três causas:
1. card inferido exclui o acerto e substitui decisão incerta (MF/SO);
2. datas de seção ampliam competição lexical (ES2/IA);
3. unidade do bloco sobrepõe ou preenche a unidade curricular (ES2/SO).

### 3.5 Raiz da cadeia captura → currículo (`raiz-cadeia-metadados_15-09.md`)

**Premissa corrigida:** o payload Moodle existe nos 7 tutores da cópia herdada, SHA256 igual ao produto. O driver de 3.2 carregou só
CG e FR. Parte da "herança" era captura bruta omitida, não curadoria. Parsing recupera a estrutura histórica em 303/326 entradas
(23 sem match); datas iguais em 23/24 cards (TDE ES2: 03/07 × 06/07). Unidade inferida do bloco gold concorda com o currículo em
203/220.

### 3.6 Pacote completo de fontes (`pacote-fontes_15-09.md`, protocolo `protocolo-pacote-fontes_15-09.md`)

Documentos originais + `contents.json` Moodle local + perfil salvo (plano/SARC), sem transplantar manifest, pinos ou decisões.
Parsers/backfills existentes, 0 LLM, 7 builds `completed=true`.

| eixo | cru desde fontes | pacote completo | ganhos | perdas |
|---|---:|---:|---:|---:|
| bloco (237) | 169 | **210** | 47 | 6 |
| unidade (284) | 234 | **239** | 9 | 4 |
| aceito (251) | 99 | **108** | 9 | 0 |
| primário (251) | 76 | **84** | 8 | 0 |

338 textos idênticos à referência após normalizar só o prefixo de caminho das imagens. Perdas de bloco: MF 4 (três
`ProvasIndutivas_EspecificaçõesRecursivas*` sem bloco + `terminacao` → 11), SO 1, IA 1. Perdas de unidade: SO 1, ES2 3
(`microsservicos5`, `microsservicos7`, `azure`).

Cadeia reproduzida das 3 provas MF: categoria `provas` (`src/utils/helpers.py:682` casa substring "prova") →
`tier2_due_scope` (`routing/motor/due_window.py:41`) → `lexical=False` (`apply.py:91`) → janela [05,06,07] sem voter → `None`
(`anchor_engine.py:253`). **O acerto antigo escondia um erro de categoria.**

### 3.7 Categoria prova matemática × avaliação (`categoria-prova-verificacao_15-09.md`)

Regra só no script, em memória: `provas` + nome com "prova(s) indutiva(s)/por indução" → `material-de-aula`, salvo marcador
P1/P2/P3, AV1/AV2, exame, test, avaliação, Prova 1/2/3. Mudou 3 categorias em 338. Replay temporal: MF 50 → 53/66, 7 cursos
**210 → 213/237 (+3/0)**; outros 335 sem alteração. Controles preservados: 4 avaliações reais IA, 14 revisões/resoluções, 1 imagem
FR, 6 nomes sintéticos com P1/Prova 1; 56 hashes inalterados.

Limites declarados: **3 positivos, todos conhecidos antes da regra, sem holdout**; unidade/subunidade não reavaliadas; 213 é replay,
não snapshot de build.

## 4. Placar dos regimes (7 cursos de desenvolvimento)

| regime | bloco /237 | unidade /284 | aceito /251 | primário /251 |
|---|---:|---:|---:|---:|
| cru honesto herdado (cópia do produto, 14/09) | 222 | 253 | 142 | 100 |
| taxonomia direta (cópia do produto, 15/09) | 222 | 253 | 142 | 100 |
| cru desde fontes locais | 169 | 234 | 99 | 76 |
| pacote completo de fontes | 210 | 239 | 108 | 84 |
| pacote + categoria prova (replay temporal) | 213 | não medido | não medido | não medido |

Distância do pacote completo ao herdado: bloco −12 (−9 com a categoria), unidade −14, aceito −34, primário −16.

## 5. Decisões do usuário em 15/09: não reabrir

- **MD Datalab existente primeiro**, com arquivo e proveniência verificados (preferência permanente). Metadados de seção/semana
  Moodle são outra fonte, não substituída pelo Markdown.
- Recaptura remota do Moodle **não** é necessária agora: a captura local basta.
- Não habilitar `lexical` globalmente; a distinção prova matemática × avaliação precede qualquer mudança de prioridade temporal.
- Não remover metadados nem trocar precedência global sem medida.
- Nenhuma promoção ao produto nem correção em `src/` além da taxonomia direta sem autorização explícita.

## 6. Defeitos do produto achados e não corrigidos

| defeito | evidência | estado |
|---|---|---|
| `auto_detect_category` casa substring "prova" e trata prova matemática como avaliação | `src/utils/helpers.py:682`, importador `stash_import.py:104`; 3.6 e 3.7 | regra validada só em replay |
| HTML offline: `_PageImages.replace` tenta Datalab com `image_description_source=none` | tripwire bloqueou chamadas no CG (3.2) | harness usa cap zero; produto não autorizado |
| coletor de títulos ignora `staging/`: TCC perde 54 candidatos, SO 72 | `herancas-cru_15-09.md` | sem ablação causal isolada |
| `sync` incremental (`robocopy /E`) preserva arquivos ausentes da origem | resíduos MF/FR em `.motor3eixos/` com `_CONFIG_ATUAL.txt` correto | contornado por `sync_fresh`; `sync` legado intacto |
| card inferido substitui decisão incerta (SO: alternativa com dois scores zero) | `diagnostico-perdas-metadados_15-09.md` §1 | teste mínimo proposto, não rodado |

## 7. Decisões em aberto (do usuário)

1. **Gate 2 e commit da taxonomia direta.** Proposta: um commit `src/`+testes+Overview, outro de harness/relatórios/tracker.
2. **Categoria prova:** reconstrução em cópia com a categoria corrigida na entrada, medindo unidade e subunidade; só então
   `orch-fix-defect` em `helpers.py:682`.
3. **Remedir estrito, A e C** do handoff de 14/09 §8 sobre código com a taxonomia direta. O bloqueio de §8.1 (teto apagando aliases)
   deixou de existir nesse código; o plano de 15/09 excluiu explicitamente essa remedição.
4. **Fechar a distância pacote × herdado (§4):** `staging/`, os 23 vínculos sem match, TDE ES2, perdas de unidade ES2.
5. Herdadas de 14/09 §10, ainda abertas: meta revista, opção B, certificação do zero para cursos inéditos.

## 8. Próximo passo recomendado (recomendação do Claude, não decisão)

1. **Gate 2 + commit da taxonomia direta.** Suite verde e 0 perdas medidas; manter árvore suja com 10 arquivos de `src/` torna toda
   medição seguinte ambígua quanto ao código usado.
2. **Categoria prova em cópia** (item 7.2). Custo medido do pacote MF: 3.980 s; os 3 materiais são só MF, então MF sozinho basta
   para unidade/subunidade, mais um controle IA pelas avaliações reais.
3. **Remedir C** (item 7.3). É o único jeito de a opção C dizer algo sobre o LLM. Ressalva: LLM é regime opcional (14/09 §4), então
   isso informa a meta revista, não o cru.

Contraponto: o fix do teto deu **0** no placar do cru. Ele era pré-requisito de medição, não alavanca; não esperar ganho dele.

## 9. Armadilhas novas (estão também em `.mex/patterns/medir-alavanca-ablacao.md`)

- Cópia nova do produto **não** é construção nova: herda manifest, pinos, captura e curadoria.
- Driver de cópia: `c1-3/motor_copia_nova_15-09.py --destino .frzero/<nome-novo>` (usa `sync_fresh`). Falha de cópia inutiliza o
  destino; rodar de novo com outro nome, sem apagar a saída parcial.
- `_CONFIG_ATUAL.txt` correto não prova ausência de resíduos.
- Perfil salvo (plano/SARC) é herança declarada: o pacote completo não prova autonomia a partir de PDFs puros.
- Replay temporal não valida unidade nem subunidade: `computed_*` antigos não são evidência após reconstrução.
- Conferir estrutura temporal (IDs, períodos, sessões) antes de reutilizar gold ordinal.
- Não atribuir delta isolado a aliases quando texto, metadados e pinos mudaram juntos.
- HTML exige tripwire mesmo com `image_description_source=none`.
- Sete PDFs marcados `scanned-pages`: importar não garante qualidade de texto.

## 10. Afirmações corrigidas em 15/09 (não repetir)

| afirmação errada | correção | fonte |
|---|---|---|
| "o cru desde fontes exige recaptura remota do Moodle" | payload local existe nos 7, SHA256 igual; o driver só carregou CG/FR | 3.5 |
| "a regressão do cru desde fontes é curadoria herdada" | parte é captura bruta omitida | 3.5 |
| "as 3 ProvasIndutivas MF estavam certas no herdado" | acerto escondia categoria errada; janela temática estreita decidia por acaso | 3.6 |
| "`.motor3eixos/` com config regua está limpa" | tinha resíduos MF/FR | 2 |
| "fix do teto melhora o placar do cru" | 0 ganhos / 0 perdas | 3.1 |

## 11. Índice de artefatos de 15/09

| tema | relatório | driver / evidência principal em `c1-3/` |
|---|---|---|
| taxonomia direta | `plano-taxonomia-direta_15-09.md`, `taxonomia-direta-implementacao_15-09.md` | `motor_copia_nova_15-09.py`, `verifica_taxonomia_impl_15-09.py`, `compara_implementacao_taxonomia_15-09.log`, `suite_taxonomia_final_15-09.log` |
| heranças | `herancas-cru_15-09.md`, `protocolo-herancas-cru_15-09.md` | `cru_fontes_15-09.py`, `audita_herancas_15-09.py`, `compara_herancas_15-09.py`, `auditoria_herancas_15-09.json` |
| metadados | `metadados-blocos_15-09.md` | `metadados_blocos_15-09.py`, `pontua_metadados_15-09.py`, `placar_metadados_7cursos_15-09.json` |
| diagnóstico | `diagnostico-perdas-metadados_15-09.md` | `diagnostica_perdas_metadados_15-09.py`, `diagnostico_perdas_metadados_verificado_15-09.json` |
| raiz da cadeia | `raiz-cadeia-metadados_15-09.md` | `rastreia_cadeia_metadados_15-09.py`, `cadeia_metadados_verificada_15-09.json` |
| pacote completo | `pacote-fontes_15-09.md`, `protocolo-pacote-fontes_15-09.md` | `pacote_fontes_15-09.py`, `verifica_pacote_fontes_15-09.py`, `verificacao_pacote_7cursos_15-09.json`, `replay_abstencoes_pacote_raiz_15-09.json` |
| categoria prova | `categoria-prova-verificacao_15-09.md` | `verifica_categoria_prova_15-09.py`, `verificacao_categoria_prova_verificada_15-09.json` |
| teto (sondas) | — | `teto_glossario_cru_15-09.py`, `teto_taxonomia_cru_15-09.py`, `teto_*_CG_15-09.log` |

## 12. Primeira mensagem sugerida

```
Leia .mex/AGENTS.md, .mex/ROUTER.md e docs/reports/2026-09-15-handoff-regime-cru.md inteiro
(e o de 14/09 §3–§9 sob demanda). Não mude src/ nem rode medição ainda.
Mostre o git diff --stat de src/ e diga se o diff da taxonomia direta está pronto para Gate 2,
depois resuma em 5 linhas as decisões em aberto da §7, separando medido de hipótese.
Medições com 0 chamadas de LLM; astra só por ordem minha.
```
