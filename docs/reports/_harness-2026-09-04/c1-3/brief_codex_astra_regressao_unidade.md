# Brief para segunda opinião (Codex astra, read-only) — regressão de UNIDADE entre 07/09 e 11/09 (SO 4, CG 5), 2026-09-12

Repositório: C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator. Sandbox read-only: não edite, não rode nada que chame
Gemini. Você JULGA os dados abaixo, que já estão prontos; só abra arquivo se um trecho aqui não bastar, e leia por trecho
(`sed -n a,b`), agrupando leituras num comando só. Responda em português, no máximo 1 página mais tabelas; cada achado com
evidência (linha desta página ou arquivo:linha) e marcado MEDIDO ou HIPÓTESE. Abreviação: `c1-3/` =
`docs/reports/_harness-2026-09-04/c1-3/`. Sua revisão do estado da C1 (ontem à noite) apontou que o gate "sem regressão em
unidade" não estava demonstrado; isto é a caça à causa. O defeito vai entrar por `orch-fix-defect` (teste vermelho primeiro).

## 1. O que regrediu (MEDIDO: unidade de cada material no último commit de 07/09 de cada tutor × hoje; gold = `_load_truth`)

| curso | mudou | piorou (com gold) | materiais |
|---|---|---|---|
| SO | 4 | 4 (2 confiantes, `revisar=ok`) | `lista-exercicios-p1`, `lista-exercicios-p1-gabarito`, `laminas-cs-4244-internet-programming-sockets-p…`, `laminas-sockets-material-alternativo-em-pt`: u03 → u02 |
| CG | 6 | 5 (gold de 11/09) | card "2 - Biblioteca OpenGL": `exercicios`, `opengl-cpp`, `opengl-py`, `openglbasico`, `texturas-v3`, `video-…-opengl-na-vdi`: u01 → u02 (`texturas-v3` errava nos dois, gold u08) |
| TCC | 1 | sem gold | `aula-06-revisao-…`: u01 → u02 |
| IA, ES2, MF, FR, LR | 0 | 0 | |

Os rollouts de 11/09 (camada 3, zips, vocab LLM nos 8, M1) mediram bloco e subunidade, não unidade. Os 4 do SO não estão na
régua de subunidade; os 5 do CG estão (gold `aplicacoes` desde ontem; hoje o produto prevê vazio em 2 e `entidades-geometricas` em 3).

## 2. Mecanismo (MEDIDO no manifest: `unit_match_reasons`)

Os materiais NÃO mudaram de bloco temporal. O que mudou foi a UNIDADE DO BLOCO, que o material herda (`herdada_do_bloco`):
```
SO  laminas-cs-4244-…   07/09: unit=u03 tb=cfb895fb reasons=['winner_score=3.52','topic_score=4.14','ambiguous','herdada_do_bloco=bloco-09']
                        hoje : unit=u02 tb=cfb895fb conflito=u03 reasons=['winner_score=39.74','topic_score=44.69','reconciliada_do_bloco=bloco-09']
SO  lista-exercicios-p1 07/09: unit=u03 reasons=['winner_score=19.97','topic_score=3.92','herdada_do_bloco=bloco-09']
                        hoje : unit=u02 reasons=['winner_score=24.38','topic_score=9.11','herdada_do_bloco=bloco-09']
    bloco-09 hoje: 2026-04-23 unit_bloco=u02 auto=u02 conf=0.6 topic_text='comunicacao entre processos pipes filas'
CG  opengl-py           07/09: unit=u01 tb=21eb1cc4 reasons=['winner_score=29.60','topic_score=13.34','herdada_do_bloco=bloco-02']
                        hoje : unit=u02 reasons=['winner_score=33.14','topic_score=12.40','herdada_do_bloco=bloco-02','herdada_do_vizinho=bloco-03']
CG  video-…-vdi         07/09: unit=u01 reasons=['winner_score=6.00','topic_score=7.06']
                        hoje : unit=u02 reasons=['winner_score=0.00','topic_score=0.00','ambiguous','herdada_do_bloco=bloco-02','herdada_do_vizinho=bloco-03']
    bloco-02 hoje: 2026-08-06 unit_bloco='' auto=u01 conf=0.0 topic_text='introducao opengl'
```
A unidade do bloco vem de `src/builder/timeline/index.py::_assign_timeline_block_to_topic` (l. 2036–2131): pontua
`topic_text` do bloco contra cada tópico da taxonomia (label + aliases; aliases = glossário manual + vocab LLM
`course/.glossary_curation.llm.json`); vencedor fraco (`winner_score` < 1,35..1,85 conforme tokens do label, ou confiança baixa)
→ `unit_slug=""` e o material cai para `herdada_do_vizinho`.

## 3. O que mudou nas taxonomias em 11/09 (MEDIDO)

**SO.** O compilador de vocabulário (item 2.4, Gemini, 1 chamada por unidade) doou a "3.1 Conceitos básicos" (u02, gerência do
processador): `Processos, Recurso Computacional, Imagem do processo, Bloco de Controle do Processo, Inter-process
Communication, Comunicação entre Processos, Memória Compartilhada, Pipes, Tubos, Multithread, Troca de Mensagens,
Sincronização, Exclusão mútua`. Os 4 primeiros já eram sinônimos manuais de 3.1 (`GLOSSARY.md:50`). O plano tem em u03
"4.2 Comunicação e sincronização de processos", cujos aliases manuais são `Comunicação e Sincronização, Comunicação entre
Processos (1), Comunicação entre Processos (2), Processos, Programação de sockets, Socket, Socket programming, Sockets, exec…`.
O pós-filtro `src/builder/core/vocabulary_compile.py::filter_terms` (l. 135–170) checa: termo == label · termo em > 1
tópico DO PRÓPRIO compilado · genérico · identidade contra LABELS de outros tópicos e títulos de unidade (`others`) · rótulo
meta. **Não checa contra os aliases MANUAIS dos outros tópicos**: "Comunicação entre Processos" não é igual ao label
"Comunicação e sincronização de processos" nem está contido nele, e "Comunicação entre Processos (1)" é alias manual, invisível
ao filtro. "Conceitos básicos" existe em 2 unidades do SO e é alvo real: generalizar rótulo meta para ele PERDE (medido 11/09,
`c1-3/replay_exp_regras.log`).

**CG.** O M1 (`META_LABELS` += conceitos, areas relacionadas; +2 na subunidade do CG, 0 perdas em 6 cursos, aprovado) tirou
`OpenGL`/`OpenGL 3D` de "1.2 Conceitos" (u01). Hoje 1.2 tem só o alias com código. O bloco-02 "introducao opengl" ficou sem
âncora. Ruling do user (11/09 noite): OpenGL é u01, subunidade 1.4 Aplicações; o plano de ensino não lista OpenGL em unidade
nenhuma.

## 4. As hipóteses medidas com a função real do motor (MEDIDO, `c1-3/mede_regressao_unidade_bloco.log`, 0 chamadas)
```
== SO bloco-09 'comunicacao entre processos pipes filas' (07/09: u03; hoje: u02)
  hoje (3.1 com as doacoes do LLM)                           -> unit=unidade-02 topico=Conceitos básicos              conf=1.00 ['winner_score=10.97'] | top3=[(u02,'Conceitos básicos',10.968), (u03,'Comunicação e sincronização',4.556), (u05,'Sistemas monoprogramados',0.2)]
  sem 'Comunicacao entre Processos' e 'Pipes' em 3.1         -> unit=unidade-03 topico=Comunicação e sincronização de conf=1.00 ['winner_score=4.56'] | top3=[(u03,'Comunicação e sincronização',4.556), (u02,'Conceitos básicos',3.366), (u05,'Sistemas monoprogramados',0.2)]
  3.1 sem NENHUMA doacao do LLM (so o manual)                -> unit=unidade-03 topico=Comunicação e sincronização de conf=1.00 ['winner_score=4.56'] | top3=[(u03,'Comunicação e sincronização',4.556), (u05,'Sistemas monoprogramados',0.2), (u05,'Partições fixas',0.2)]
== CG bloco-02 'introducao opengl' (07/09: u01 via 1.2 Conceitos com OpenGL; hoje: sem unidade -> herda bloco-03 u02)
  hoje (1.2 Conceitos so com o codigo, M1)                   -> unit=(nenhuma)  conf=0.04 ['winner_score=0.20','weak-topic','ambiguous'] | top3=[(u04,'2D, 3D (mão direita)…',0.2), (u04,'Desenho de Linhas',0.2), (u04,'Preenchimento de Polígonos',0.2)]
  OpenGL e OpenGL 3D de volta em 1.2 Conceitos (estado 07/09) -> unit=unidade-01 topico=Conceitos  conf=1.00 ['winner_score=3.37'] | top3=[(u01,'Conceitos',3.366), (u04,…,0.2), (u04,…,0.2)]
  OpenGL e OpenGL 3D em 1.4 Aplicacoes (ruling do user 11/09) -> unit=unidade-01 topico=Aplicações conf=1.00 ['winner_score=3.37'] | top3=[(u01,'Aplicações',3.366), (u04,…,0.2), (u04,…,0.2)]
  so 'OpenGL' em 1.4 Aplicacoes                              -> unit=unidade-01 topico=Aplicações conf=1.00 ['winner_score=3.37']
```

## 5. Perguntas, em ordem

1. **Causa raiz.** Está confirmada em cada caso? Há terceira causa que eu não vi (TCC 1 sem gold; o `herdada_do_vizinho` como
   desenho; `reconciliada_do_bloco` nas lâminas de sockets, que em 07/09 eram `ambiguous` e hoje têm score 39)?
2. **Correção: motor ou curadoria?** Candidatos; diga qual é causa raiz e qual é sintoma, e o que cada um arrisca regredir:
   F1 `filter_terms` passa a rejeitar termo doado igual a, ou contido em, alias MANUAL de tópico de outra unidade (cortaria
   "Comunicação entre Processos" no SO; "Pipes" não). F2 exclusividade ampliada: termo doado que já é alias em outro tópico
   (manual ou LLM) sai. F3 curadoria: sidecar manual do SO tira as 2 doações de 3.1 (0 código). CG: F4 "OpenGL" como alias
   de 1.4 no sidecar manual, conforme o ruling (0 código); F5 reverter o M1 em 1.2; F6 regra de motor "bloco fraco com
   `auto_unit_slug` não herda do vizinho". Diga também que variante medir antes: só "Comunicação entre Processos" fora? só "Pipes"?
3. **Teste vermelho.** Forma mais barata que falha hoje e passa com a correção: unitário em `filter_terms` (termo contido em alias
   manual de outra unidade), unitário em `_assign_timeline_block_to_topic` com o bloco-09 como fixture, ou os dois?
4. **Remedição para o gate.** O que basta para declarar "sem regressão em unidade": rodar o diff 07/09 × hoje nos 8 tutores
   (unidade E subunidade) depois da correção, com a régua de `calibra_fila_como_regua`? O que mais pode ter regredido sem gold
   (FR 22, LR 7, TCC 1)?
5. **Risco.** O vocab LLM está nos 8 tutores desde 11/09; quantos outros blocos podem ter mudado de unidade sem gold para acusar?
   Que medição barata (0 chamadas) responde isso antes de a correção entrar?
