# Brief 11 para o astra (read-only): AUDITORIA — a relação "termo pertence a tópico" sem LLM, sem sujar o motor — 2026-09-14

## 0. A ordem do usuário, literal

> *"E como podemos fazer isso que não existe? o tirar das fontes do professor a relação 'este termo pertence a este tópico',
> por exemplo 'perceptron' → Modelos Preditivos, sem LLM. Delegue o astra para fazer uma auditoria se já existe algo parecido
> hoje em dia, e como poderíamos fazer isso, sem criarmos mais um eixo sem sentido, ou ter muitos eixos e deixar o motor
> sujo. Penso em depois fundir alguns eixos, mas isso podemos ver depois, quais eixos que existem (datas, sarc, título, etc)."*

**"Eixo", na fala dele, é FONTE DE SINAL / MÉTODO DE DECISÃO** (datas, SARC, título, seção...), não os três eixos de
atribuição. Ele tem medo de resolver o problema acrescentando mais uma fonte ad hoc — e já pensa em consolidar as
existentes depois. **Não faça a fusão agora; mapeie.**

Regras de sempre: MEDIDO × HIPÓTESE, `arquivo:linha`, e diga quando o dado não sustenta. Read-only; você pode rodar código
que só lê e imprime.

## 1. Por que esta pergunta existe — o que já está medido (resumo; detalhe em `docs/reports/2026-09-12-handoff-regime-cru.md`)

Meta: bloco, unidade e subunidade ≥ 95%, **no motor cru** (LLM opcional, nada se sustenta em LLM nem em gold), modular por
professor, com resync.

| eixo | cru honesto (7 cursos) |
|---|---|
| bloco (237) | 93,7% |
| unidade (284) | 89,1% |
| **subunidade (251)** | **56,6% aceito · 39,8% primário** |

**13 regras de ESTRUTURA testadas, nenhuma sobreviveu** (LOCO ou regressão nos 7): precedência bloco×texto (2 versões),
regra do título, SARC posicional, abstenção/margem, limpar mídia, Datalab, seletor de tópicos carentes, engenharia de
bundle, `moodle_label` no scorer, desligar a propagação de headings (+2 no FR, 0 nos 7), singular×plural (0 de 5),
desempate pai×filho.

**O que funcionou, e define a pergunta:**
- **Braço V** — devolver ao cru a relação de 2 tópicos do IA (18 termos, vindos do sidecar LLM): subunidade **142 → 175**,
  IA **12,8% → 97,4%**, zero regressão em bloco/unidade. **Quando a relação certa existe, a conversão é 33 de 34.**
- **FR construído do zero** (0 chamadas): subunidade primário **6/18**; com o vocabulário compilado por LLM, **16/18**.
- **Pai × filho** (`c1-3/scores_pai_filho_13-09.log`): nos 8 erros o filho tem **0 token distintivo no texto**; quando tem,
  vence e acerta **36 de 38**.

**Diagnóstico convergente: o texto tem a evidência, o plano não tem o termo.** O plano diz "Modelos Preditivos"; os slides
dizem perceptron, k-NN, MLP, árvore de decisão. A ementa do IA não menciona nenhuma dessas técnicas.

## 2. INVENTÁRIO — as fontes de sinal que decidem hoje (medido nos manifests da cópia dos 7 cursos)

**Bloco** (`temporal_block_method`, 341 entries): `janela-1` 147 · `disamb` 100 · `titulo-topico` 24 · vazio 23 ·
`prep-prova` 12 · `irmao-card` 10 · `meta-generica` 7 · `disamb-curto` 7 · `ref-generica` 5 · `secao-geral` 3 ·
`due-contain` 2 · `due-straddle` 1.

**Unidade** (`unit_match_reasons`): scorer de texto (todas) · `herdada_do_bloco` 79 · `reconciliada_do_bloco` 66 ·
`herdada_do_vizinho` 26 · `unidade-explicita` (seção `U<n>`) 19 · `unidade_do_bloco_manual` 6 · `tag_boost` 5 · `manual` 4 ·
`explicita-vence-bloco` 2. Cascata em `routing/file_map.py:785-807`.

**Subunidade** (rota): 1ª passada 250 · `rotulo-decomposto` 28 · `sem-sinal` 20 · empate exato 21 · `meta-material` 9 ·
`revisao-sem-assunto-dominante` 5 · `secao-nomeia-subtopico` 8.

**Scorer de subunidade** (`timeline/index.py:1838-1943`): 8 campos com peso — headings 4,4 · título 3,8 · lead 2,8 ·
tags manuais 3,0 · corpo 1,1 · auto-tags 0,22 · legacy 0,15 · raw 0,9; frase exata × alias (0,82) × slug (0,65); overlap de
tokens; `+0,04` incondicional a subtópico. **Não lê `moodle_label_text`**, que `extraction/entry_signals.py:173` coleta.

## 3. INVENTÁRIO — o que JÁ EXISTE que faz (ou tenta fazer) "termo → tópico". Esta é a auditoria.

| # | mecanismo | onde | o que faz | o que se sabe |
|---|---|---|---|---|
| 1 | **Canal do glossário** | `artifacts/repo.py:1713-1760` (`load_glossary_curation`), `repo.py:1771` (`merge_glossary_synonyms`), `extraction/content_taxonomy.py:383-470` (`_parse_glossary_terms`, `_glossary_aliases_for_topic`) | `GLOSSARY.md` tem, por termo do plano, "**Sinônimos aceitos:**"; esses sinônimos viram `aliases` do tópico | **O canal funciona.** No produto, *Modelos Preditivos* tem 14 aliases vindos por ele (Rede Perceptron, k-NN, Árvores de Decisão...). **No cru, só 1: `modelos supervisionados`.** Verificado hoje. |
| 2 | **Seed fixo no código** | `repo.py:1464-1678` (`seed_glossary_fields`), 215 linhas | **36 regras escritas à mão** para termos do MF e do IA (`lógica de hoare`, `model checking`, `modelos preditivos`, `k-nn`, `árvores de decisão`, `mlp`...): devolve definição + UM sinônimo + "não confundir com" | **A relação está na direção errada:** `"modelos preditivos"` → sinônimo `"modelos supervisionados"`. Existe regra `"k-nn"` e regra `"mlp" / "perceptron"`, mas **k-NN e MLP não são tópicos do plano**, então nunca viram alias de *Modelos Preditivos*. É conhecimento de domínio de 2 cursos embutido em `src/` — o padrão "motor sujo". |
| 3 | **Evidência do glossário no acervo** | `repo.py:1199` (`collect_glossary_evidence`), `repo.py:1399-1432` (`find_glossary_evidence`), `repo.py:1434-1462` (`refine_glossary_definition_from_evidence`) | para cada termo DO PLANO, acha o documento com mais tokens do termo e extrai a frase que o define | **Determinístico e já roda no build.** Mas só procura termos que o plano já tem — não descobre termo novo. |
| 4 | Sidecar "do professor" | `c1-3/gera_sidecar_professor.py` → `course/.glossary_curation.json` | a seção do Moodle / sessão do SARC que nomeia um tópico doa os tokens dos seus materiais | **+11 de 66 pontos; IA +0.** Conteúdo quase todo ruído (`chiara`, `capitulo`, `demo`). 6 termos foram escolhidos medindo contra a régua (§29) e saíram. |
| 5 | Vocabulário por LLM | `core/vocabulary_compile.py` → `.glossary_curation.llm.json` | 1 chamada por unidade classifica títulos/headings nos tópicos | IA 5 → 37/39, FR 12 → 17/19. É o que o braço V devolveu. **Fora do regime cru.** |
| 6 | Doação de headings na taxonomia | `content_taxonomy.py:603-646` | heading de material vira alias do tópico que ele "suporta" | **Auto-envenenamento medido** (IA: 5 headings no tópico errado). Sobrevive ao corte do LLM. |
| 7 | 2ª passada da subunidade | `routing/resolver_apply.py` (`propagar_vocabulario_por_headings`, `_partes_de_rotulo`) | token exclusivo dos materiais confiantes vira alias; partes de rótulo composto viram alias | Partes do rótulo **ajudam**; propagação de headings é **troca** (FR +2, CG −3, saldo 0). |
| 8 | Correções aprendidas | `models/tag_profile.py:159-195` (`build_learned_unit_boosts`), gravadas por `ui/dialogs.py:3285` | correção humana na UI grava termos do material → boost de UNIDADE para quem compartilhar termos | Só **unidade**, nunca subunidade. Existe em 3 cursos, com **1-2 correções cada**. |
| 9 | Perfil semântico | `src/builder/semantic_defaults.json`, `core/semantic_config.py:170-232` | `known_tools` (11 provadores), `heading_single_overlap_cues`, e os campos **`domain_cues: {}`** e **`tool_aliases: {}` — VAZIOS** | `content_taxonomy.py:258` ainda tem cues fixos no código: `("recursiv", "indutiv", "predicad", "isabelle", "kripke", "modelo")` — MF. |
| 10 | Co-heading determinístico | `docs/reports/_harness-2026-09-02/coheading.py` | doc cujo 1º heading suporta T doa os demais headings a T | **Refutado**: 26 → 31/93 (contra o LLM 5 → 37/39 no IA). |
| 11 | Resumo de código | `core/code_summarization.py:294`, `code_curation.json` `model: determ-v3` | conceitos extraídos do código dos zips viram texto do scorer | Determinístico; todos os zips têm. |
| 12 | Siglas do plano | `text/stopwords.py:131` (`short_vocab_from_topic_labels`) | sigla de 2-3 letras de rótulo vale como token | Determinístico, por curso. |

## 4. O QUE EU QUERO

1. **A auditoria.** Confirme ou corrija o inventário da §3 — inclusive o que eu não achei. Para cada mecanismo: **faz
   relação termo→tópico de verdade, ou só sinônimo/alias?** Funciona, é peso morto, ou é sujeira (conhecimento de curso em
   `src/`, placeholder vazio, duplicata de outro)? O que deveria **sair**?

2. **"Já existe algo parecido hoje em dia?"** — fora deste código. Quais técnicas **sem LLM** obtêm "técnica pertence a
   categoria" a partir de texto: padrões lexicais de hiperonímia (tipo Hearst: *"algoritmos como X e Y"*, *"X é um tipo de
   Y"*), coocorrência dentro da estrutura do professor (a mesma aula/seção/sessão do SARC nomeia a categoria e a técnica),
   tesauros/ontologias externos de domínio, extração de definição, embeddings locais... **Para cada uma, diga se o dado
   deste projeto sustenta** — você pode ler o acervo (ex.: `../Inteligencia-Artifical-Tutor/`) e procurar se as frases
   existem. **E diga explicitamente se "embedding local" conta como LLM pela restrição do usuário** — não decida por ele,
   mostre a fronteira.

3. **Onde isso entra SEM criar um eixo novo.** O canal nº 1 (glossário → alias) já existe e já funciona no produto. A
   relação obtida deveria entrar por ele? Ou precisa distinguir **sinônimo** de **pertencimento** (seu ponto no brief 7:
   *"k-NN não é sinônimo de Modelos Preditivos"*) — e se precisa, isso é um campo no mesmo canal ou um eixo novo?

4. **O mapa de consolidação** (sem executar): quais das fontes das §2 e §3 se sobrepõem e poderiam virar UMA camada. Minha
   leitura, para você derrubar: os nºs 1, 2, 4, 5, 6 e 7 são todos "vocabulário do tópico" com origens diferentes e hoje
   vivem em 4 arquivos, 2 passadas e 1 função com regras fixas. Isso é uma camada com proveniência, ou são coisas
   diferentes de verdade?

5. **O primeiro experimento**, falsificável: determinístico, 0 LLM, **não escolhido olhando o gold**, com critério de
   parada, validado no FR do zero **e** nos 7 cursos sem regressão por curso. Diga o número mínimo que o faria continuar.

6. **O que NÃO fazer.**
