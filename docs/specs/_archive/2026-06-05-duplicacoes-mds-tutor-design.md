# Consolidação de duplicações nos MDs do tutor — Design

last_updated: 2026-06-05

## Contexto

Terceira rodada da higiene dos MDs do tutor (audit 2026-06-04, grupo 🟡). As
duplicações de conteúdo entre geradores criam risco de divergência ao editar.
A investigação distinguiu três classes:

- 🔴 **Contradição real:** a sequência pedagógica de ensino existe em 3 ordens
  divergentes (PEDAGOGY 8 passos com Definição→Intuição; MODES 5 com
  Intuição→Definição; OUTPUT_TEMPLATES 7 com Intuição→Definição e rótulos
  diferentes). O tutor recebe instrução conflitante.
- 🟠 **Duplicação de fato:** os pesos de escopo de prova (P1/P2/P3 → 70/30/20/10)
  estão hardcoded em 2 lugares (`pedagogy_md` + `modes_md`).
- ✅ **Não-redundância (fora de escopo):** code_review posture (postura vs
  template — propósitos distintos, já usam `_code_review_profile`);
  CRONOGRAMA_DETALHADO vs CODE_INDEX e cronograma_health vs CODE_HEALTH (views
  complementares, escopos distintos, 4 geradores ativos).
- 🟡 **Summaries por backend (adiado):** 5 modos inline nas 3 variantes de
  prompt + `deeptutor.py` _soul_md — resumos que apontam pra MODES.md; drift de
  nomes possível. Fica pra rodada própria.

## Objetivo

Eliminar a contradição da sequência e a duplicação dos pesos de prova, criando
uma **fonte única** (constante + helpers) em `src/builder/artifacts/pedagogy.py`
da qual os 3 geradores derivam. Decisões aprovadas: ordem canônica
**Intuição antes de Definição**; consolidação via **helper único + rótulos
padronizados**.

## Componente 1 — Sequência pedagógica canônica

Constante única em `pedagogy.py` (ordem Intuição→Definição, rótulos padronizados):

```python
PEDAGOGICAL_SEQUENCE = [
    {"label": "Contexto",         "full": "Por que este conceito existe? Que problema resolve?", "template": "[contexto em 1-2 frases]"},
    {"label": "Intuição",         "full": "Como pensar sobre isso sem formalismo",              "template": "[analogia ou imagem mental]"},
    {"label": "Definição",        "full": "O que é, em termos precisos",                        "template": "[definição precisa, com LaTeX se necessário]"},
    {"label": "Exemplo mínimo",   "full": "O caso mais simples possível",                       "template": "[exemplo mais simples possível]"},
    {"label": "Aplicação",        "full": "Como aparece na disciplina / em computação",         "template": "[conexão com o conteúdo do curso]"},
    {"label": "Erros comuns",     "full": "O que os alunos costumam confundir",                 "template": "[erro mais comum]"},
    {"label": "Exercício guiado", "full": "Uma pergunta para o aluno aplicar",                  "template": "[pergunta para o aluno aplicar]"},
    {"label": "Resumo",           "full": "Uma frase que captura a essência",                   "template": "[uma frase que captura a essência]"},
]
```

Helpers derivados (mesma ordem/rótulos):
- `_pedagogical_sequence_full_lines() -> list[str]`: `["1. **Contexto** — Por que...", ...]` (8 itens numerados, `label — full`).
- `_pedagogical_sequence_compact() -> str`: `" → ".join(label)` → `Contexto → Intuição → Definição → Exemplo mínimo → Aplicação → Erros comuns → Exercício guiado → Resumo`.
- `_pedagogical_sequence_template_lines() -> list[str]`: `["**Contexto:** [contexto em 1-2 frases]", ...]` (bloco template).

Padronização de rótulos (resolve divergências): "Por que existe"→**Contexto**;
"Definição formal"→**Definição**; "Cuidado com"→**Erros comuns**; "Agora
você"→**Exercício guiado**.

Consumo:
- `pedagogy_md` (PEDAGOGY.md): lista numerada via `_pedagogical_sequence_full_lines`.
- `modes_md` (MODES.md, modo study, "Formato de resposta"): via `_pedagogical_sequence_compact` (acaba o "5 vs 8" — mostra os canônicos).
- `output_templates_md` (OUTPUT_TEMPLATES.md, study): bloco via `_pedagogical_sequence_template_lines`.

## Componente 2 — Escopo de prova canônico

Helper único `_exam_scope_rule_lines() -> list[str]` em `pedagogy.py`, forma
bullet canônica:

```python
def _exam_scope_rule_lines() -> list[str]:
    return [
        "As provas são cumulativas mas com peso progressivo:",
        "",
        "- **P1** → cobre tudo do início até a P1. Foco total no conteúdo pré-P1.",
        "- **P2** → cobre tudo até a P2. Foco principal no conteúdo entre P1 e P2 (~70%). Conteúdo da P1 ainda cai, mas com menos peso (~30%).",
        "- **P3** → cobre tudo até a P3. Foco principal no conteúdo entre P2 e P3 (~70%). Conteúdo entre P1-P2 cai menos (~20%). Conteúdo pré-P1 cai pouco (~10%).",
    ]
```

Consumo:
- `pedagogy_md`: substitui o diagrama ASCII (192-208) pelo bloco do helper;
  mantém "Regra prática" + "Exemplo de resposta" como conteúdo próprio em volta.
- `modes_md` (exam_prep): substitui os bullets hardcoded (290-292) pelo bloco do
  helper; mantém "Postura" + "Formato de resposta" próprios.

Resultado: os pesos `70/30/20/10` vivem em um lugar só.

## Implementação

Os 3 geradores hoje são literais `"""..."""` grandes. Converter para
**concatenação**: manter as partes estáticas como literais e injetar a saída dos
helpers via `+ "\n".join(_helper())` (evita f-string com risco de chaves).
`pedagogy_md()` passa a montar o doc por concatenação; `modes_md()` e
`output_templates_md()` já interpolam `profile`, então adicionam os helpers do
mesmo modo.

## Testes

- Unit dos helpers: ordem (Intuição antes de Definição), rótulos padronizados,
  compact arrow, pesos de prova presentes.
- Por gerador: `pedagogy_md`/`modes_md`/`output_templates_md` refletem a fonte
  única (Intuição antes de Definição; rótulos canônicos; sem rótulos antigos
  "Por que existe"/"Definição formal"/"Cuidado com"/"Agora você").
- Guard DRY: o bloco de escopo de prova é idêntico em `pedagogy_md` e `modes_md`
  (ambos contêm cada linha de `_exam_scope_rule_lines()`).
- Testes existentes de `test_code_review_profiles.py` (code_review) não são
  afetados — verificar verdes.

Base: 893 testes verdes.

## Fora de escopo

- 🟡 5 modos inline (3 variantes + `deeptutor.py` _soul_md + MODES.md) — rodada
  própria (extrair lista canônica de modos).
- code_review posture, CRONOGRAMA/CODE overlap — não-redundância, documentado.
- Fim de sessão (2 protocolos) — vai no student_state.
