# Catálogo — formatos de labels temporais nos cards Moodle (semestre 2026/1)

date: 2026-06-12
fonte: API `core_course_get_contents` ao vivo, 7 cadeiras do semestre do usuário.
finalidade: insumo da spec P1 (card_block_map automático via labels) — o parser
deve reconhecer os formatos A-D e degradar honesto no E.

## Formato A — labels "Semana ... a ...:" com ano completo

**Cadeiras:** Métodos Formais para Computação (92717), Engenharia de Software II
(92714); usuário reporta TCC igual. Provável padrão de um grupo de professores.

```
Semana 13/04/2026 a 17/04/2026:
(13/04/2026): Provas em Isabelle, exercícios;
(15/04/2026): Exercícios de revisão para P1.
Semana 20/04/2026 a 24/04/2026:
(20/04/2026): Feriado;
(22/04/2026): Prova P1.
```

- Vive em módulos `label` (campo `description`, HTML) DENTRO dos cards de conteúdo.
- Datas completas DD/MM/AAAA. Várias semanas por card (card temático atravessa semanas).
- Linhas `(atividade assíncrona): ...` intercaladas — sem data, ignorar ou tratar à parte.
- ES2 tem data avulsa fora do padrão no TDE: `Trabalho Final (03/07/2026):`.
- **Derivação**: card → conjunto de datas de aula → blocos da timeline que contêm
  essas datas. Cobertura total dos cards de conteúdo, granularidade por DIA
  (não só semana) — dá até pra mapear linha de aula → bloco específico.

## Formato B — nome da seção carrega a semana + label "Roteiro"

**Cadeira:** Inteligência Artificial (93156).

```
SEC: "Semana 5 -30/03 a 01/04: ML - Aprendizado Supervisionado"
label: "Roteiro
        30/03: Rede Perceptron; Exercicios
        01/04: Rede MLP."
```

- Datas SEM ano (resolver pelo semestre do curso); formatos sujos reais:
  `Semana 5 -30/03` (sem espaço pós-hífen), `20/04 a 24/4` (dia/mês sem zero).
- NOME da seção tem range; label `Roteiro` tem o dia-a-dia.
- **Derivação**: regex no nome da seção + parse do Roteiro. 1 seção ≈ 1 semana
  (mapeamento seção→bloco quase direto).

## Formato C — "Aula N - DD/MM" + CONTEÚDO

**Cadeira:** Experiência do Usuário (92619).

```
label: "Aula 2 - 05/03
        CONTEÚDO: Contexto da Área e Princípios Básicos de IHC/UX
        Orientações sobre esta aula ..."
```

- Seções temáticas; labels de AULA numerada com data sem ano, vários por seção.
- **Derivação**: card → datas das aulas listadas nele → blocos. Mesmo princípio
  do A com regex diferente.

## Formato D — "Semana N - Tópico" sem data

**Cadeira:** Teoria da Computabilidade e Complexidade (93728).

```
SEC: "Semana 7 - Halteproblem und Entscheidungsproblem"
```

- Só o NÚMERO da semana. Datas raras em avisos avulsos ("O Trabalho T1 será
  realizado na aula do dia 20/03").
- **Derivação**: semana N → N-ésima semana letiva do cronograma da matéria
  (precisa da data de início do semestre/cronograma; mais frágil — confiança menor).

## Formato E — sem sinal temporal

**Cadeira:** Sistemas Operacionais (92854).

- Seções temáticas puras ("Threads", "Gerência de Memória"), labels só com
  leituras indicadas. Nenhuma data.
- **Derivação**: NENHUMA pelos labels. Fallback: seção→tópico→bloco por matching
  de conteúdo (o funil atual), com confiança honesta. Nunca inventar.

## Implicações de design pro P1

1. Parser por formato em cascata: A (datas completas) → B (seção+roteiro) →
   C (aula-data) → D (semana ordinal) → E (sem sinal). Cada um emite
   `card → {datas}` com um `format` e uma confiança própria.
2. Datas sem ano: ano do semestre do curso (`parse_moodle_course` já extrai
   "2026/1").
3. `card → {datas} → {block_ids}`: interseção com `period_start..period_end`
   dos blocos do índice — substitui o `card_block_map` manual (que cobria 5/9
   seções de MF e tinha erro comprovado: revisão P1 06→07).
4. O mesmo sinal audita a SEGMENTAÇÃO da timeline (ex.: "Introdução ao Dafny"
   em 11/05 e 13/05 atravessa blocos 12-13 — candidato a fusão).
5. Tolerância obrigatória: espaços ausentes, dia/mês sem zero, linhas
   assíncronas, HTML nos labels (`description` precisa de strip + unescape).
6. Por-dia > por-semana: no formato A, a LINHA de aula identifica o dia exato —
   um card com 7 semanas (ES2 "Microsserviços", 21 arquivos) pode rotear
   arquivo→dia se o nome do arquivo casar a descrição da aula (sinal extra
   futuro, não obrigatório no P1).
