# Handoff 2026-08-26 — holdout Computação Gráfica: site → PDF → stash → CLI → motor nu

Substitui, para a fila, o `2026-08-21-handoff-rumo-aos-100.md` (que continua valendo como história e leis).
Tracker vivo: `docs/reports/pendencias.md` (cabeçalho as-of 2026-08-26 + `## FILA VIVA`).
Artefato de leitura: "Razão dos Blocos" — https://claude.ai/code/artifact/d2ef4eaa-3483-412a-9dc8-110b1f9ccacb
(cronograma × bloco × atribuição × decisor, uma tab por cadeira; regenerar com `scratch/dados_artefato.py` + `patch_razao.py`).

## 0. Leia antes de tocar em qualquer coisa

**Leis da campanha (inalteradas + 3 aprendidas hoje):** dado real antes de código · raiz, nunca remendo · tudo pelo
motor, LLM o mínimo (fallback, não primário) · sem motor por categoria · **4b: sem motor por CURSO** (os 5 tutores são
bancada, não alvo; regra que só vale para um curso é pino ou curadoria) · pinar menos · nada avança com régua pior em
qualquer eixo · commit trailers `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>` + `Claude-Session:` ·
respostas em português começando com `[Humberto]`.
- **Restaurou tutor por git → reprocessa.** `.timeline_index.json`, `.content_taxonomy.json`, `.tag_catalog.json`,
  `.semantic_profile.generated.json`, `.assessment_context.json` são ignorados pelo git (R11).
- **Gate é determinismo também:** 2 reprocess seguidos = 0 campos (R11 fechou a memória de 1 passo).
- **Sentinela contra `git show HEAD:manifest.json`**, nunca contra `.bak`.
- **Medida do motor nu = `scripts/ablacao_rapida.py`** (cópia, paralelo, 81 s). Nunca mais ablação in-place.

**Gate único entre passos:** `python scripts/eval_eixos.py` · `python -m pytest -q` (ler "N passed") · sentinela campo a
campo (`scratch/sentinel_head.py`) · para regra de motor: `ablacao_rapida.py` antes/depois e `--curado` (cópia == original).

## 1. Onde estamos (as-of 2026-08-26, gerador `d12a5da`)

| eixo | curado | motor nu (zero curadoria) |
|---|---|---|
| bloco | **199/200**, conf-err 0 (o erro = ES2 `azure`, convenção) | **205/212 por uuid (96,7%)**, display 194/200, conf-err 2 |
| unidade | **191/191** | 134/191 (DP monotônico vs inversão calendário-vs-plano; raiz atrás dos pinos de unidade IA/ES2) |
| cobertura | 40/57 F1 0,811 | 34/57 |
| subunidade | 87/93 | ~21/94 (depende do sidecar de sinônimos) |
| humano | **pinos 5** · cards manuais **1** (TCC "Semana 12") · 6 decisões de bloco (eram 23) | 0 |
| suíte | **2047 passed** | — |

**O que esta sessão fechou (tudo com número, tudo no tracker):** R11 perfil semântico sem memória da rodada anterior;
R12 injetor do sumário idempotente; corte de bloco pela CABEÇA da linha do cronograma (SO sem `boundary_dates`);
prep-prova antes do voto em janela indireta; identificador de trabalho `t1/t2` (card ↔ sessões); `titulo-topico`
(arquivo nomeado pelo tópico do bloco decide sem voto); 7 golds corrigidos por ruling com evidência de conteúdo;
23 → 6 decisões humanas; ablação 12 min → 81 s.
**Refutado (não retentar sem dado novo):** `posting_date` como provider (modal = carga inicial; não-modal em mini-lotes
e pós-bloco); afinidade de kind material-de-aula → só `class` (−25/+2); tópico vence ordinal (−3/0); "bola de neve" como
raiz do SO. Os 7 erros nus restantes são decisão, não código (3 ruído do voto, 2 convenção, 2 domínio Cook-Levin).

**Decisões abertas do user:** (a) `pthread` SO: ruling de 25/08 dizia bloco-03 (heading "Thread APIs vs. System
calls"); 26/08 disse 04 (card Threads; `exemplo-threads-em-c` ×3 já são 04). Mantido 04; reverter = 1 gold + 1 pino.
(b) IA `prova-1-2024-02` e ES2 `azure`: pino ou `scorable=no`. (c) sidecar `.glossary_curation.json` por LLM.
(d) SO e ES2 **sem remote** (sem backup).

## 2. O site da CG — fatos verificados no HTML cru (26/08)

`https://www.inf.pucrs.br/pinho/CG/` (professor Márcio Pinho). HTML estático; **0 script de conteúdo, 0 iframe, 0
"modal"** — a pendência "modals" (25/08) morre: não existe. Arquivos do dia salvos no scratch (`cg_index.html`,
`cg_cronograma.html`, `cg_cronograma.md`) — servem de fixture.

| documento | formato | encoding | o que importa |
|---|---|---|---|
| índice `/CG/` | Word 15 HTML, 132 palavras | cp1252 | links: `CronogramaAtualCG.html`, `Bibliografia.htm`, `Exercicios/Lista2D/ExerciciosP1.html`, `Exercicios/Lista3D/Lista3D.htm`, `tiny.cc/PinhoOpenGL`. **Não linka as páginas de aula.** |
| `CronogramaAtualCG.html` | Word 15, 1 tabela **40 linhas × 6 col = formato SARC idêntico aos outros 5** (`# \| Dia \| Data \| Hora \| Descrição \| Atividade`) | **UTF-16 com BOM** (`charset=unicode`) | `html_to_structured_markdown` já produz a tabela perfeita (42 linhas) **se decodificado certo**; o parser de timeline funciona sem mudança. |
| hub `Aulas/GeomComp/GeomComp.htm` | 118 palavras, 2 tabelas, 0 headings | cp1252 sem header | 3 links relativos (`Dominancia/Domina.html`, `Slab/Slab.html`, `PlaneSweep/PlaneSweep.html`) + 3 logos |
| folha `Dominancia/Domina.html` | 231 palavras, 27 `<p>`, 0 headings | cp1252 sem header | 5 diagramas relativos `domina1..5.jpg` + 3 logos; 0 links |
| `Exercicios/Lista2D/ExerciciosP1.html` | Word 15, 2 headings, 3 tabelas | ISO-8859-1 | 4 imagens de conteúdo (`Image53.gif`, `../ListaP1-2011-1/Window1.png`) + 3 logos |
| `Bibliografia.htm` | 197 palavras | ISO-8859-1 | 6 links externos (livros/PDF de terceiros) |

**Consequências:** (1) as páginas de aula chegam **pelo Moodle** (links), não pelo índice — o crawl começa nas URLs
do Moodle, 1 nível (hub → folhas); (2) toda página tem 3 logos (`/pinho/Logotipos/*`, `grv…logo`) = boilerplate a
filtrar por **frequência**, não por nome; (3) encodings misturados — **defeito real**: `ops/url_and_cleanup.py:81`
decodifica com `get_content_charset("utf-8")` fixo → UTF-16 vira "l e t r a", latin-1 vira mojibake. Ordem certa:
BOM → `<meta charset>` → header → cp1252; (4) `.htm` (sem L) é descartado em silêncio no import e `.html` vira
`codigo-professor` (`utils/helpers.py:204/647`) — 2 defeitos conhecidos, só importam na rota direta.

## 3. Decisão de rota (user, 26/08): PDF como desbloqueio, HTML direto como regime permanente

**Rota escolhida para o holdout: snapshot → PDF (Edge headless) → stash → Datalab → pipeline de sempre.** Por quê:
zero código novo no pipeline (o holdout testa o MOTOR, não a ingestão); o navegador resolve encoding e renderiza as
imagens relativas dentro do PDF, e o Datalab já extrai figuras de PDF — os `domina1..5.jpg` chegam sem código de
imagem. O que se perde: `href` (texto morto no PDF), estrutura HTML, e custo Datalab por página.
**Exceção obrigatória: o cronograma NÃO passa por PDF.** É o esqueleto da timeline; a tabela já sai limpa do
conversor HTML. Mandar 40×6 para OCR reconstruir é risco gratuito. HTML → `SYLLABUS.md` direto.
**Adendo que preserva a camada de links:** o snapshot grava `raw/site/site_links.json` (hub → folhas, URL + caminho
local + título) além do HTML cru. Não toca o pipeline; quando a rota direta HTML→MD entrar, a relação já existe.
**Regime permanente (depois do holdout, não agora):** `.htm/.html` como tipo de 1ª classe, conversor com `<img>`
(`content/images/<entry>/` + IMAGE_DESCRIPTION), `href` relativo → absoluto, logos por frequência, e link entre
páginas do snapshot vira relação `hub → folha` gravada na entry (folha herda card/bloco do hub, como o irmão-card).
O user aprovou esse desenho em princípio; codar só com material medido.

## 4. O plano, passo a passo, com dados reais (user: "um a um")

### Passo 1 — `scripts/site_snapshot.py` (camada raw + PDFs para o stash)
Entrada: lista de URLs com o card do Moodle de cada uma (JSON ou `URL@card`), `--stash <dir>`, `--depth 1`.
Saída: `raw/site/<host>/<path>` = bytes originais (`.orig`) + cópia normalizada UTF-8 com `<meta charset>` (é a que se
imprime; o navegador não erra o BOM, mas erra cp1252 sem header) + imagens relativas ao lado + `site_links.json`.
`--pdf`: `msedge --headless=new --disable-gpu --no-pdf-header-footer --print-to-pdf=<stash>/<card>/<nome>.pdf file:///<normalizado>`
(Edge em `C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe`; Chrome também existe; weasyprint não).
`--syllabus <URL>`: decodifica (BOM/meta/header) → `html_to_structured_markdown` → grava a tabela como `SYLLABUS.md`.
Gate do passo: PDF abre e tem N páginas > 0; imagens de conteúdo presentes no PDF (as 5 do Domina); `SYLLABUS.md`
com 40 linhas de dados; `site_links.json` com hub → 3 folhas. Fixture: os 4 HTMLs reais.

### Passo 2 — links do Moodle importados automaticamente, com classificação (requisito do user, 26/08)
Fonte: `MoodleClient.get_course_contents` (`core_course_get_contents`) já usado pelo backfill; módulos com
`modname == "url"` (e `resource`/`page` quando apontam para fora) trazem nome, URL externa e a seção (card).
**O problema real não é baixar, é classificar:** link de **material de aula** (página do professor, PDF de slide) vs
link de **bibliografia / referência / repositório** (livro, artigo, GitHub, documentação, YouTube). Os dois já têm
destino no sistema: material → stash (passo 1, vira entry normal); referência → entry com categoria
`bibliografia`/`referencia` (fora do desempate: `_OUT_CATEGORIES`; sem card → `ref-generica` = 1º bloco de aula), sem
imprimir PDF de repositório.
Sinais **determinísticos e sem curso** (ordem de confiança, medir cada um contra rotulagem do user na CG):
1. **Card**: seção do Moodle com "bibliografia", "referência(s)", "links úteis", "leitura(s)", "material complementar"
   → referência. Seção "Semana N…"/tópico → material.
2. **Domínio/caminho**: mesmo host do site do professor, sob o diretório do curso (`/pinho/CG/Aulas/...`) → material;
   `github.com`, `gitlab`, `doi.org`, `dl.acm.org`, `ieeexplore`, `springer`, `sciencedirect`, `scholar.google`,
   `books.google`, `amazon`, `wikipedia`, `youtube` → referência/repositório (lista curta, genérica, no código — NÃO por curso).
3. **Nome do link**: "livro", "artigo", "paper", "repositório", "documentação", "tutorial", "manual" → referência;
   "aula", "slides", "notas", "capítulo N", "roteiro", "exercícios" → material.
4. **Conteúdo (fetch)**: página com texto + imagens e poucos links de saída = folha de material; página que é lista de
   links = hub (segue 1 nível); PDF no domínio do professor = material; PDF de terceiros = referência.
**Ambíguo → `manual-review/web/` (já existe)**, nunca chute silencioso. Gate do passo: o user rotula a lista de links
da CG (material / referência / repositório / ignorar) e a classificação é medida — precisão por sinal, antes de virar
default. Saída do passo: `stash/<card>/…` (material) + `links_referencia.json` (referências, para virar entries
`bibliografia` no passo 3).

### Passo 3 — `scripts/build_course.py` (CLI do build inicial; hoje só existe pela UI)
Stash + metadados (nome, `SYLLABUS.md` do passo 1, plano de ensino PDF) → repo novo pelo **mesmo caminho da UI**:
`stash_import.scan_stash_cards` → `build_stash_entries` → `RepoBuilder(...).build()` com as options de
`_build_options_from_config` (ui/app.py:101-102) — ler antes de codar; nada de segundo caminho. Entries de
referência do passo 2 entram com categoria `bibliografia`/`referencia`. Depois: `reprocess_assignments.py`,
`eval_eixos.py` (precisa de gold — passo 4). Por quê CLI: holdout **reprodutível** ("zero curadoria" = 1 comando),
log inteiro visível, e é a peça que falta para automatizar cadeira nova. Também diagnóstico: o user pediu
explicitamente para eu ver o fluxo inteiro.

### Passo 4 — holdout
Repo CG com **zero pino, zero card manual, zero sidecar, zero boundary_dates**. Gold de bloco por uuid (~30 entries,
protocolo dos outros: conteúdo primeiro, `ground_truth_CG.csv` com `true_block_uuid`). Medida: `ablacao_rapida.py
--repos CG` (adicionar CG ao `REPO`) — bloco por uuid; expectativa honesta **≥ 90%** (os 5 deram 96,7% mas foram
vistos). O que a CG revela primeiro: **o hábito do professor** (data na seção? no nome? "Aula N"? só card temático?) —
o motor tem um provider por hábito (labels / data / ordinal / topic+t1t2); hábito novo = balde A/B de novo, nunca
curadoria. Depois: unidade (o plano da CG segue o calendário?), cobertura, subunidade (sem sidecar = cega).

## 5. O que o user precisa fornecer
- Acesso ao curso CG no Moodle (token já em `moddle/.env`; falta o `courseid` da CG) ou o export do Moodle.
- Plano de ensino da CG (PDF) — unidades e tópicos alimentam taxonomia e DP de unidade.
- Rotulagem da lista de links (passo 2) e decisão sobre repositórios (só metadado, ou baixar README?).

## 6. Ferramentas (onde está o quê)
`scripts/ablacao_rapida.py` (nu em cópia, paralelo; `--curado` = gate; env `TUTOR_REPOS_DIR` nos avaliadores e
`TUTOR_REPOS_ORIG` no reprocess) · `scripts/erros_motor_nu.py` (33→7 erros por entry com sinais) ·
`scripts/harness_balde_b.py` (regras candidatas × gold, sem LLM) · `scripts/reprocess_assignments.py` ·
`scripts/eval_eixos.py` · `scripts/explain_entry.py`. No scratch (mover para `scripts/` se virar rotina):
`harness_regras.py` (R3/R5/R6), `redundancia.py` (pino/card × motor nu), `dados_artefato.py` + `patch_razao.py`
(artefato), `sentinel_head.py`, `mdiff.py`, `fusao.py` (estrutura de blocos em memória sem boundary_dates).
