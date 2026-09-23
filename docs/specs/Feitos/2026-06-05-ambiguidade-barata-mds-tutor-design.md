# Ambiguidade barata nos MDs do tutor — Design

last_updated: 2026-06-05

## Contexto

Continuação da higiene dos MDs do tutor (audit 2026-06-04, grupo 🟢). Depois de
remover as tabelas mortas (grupo 🟠, entregue), restam ambiguidades baratas de
clareza nos geradores/prompts que o tutor lê. Item de backlog: "Higiene dos MDs
do tutor", grupo 🟢.

## Objetivo

Seis correções pontuais de clareza, sem mudança de comportamento estrutural. O
protocolo de fim de sessão (2 variantes divergentes) fica **fora de escopo** —
é acoplado ao formato de import do STUDENT_STATE e vai junto do refactor do
student_state.

## Mudanças

### A. `pedagogy.py:240` — contagem de modos errada
A linha diz "O tutor opera em **quatro** modos." mas a lista enumera **cinco**
(study, assignment, exam_prep, class_companion, code_review). Trocar "quatro" →
"cinco". Única ocorrência de contagem no arquivo.

### F. `pedagogy.py:270` — modo `assignment` referencia só `exercises/`
A postura do modo `assignment` diz "Consulte `exercises/EXERCISE_INDEX.md`",
fundindo lista de prática vs trabalho avaliado (`assignments/`). Passar a
referenciar **os dois índices**: `exercises/EXERCISE_INDEX.md` (prática) e
`assignments/ASSIGNMENT_INDEX.md` (trabalhos).

### B. `repo.py:1658-1662` — label de clamp errado no `glossary_md`
`glossary_md` (emite `# GLOSSARY — {course_name}`) chama
`clamp_navigation_artifact_fn(..., label="course/COURSE_MAP.md")`. Corrigir para
`label="course/GLOSSARY.md"`. (Único label errado restante; os demais caíram nas
rodadas anteriores.)

### C. `navigation.py:288-404` — `render_course_map_md` é código morto
Gerador COURSE_MAP legado paralelo, substituído por
`render_low_token_course_map_md`. **Zero callers** em `src/`, não exportado em
`__all__` nem em `engine.py`, nenhum teste o referencia (confirmado via grep
global: só a definição + docs). Remover a função inteira.

### D. `navigation.py:764-770` — sufixo redundante na célula Unidade do FILE_MAP
A célula Unidade recebe sufixo `_(ambíguo)_` OU `_(baixa confiança)_`. A coluna
Confiança separada já emite "Baixa" para ambos os casos. Decisão refinada: o
sufixo `_(baixa confiança)_` **é** redundante com Confiança=Baixa, mas
`_(ambíguo)_` agrega o **motivo** distinto (vários candidatos vs match fraco) —
não é duplicação pura. Remover **apenas** o ramo `_(baixa confiança)_`; manter
`_(ambíguo)_`.

Novo:
```python
            unit = (
                f"{match.slug} _(ambíguo)_"
                if match.slug and match.ambiguous
                else match.slug
            )
```
Os 3 testes existentes que afirmam o sufixo afirmam o caso `_(ambíguo)_`
(`test_file_map_unit_mapping.py:770,1451`; `test_tag_scoring.py:154`) — nenhum
quebra.

### E. `prompts.py:26` — ordem de navegação contraditória
O contrato estrutural (`_prompt_structural_artifact_contract_lines`) manda "Leia
`course/FILE_MAP.md` e `course/COURSE_MAP.md`" (FILE_MAP primeiro), mas as 3
variantes de prompt (Claude/GPT/Gemini) mandam COURSE_MAP primeiro. O projeto já
decidiu COURSE_MAP como 1º carregado (Approach C). Alinhar a linha 26 para
"Leia `course/COURSE_MAP.md` e `course/FILE_MAP.md` antes de entrar no
conteúdo." (linha 27 só nomeia ambos, sem ordem de prioridade — não muda.)

## Fora de escopo

- **G. Protocolos de fim de sessão** (`prompts.py:94-168`): ditado (`YYYY-MM-DD`)
  vs bloco importável (`DD-MM-YY`), ambos sob "sessão substancial" indefinido.
  Acoplado ao import do STUDENT_STATE → consolidar no refactor do student_state.
- Duplicação 🟡 (escopo de prova 2x, sequência pedagógica em 3 ordens, 5 modos
  inline) — próxima rodada.

## Estratégia de implementação

TDD por item. A/B/F/E são edições simples com teste de regressão leve. C é
remoção de código morto (teste: o símbolo deixa de existir / suíte verde). D tem
RED no novo formato (entry de baixa confiança não-ambígua não recebe sufixo
`_(baixa confiança)_` mas mantém Confiança=Baixa). ~6 tasks curtas,
subagent-driven. Base: 887 testes verdes.
