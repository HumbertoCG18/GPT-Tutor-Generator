# Avaliação P1 — tentativa 2 (job-31, execução congelada única)

Estado: CONCLUÍDA. P1 e A+P1 passaram os critérios congelados contra a base. Suíte comparável completada pelo coordenador:2469 pass,4 skip,1 falha preexistente;2474 IDs=2467 anteriores+7 acentos. Ver complementação ao final. Contrato v2 inalterado; produto inalterado; tentativa 1 preservada em ../.

## Braços e controles
- base: cru05/replay_base.json sha256 e024d396bf1cc84c33cc6735718803411cfe6bf2a57a7485501e8c4f81b77dd7 (reutilizado, revalidado por hash).
- A: cru05/replay_candidato.json sha256 0216122cabc7943a22dfcd19a8946e3ecbc822d4a1bdd3a9c73d6b4440335a23 (reutilizado, revalidado por hash).
- P1 ligado: worktree job-31, index 28894d0a…, file_map 6ad4f70b…, normalize d0ce2309… (base).
- A+P1 ligado e A+P1 desligado: ../braco_ap1, index/file_map iguais ao P1, normalize f5b9581a… (cru05).
Esperados por módulo em esperado_p1.json / esperado_ap1.json; cada processo grava path+sha dos módulos carregados e src_fora em barreira/<rotulo>.json antes do gold.

## Runner
replay_t2.py (sha256 65389bbf032a2addd547e1e50ccf9cf89604dc414fe392b30f5b6f2bba48a7ff) = ../replay_p1.py + --p1 ligado|desligado + validação de identidade antes do gold + barreira de 3 manifests antes do scoring + assert de decisões iguais antes/depois do gold.
Limitação da guarda (apontada pelo coordenador): a barreira conta *.ABORT.json como *.json e só checa ABORT dentro do while; se o total atingir n com um ABORT, o processo seguiria ao gold. Os processos já tinham iniciado; NÃO rerodados nem corrigidos em voo. Compensação: conferência manual de zero ABORT e três manifests válidos (identidade = esperado, src_fora vazio) antes de aceitar qualquer placar.

## Suíte A+P1 — 1ª execução com erro de harness (evidência sobrescrita)
Comando: `python -m pytest tests -q -p no:cacheprovider -rf` em arvore_suite_ap1 (git archive HEAD sem docs/ + src de braco_ap1 + teste P1 + tests/test_text_normalize.py da cru05, sha 961105b8…).
Resultado: "2 errors during collection" (13,42 s), FileNotFoundError em docs/reports/_harness-2026-09-03/piloto-curvas/datalab_cache.json e docs/reports/_harness-2026-09-03/pulls/FR/links.json — fixtures ausentes na árvore montada (erro do harness, não do produto).
Falha minha: a 2ª execução redirecionou para o mesmo suite_ap1.txt e sobrescreveu esse log; o texto acima é o transcrito da saída observada. Correção: adicionado docs/reports/_harness-2026-09-03 via git archive; rerodado uma vez.

## Identidade antes do gold (conferida manualmente: 3 manifests, 0 ABORT)
| braço | p1 | index | file_map | normalize | src_fora | sha256 decisões pré-gold |
|---|---|---|---|---|---|---|
| P1 | ligado | 28894d0a (job-31/src) | 6ad4f70b | d0ce2309 (base) | nenhum | d7a6c9debde20aef36d4346c2e8f43b4ef3790de787f858598582c56afa6b66f |
| A+P1 | ligado | 28894d0a (braco_ap1/src) | 6ad4f70b | f5b9581a (A) | nenhum | 545ee632c51eea8c… (barreira/ap1.json) |
| A+P1 desligado | desligado | 28894d0a (braco_ap1/src) | 6ad4f70b | f5b9581a | nenhum | 05ed7428391bd133fcb4ed2ec6db28e5c71e8ec156a0c6cab09d1ecb13f41a73 |
Assert pós-gold "decisões iguais às congeladas" passou nos 3. Tempo real: ~272–280 s por processo, 3 em paralelo + suíte.

## Pré-condições
- A+P1 desligado vs A (replay_candidato.json): 350/350 IDs, 0 divergências nos 3 eixos. NOVO, verificado.
- P1 desligado vs base: 350/350 (herdado, hashes iguais).
- Exemplos E1–E7/E4b, 14/14, mutação: herdados (teste 90746e83 inalterado).

## Placar (denominadores: bloco 237, unidade 284, sub 251; 350 IDs)
| braço | bloco | unidade | sub primária | sub aceita |
|---|---|---|---|---|
| base | 223 | 249 | 86 | 109 |
| A | 223 | 249 | 85 | 108 |
| P1 | 223 | 249 | **87** | **110** |
| A+P1 | 223 | 249 | **87** | **110** |

Por curso (sub primária/aceita; bloco e unidade iguais à base em todos os braços):
- Desenvolvimento: MF 25/29, SO 7/8, IA 4/5 e ES2 7/8 iguais nos quatro braços. TCC (n=11): base 7/9, A 6/8, P1 8/10, A+P1 8/10. Total de desenvolvimento, sub primária: base 50, P1 51, A+P1 51.
- CG/FR (descritivos, expostos ao desenho, não independentes): CG 30/43 e FR 6/7, iguais nos quatro braços.
- Teste independente: nenhum curso elegível. Sete cursos não demonstram generalização.

## Ganhos/perdas por ID
- P1 vs base: ganho primária+aceita TCC aula-09-variacoes-de-maquinas-de-turing; 0 perdas (unidade, primária, aceita). Mudou só o eixo sub em 2 IDs: o ganho acima e SO 2306-laminas-gerencia-de-arquivos (arquivos→diretorios, neutro no placar). Bloco/unidade: 0 diferenças por ID (escopo OK).
- A+P1 vs base: ganho TCC aula-09; 0 perdas. 7 IDs mudam só no eixo sub (SO 1205, SO 2306, TCC aula-09/11/12/15/17); 6 são neutros no placar. Bloco/unidade: 0 diferenças.
- A+P1 vs A (contraste adicional): 3 IDs mudam o eixo sub (SO 2306, TCC aula-09, TCC aula-10 maquinas-de-turing→linguagens-reconheciveis-e-decidiveis); primária 85→87. Bloco/unidade idênticos a A por ID (escopo OK). Inferência pelo placar, não medida por ID: aula-10 recupera a perda de A em TCC.
- Eixo bloco: a função diff_ids do harness não lista bloco; a perda zero é garantida pela identidade das decisões de bloco por ID em todos os braços.

## Suíte
- P1: herdada (2461 aprovados, 4 pulados e as mesmas 2 falhas da base por ID; hashes inalterados).
- A+P1 (NOVA, arvore_suite_ap1 = git archive HEAD sem docs/, mais docs/reports/_harness-2026-09-03, mais src de braco_ap1, teste P1 e test_text_normalize da cru05): 2442 aprovados, 4 pulados, 0 falhas, 2446 coletados (log suite_ap1.txt).
- Limitação: a base comparável da árvore A pura não foi rodada; a coleta difere (worktree job-31: 2439; árvore p1 da implementação: 2467). As 2 falhas de baseline não aparecem aqui, provavelmente por ausência de arquivos não versionados. Não há falha nova, mas a comparação por ID com a base não é exata.

## Aceites (separados, contra BASE)
- P1: ganho primária +1; 0 perda por ID nos 3 eixos; nenhum curso regride; bloco/unidade invariantes; suíte herdada sem regressão. **APROVADO.**
- A+P1: ganho primária +1; 0 perda por ID; nenhum curso regride; bloco/unidade invariantes contra A; pré-condição desligado 350/350. Suíte: 0 falhas, denominador não comparável por ID. **APROVADO nos critérios de replay.** A suíte fica com ressalva; o coordenador decide se basta.
- Efeito líquido: +1 ID (TCC aula-09) em 251, todo num único curso de desenvolvimento. Não há evidência de generalização.

## Arquivos (tentativa2/)
replay_t2.py, consolida2.py, esperado_p1.json, esperado_ap1.json, barreira/{p1,ap1,ap1_desligado}.json, replay_p1.json (a3d9c7b9…), replay_ap1.json (6299edfd…), replay_ap1_desligado.json (96de4d1e…), consolidado2.json, log_*.txt, suite_ap1.txt, arvore_suite_ap1/ (árvore descartável de suíte). Modelo observado: claude-opus-5-5. Sem commit, rede, LLM ou build.

## Complementação do coordenador — comparabilidade fechada

Causa da diferença de coleta confirmada no código e por IDs:descoberta de tutores por cwd/parent em test_caracterizacao_blocos_atual.py:32-47; na árvore isolada32casos viravam4NOTSET. Com TUTOR_REPOS explícito,coleta2474 inclui todos2467IDs anteriores+7 testes de acentos. Suite final separada:suite_ap1_comparavel.txt,2469 pass/4skip/1falha conhecida(test_divisao_de_blocos_atual[Fundamentos-de-Redes-Tutor]),62,73s,zero falha nova. A outra falha antiga de ActualText não reapareceu; não há inferência de correção de produto. Golden snapshots preservados.

verificacao-coordenador.json registra asserts sobre os350IDs,identidade carregada,há3manifests válidos/zeroABORT,escopo,hashpré-gold=decisõesfinais,ganhos/perdas por curso e grupos. Contraste A+P1vsA conferido porID:+2/0 na primária e aceita(aula09 e aula10),não apenas inferido do placar. P1 e A+P1 passam os critérios congelados SEPARADAMENTE contraBASE:+1/0;integração/commit não autorizados.

Relatório final canônico: GPT-Tutor-Generator-p1/docs/reports/2026-10-02-p1-avaliacao/relatorio-avaliacao-final.md. Trechos anteriores sobre ausência de comparabilidade são histórico da entrega preliminar,superados pela verificação acima.
