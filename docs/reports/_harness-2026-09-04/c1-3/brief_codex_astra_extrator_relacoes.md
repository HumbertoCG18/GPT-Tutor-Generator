# Brief 12 para o astra (read-only, esforço LOW): EXECUTE os passos 1–3 do seu experimento — o extrator de relações explícitas — 2026-09-14

## 0. A ordem e as decisões do usuário

> *"1 - Embedding conta como LLM, mas temos que levar em consideração que, dependendo do aluno, ele não vai ter um computador bom
> o suficiente para rodar uma LLM local. E pode rodar o experimento, delegue o astra no low para isso."*

**Decisões que valem para este extrator:** embedding (SBERT, word2vec pré-treinado etc.) **conta como LLM** e está fora; e o
caminho padrão tem que rodar em máquina fraca. **O extrator é processamento de texto puro**: regex, estrutura do documento,
normalização. Nenhum modelo.

**Divisão do trabalho (você está em sandbox read-only):** você faz os passos 1–3 da sua §38.6 — congelar o protocolo, extrair,
auditar. Eu salvo o seu código **verbatim**, reproduzo e rodo os passos 4–5 (motor completo + corte). **Resposta curta.**

## 1. O experimento, como você mesmo o definiu (resumo da sua resposta ao brief 11)

**Hipótese:** enumerações explicitamente ancoradas nas fontes acrescentam relações úteis ao vocabulário, sem mudar regra de
decisão. Extrair **só relações locais explícitas**: `categoria: itens`, `categoria (itens)`, exemplificação delimitada (itens
listados sob um subtítulo que é a categoria). A categoria tem que casar com **rótulo de tópico do plano** ou equivalência
documental admissível. **Não inserir `supervisionado = preditivo` silenciosamente.** Registrar arquivo, linha e trecho.
**Zero relação nova admissível → encerrar o extrator**, sem afrouxar depois.

## 2. FONTES PERMITIDAS e PROIBIDAS (a lista é o protocolo — congele-a)

**Cursos:** os 7 repositórios-produto em `C:/Users/Humberto/Documents/GitHub/<Tutor>/` — `Metodos-Formais-Tutor`,
`Sistemas-Operacionais-Tutor`, `Inteligencia-Artifical-Tutor`, `Engenharia-Software-2-Tutor`, `TCC-Tutor`,
`Computacao-Grafica-Tutor`, `Fundamentos-de-Redes-Tutor`. E o FR construído do zero em
`C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/.frzero/base/`.

**Permitido:**
- **tópicos do plano**: só `label`, `code`, `kind`, `unit_slug` de `course/.content_taxonomy.json` — **NUNCA os `aliases`**
  (são derivados: glossário, sidecar LLM, doação de headings);
- **plano**: `course/COURSE_MAP.md` (gerado do plano de ensino; checklist de tópicos);
- **estrutura do Moodle**: `source_section` e `moodle_label` de cada entry do `manifest.json`;
- **texto nativo dos materiais**: o markdown do material (`manifest.json` → `approved_markdown`/`curated_markdown`/
  `base_markdown`) **com os blocos `<!-- IMAGE_DESCRIPTION ... -->` ... `<!-- /IMAGE_DESCRIPTION -->` REMOVIDOS** (são
  descrições de imagem geradas por LLM), ou o texto nativo do PDF em `raw/` se você preferir. Declare qual usou e por quê.

**Proibido (qualquer leitura disto invalida o experimento):**
- **qualquer gabarito**: `docs/reports/*_gt_*.csv`, `ground_truth_*.csv`, `contradicoes_*.csv`;
- **qualquer análise de erro** de hoje: `erros_subunidade_*`, `teto_aquisicao_*`, `scores_pai_filho_*`, `diagnostico_*`,
  `pai_filho_*`, `evidencia_fora_do_bundle_*`, os logs dos braços;
- **vocabulário derivado**: `GLOSSARY.md`, `.glossary_curation*.json`, `code_curation.json`, os `aliases` da taxonomia;
- **predições do motor**: `computed_*` do manifest (o sidecar "do professor" era circular por usar isso).

## 3. O QUE EU QUERO

1. **O protocolo congelado**, em lista: fontes, padrões aceitos, regra de âncora da categoria (quando `categoria` casa com um
   tópico do plano), regra de admissão do item (tamanho, genéricos, negação), o que descarta.
2. **O código do extrator, completo, num único bloco ```python```**, só stdlib (ou `pymupdf`/`fitz` se ler PDF). Ele deve
   imprimir JSON Lines: `{curso, topic_code, topic_label, termo, padrao, arquivo, linha, trecho, ja_no_rotulo, admissivel,
   motivo}`. `ja_no_rotulo` = o termo já aparece no próprio rótulo do tópico (ex.: DNS em "Protocolos de aplicação para
   infraestrutura (DNS, DHCP...)") — **não é relação nova**. **Rode-o** e mostre os totais.
3. **Os totais por curso:** candidatos · admissíveis · **admissíveis NOVOS** (fora do rótulo). E as relações novas do IA
   listadas, se houver.
4. **O veredito do passo 3**, sem olhar gabarito: **há relação nova admissível?** Se não, diga que o extrator encerra.

**Não faça:** abrir gabarito ou análise de erro; ajustar padrão depois de ver os candidatos para "pegar" perceptron; usar
qualquer modelo; inserir equivalência (`supervisionado = preditivo`) que o texto não declare.
