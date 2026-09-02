# Handoff — eixo de COBERTURA + taxonomia do plano de ensino

date: 2026-08-18
branch: `feat/motor-atribuicao` (HEAD `843db1e`)
sessão anterior: handoff `2026-08-18-handoff-pos-cutover-sinais.md` (HEAD era `be62db9`)
working tree: **limpa** · 5 repos-tutor: **limpos** e reprocessados

> Sessão de EXECUÇÃO: tudo abaixo está commitado e aplicado em produção. A seção
> "O que falta" é a fila para decidir, não para rodar direto.

## Boot da nova sessão

1. `mem-search` · `.mex/ROUTER.md` · este handoff · tracker `docs/reports/pendencias.md`
   (header + seção `## CODE — camada de COBERTURA`).
2. Medição desta sessão (3 rodadas + rollout): `docs/reports/2026-08-18-medicao-fix-taxonomia.md`.
3. Handoff anterior (contexto do motor e do cutover): `2026-08-18-handoff-pos-cutover-sinais.md`.

## O que esta sessão estabeleceu (a ideia central)

O sistema tem **dois eixos independentes**, e até aqui só um tinha dono:

| eixo | pergunta | dono | campo |
|---|---|---|---|
| temporal | *quando isso foi dado?* | motor de atribuição | `temporal_block_id` (1 bloco) |
| **cobertura** | *o que isso cobre?* | camada de cobertura | `coverage_units[]` (N unidades) |

Aula tem os dois. **Prova, lista, gabarito, bibliografia, apoio e código de exemplo só têm o
segundo** — enfiá-los no motor é forçar o modelo errado. O pedido original da sessão ("exercícios
e provas estão jogados") é, na verdade, a ausência desse segundo eixo.

Melhor evidência concreta, achada no plano de ensino do SO: o **cronograma** põe threads nas
aulas 8 e 9 ("Gerência do processador, threads e exclusão mútua"), e a **ementa** põe em
`4.1 Programas multithreads`, dentro de Programação Concorrente. Não é conflito — é o eixo
temporal contra o eixo de cobertura, discordando por design.

## Estado verificado (as-of 2026-08-18, HEAD `843db1e`)

- Suite: **1898 passed / 1 skipped / 0 failed**.
- `scripts/audit_taxonomy_losses.py`: **0 tópicos ausentes** nos 5 cursos.
- Réguas por material (produção): SO 27/38 · MF 63/66 · IA 43/44 · ES2 22/28 · TCC 18/25.
  Nenhuma regrediu; TCC melhorou confiante-e-errado de 2 para 1.
- Golds de unidade: ES2 7/7 · IA 9/10 · MF 12/14 · SO 9/11 · TCC 13/13. Pinos: 0 violados.
- Régua de COBERTURA (nova): SO 1/3 exact · F1 0,778 · MF 0/3 · IA 0/3 · F1 0,222.
  "Sem predição" caiu de 8 de 9 para 3 de 9.
- Taxonomia em disco: SO 36 tópicos (era 31) · TCC 26 (era 14) · ES2 21 (era 20).

## Commits desta sessão

| repo | commit | conteúdo |
|---|---|---|
| gerador | `8495926` | fix de taxonomia: parser, filtro de ferramenta, heading institucional, card |
| gerador | `231d201` | régua entry→unidade: gerador de rótulos, scorer, CSVs, baseline |
| gerador | `843db1e` | camada de referência: 4 fixes + métrica de cobertura |
| SO | `3ee2e6b` | reprocess + curation |
| MF | `b5cdef0` | idem |
| IA | `4089446` | idem |
| ES2 | `2878388` | idem (6 órfãs podadas) |
| TCC | `34061b6` | idem (2 órfãs podadas) |

## Achados que mudam como se raciocina sobre o sistema

1. **O `known_tools` era um anti-tópico.** Gerado de headings em CAIXA ALTA, capturava
   `ementa`, `pspace`, `hierarquia`, `cook-levin`, `threads` — e o filtro os usava para
   **descartar tópicos do plano**, por substring. Loop perverso: quanto mais central o termo na
   disciplina, mais provável ele virar "ferramenta" e sumir do índice. TCC perdia 11 de 27
   tópicos, incluindo a unidade 04 inteira (Classe P, NP-Completude, PSPACE).
2. **Sinal textual de uma unidade vazando para outra é uma classe de bug, não um caso.**
   Apareceu três vezes: heading institucional (`ENGENHARIA DE SOFTWARE II`) virando alias no ES2;
   glossário injetando `verificacao de programas` (título da u02) na u01 do MF; e o descritivo da
   unidade do SO carregando `{geren, proce}`, que é o núcleo do título da u02. Sempre que um
   texto genérico entra na assinatura de uma unidade, ela vira ímã do curso inteiro.
3. **Régua ausente é pior que régua imperfeita.** Nenhuma régua media `entry → unidade`:
   `eval_ground_truth` mede entry→bloco, `eval_units` mede bloco→unidade, e todo o efeito do
   trabalho de unidade caía no vão entre as duas. Foi por isso que o card precisou de três
   rodadas de medição — e foi o julgamento caso a caso, não um número agregado, que pegou a
   regressão do MF.
4. **Meu diagnóstico de `_topic_text` estava errado e a medição refutou.** Eu afirmei que os
   `topic_phrases` do pipeline vinham do dict serializado; era artefato da minha instrumentação
   (passei a taxonomia em vez do plano). O fix entrou como defesa, medido neutro. Registrado
   porque a hipótese era convincente e não sobreviveu ao número.
5. **Sem LLM, "conceitos" viram o texto inteiro.** `overlap/len(termos)` com ~2000 termos dilui a
   zero: 0 de 10 refs mapeadas *mesmo com texto disponível*. Com texto bruto a pergunta certa se
   inverte — quantos tópicos **da unidade** o texto cita.
6. **Datas do Moodle seguem inúteis** (achado da sessão anterior, não reaberto). Mas o **card**
   (`source_section`) é sinal humano forte e está em **228 de 233 entries** dos 5 cursos, já
   capturado no import: API do Moodle não é necessária para isso.

## O QUE FALTA (fila para decidir)

### A. Decisões do user — pequenas, destravam limpeza
- **Pino para `Cap. sobre Algoritmos Genéticos` (IA)** — única regressão do rollout. O card diz
  `Semana 12 - Algoritmos de Busca`, a entry foi para `aprendizado-de-maquina`. O gêmeo
  `programa-exemplo AG`, mesmo card, foi para `solucao-de-problemas`: o capítulo tem texto que
  puxa para ML e vence o card; o programa-exemplo não tem texto e segue o card.
- **Duplicatas da P1 do IA** — `p1-2024-02-ia.md`, `prova-1-2024-02.md`, `prova-1-202402.md`,
  67 linhas cada, uma sequer aparece no EXAM_INDEX. Qual fica.
- **Entry fantasma `artigo-usando-agrupamento` (IA)** — `review_status: approved` apontando
  markdown e PDF que não existem. Remover ou reimportar. Está com `scorable=no` na régua.

### B. FASE 3 — código e exemplos (não iniciada)
`code_curation.json` já existe com resumo Gemini e `assign_code_to_block` (bloco, não unidade).
Avaliar se entra na mesma camada de cobertura ou se já está suficientemente servido.

### C. FASE 4 — exercícios, listas e provas antigas (não iniciada)
**Era o pedido original da sessão.** Agora destravada. Diagnóstico já levantado:
- prova é tratada como material de aula (1 arquivo → 1 bloco → 1 unidade), sendo multi-tópico
  por natureza;
- `EXAM_INDEX` promete "quais tópicos têm maior incidência" e entrega 4 linhas com nome de
  arquivo; colunas `Observação`/`Padrão do professor` dependem de `notes` manual sempre vazio;
- `EXERCISE_INDEX` imprime tag crua (`topico:...; tipo:gabarito; bloco:...`) na coluna "Unidade",
  tendo `computed_unit_slug` disponível;
- enunciado e gabarito não são pareados: o SO tem `lista-exercicios-p1` e `-gabarito` lado a
  lado e o índice diz "Solução: não";
- zero extração de questões — sem isso, "incidência por tópico" é impossível.
- **[DECISION] granularidade**: marcar a prova inteira com um conjunto de tópicos (barato,
  determinístico) ou quebrar em questões individuais (caro, LLM, mas habilita a incidência).
  Perguntado ao user, sem ruling.

### D. Teto atual da camada de referência
`eth2` e `aws-encryption-sdk` (MF) ficam com **0 byte** de texto: são repos GitHub cujo README
depende de rede a cada build. `ia-responsavel` (IA, 258B) nunca teve a página convertida.
Não é falha de matching — as 6 refs com texto de verdade receberam cobertura. Cachear o README
no repo resolveria os dois primeiros.

### E. Rebaixado / fechado
- **Descritivo da unidade como token**: o card entrega o mesmo sinal (`threads`) sem o risco de
  arrastar o texto para a unidade errada. Só reabrir se o card se mostrar insuficiente.
- **`_topic_text` com dict**: feito, medido neutro (defesa).
- **API do Moodle para pegar card**: desnecessária, o dado já está no manifest.

### F. Dívidas antigas que seguem abertas
M7 (calibração cross-escala), M4/M5/M6, 2.7 `signal_token_set`, 2.13 smoke tests, 3.1-3.3
estruturais, e a **campanha web** (backlog no fim do tracker).

## Notas operacionais (lições desta sessão)

- **A curation é cache com `matcher_version`.** Ao mudar a semântica do matcher, ou se bumpa a
  versão ou se apaga `course/references_curation.json` — senão a medição repete o resultado
  anterior e você persegue um fantasma. Perdi duas rodadas com isso.
- **Medição em sandbox precisa de `--profile`**: `find_by_repo_root` casa por caminho e o sandbox
  tem outro. Sem o perfil, o índice de unidades cai no fallback repo-derived e a medição fica
  inválida (os `topic_phrases` viram lixo do glossário). O driver agora aborta com erro explícito
  em vez de medir errado.
- **`robocopy` pelo Bash não funciona**: o Git Bash converte `/E` em caminho. Usar PowerShell.
  Exit code 1 do robocopy é sucesso.
- **Heredoc do Bash interpola backticks e `\n`.** Duas vezes corrompeu arquivo (LaTeX e mensagem
  de commit). Para conteúdo com metacaracteres, usar Write ou `python - <<'EOF'` com cuidado.
- **Instrumentação errada gera diagnóstico errado.** Passei a taxonomia onde o pipeline passa o
  plano de ensino e conclui que `topic_phrases` estava corrompido em produção. Sempre reproduzir
  pelo caminho real (`_build_file_map_unit_index_from_course`), não montando o índice à mão.
- Hook `code-review-graph` continua crashando com `UnicodeEncodeError` cp1252 em todo commit —
  conhecido, não-bloqueante.
- MiKTeX local está com instalação mínima (falta `geometry.sty`, babel sem `brazilian`) e trava
  no instalador automático; há uma entrada inválida no PATH
  (`C:\Program Files\Tesseract-OCR\tesseract.exe\`) que ele rejeita. Fora do escopo do projeto,
  registrado porque custou tempo.
