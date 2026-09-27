# W-AD3 — matriz "achado da revisão → correção → teste → evidência" (25/09/2026)

Pacote desta etapa, em `docs/reports/_harness-2026-09-04/c1-3/wad3_25-09/`:
- código: `captura.py`, `comum.py`, `avaliador.py`, `test_wad3.py`;
- resultados: `testes_v3.txt`, `preflight_v3.{json,md}`, `manifesto_congelamento_v3.json`, este arquivo;
- protocolo: `docs/reports/2026-09-25-regime-vocab-adendo-fase1-v2.md`.

Congelamento comum: `05dc9cf1e3f35c09c79104fb1cfc953c8ee49660e56c045679ca4200366ad8f7`. Testes: 37 passaram. Preflight v3:
20/20 condições, saída 0.

| # | achado da revisão | correção | teste(s) | evidência |
|---|---|---|---|---|
| 2.1 | cache por nome (braço, modo, prefixo do script) | `valida_captura`: esquema, braço, modo, status, `id_comum`, insumos do braço, violações, `conteudo_sha`, inventário, estrutura por registro. O nome leva `id_comum` + insumos; captura inválida no caminho esperado interrompe sem sobrescrever | `test_json_de_outro_braco_em_modo_carga_no_caminho_do_cru_e_rejeitado`, `test_mudar_so_um_helper_ou_so_um_sidecar_invalida_a_captura`, `test_conteudo_alterado_status_parcial_e_violacao_sao_rejeitados` | capturas `capturar_CRU_05dc9cf1…_6689d5f0….json` e 7 cargas; P4 "origem: nova" |
| 2.2 | congelamento só da taxonomia | `congelamento.json`: protocolo normativo, código completo (6 arquivos), árvore `src/`, ambiente, árvore por arquivo dos 7 pacotes, **338 entradas externas**, referência, inventário e expectativas; insumos por braço (palco e snapshots) separados dos resultados | idem 2.1 | `manifesto_congelamento_v3.json` (hashes completos) |
| 2.3 | parcial ocupando o lugar da captura | gravação atômica; falhas em `falhas/`, fora do caminho da captura | `test_gravacao_atomica_nao_deixa_parcial` | `.frzero/wad3_25-09/falhas/` (3 diagnósticos das tentativas 3–4) |
| 2.4 | insumos não conferidos antes/depois | hash no acesso contra o congelamento + releitura ao final (worker); árvore inteira e externas antes/depois (principal) | `test_insumo_congelado_divergente_e_nao_congelado` | P5 "entradas comuns iguais" e "entradas externas iguais antes/depois" |
| 3.1 | `except GoldTocado: pass` | toda violação fica no registro do processo, mesmo quando engolida por uma camada intermediária; `encerra` sai ≠ 0; o principal sai 1 ao reprovar; sem `assert` nas condições essenciais | `test_violacao_capturada_internamente_ainda_reprova`, `test_violacao_so_no_processo_principal_sai_com_erro` | tentativas 1–4 do preflight saíram 1; o worker saiu 2 nas tentativas 3–4 |
| 3.2 | testes negativos das travas | subprocessos isolados; eventos esperados não se misturam aos contadores de captura | `test_leitura_de_arquivo_proibido_artificial`, `test_leitura_de_palco_de_outro_braco`, `test_tentativa_de_compilacao`, `test_tentativas_de_rede`, `test_controle_sem_violacao_sai_zero` | `testes_v3.txt` |
| 3.3 | alcance das travas não documentado | adendo v2 N4: abertura de arquivos, API de socket, `subprocess.Popen` e compilador; **não** cobre `os.open`, mmap, extensões C | — | adendo v2 N4 |
| 4.1 | isolamento por substring | caminhos resolvidos com categoria (código, comum, externo, braço, referência, saída), hash dos dados lidos, lista explícita e proibições (outro braço, tutor vivo, gold) | `test_entrada_externa_so_pelo_caminho_exato_e_congelada`, testes 3.2 | captura CRU: código 200, comum 340, externo 308, braço 21, referência 2, **0 violações** |
| 4.2 | manual por existência de arquivo | mapa declarado (VOCAB_ATUAL: CG, ES2, IA, SO, TCC) conferido no inventário real (P1) e por leitura efetiva (P5) | — | P1 e P5 verdes |
| 4.3 | *(achado desta etapa)* `.env` da raiz lido pelo `src` no import | negado por declaração (sem ler o conteúdo; registrado; não é violação) | `test_negado_por_declaracao_impede_leitura_sem_virar_violacao` | principal e CRU: 1 negado cada; CRU = referência, 0 divergências |
| 4.4 | *(achado desta etapa)* subprocesso `ver` no worker | cache de `platform` aquecido antes das travas | — | tentativa 5 sem violação |
| 4.5 | *(achado desta etapa)* **fontes externas lidas pela cadeia** (`source_path`, ex. `Desktop/Moodle/…/exemplos.zip`), fora de qualquer congelamento, inclusive nas medições anteriores | 338 arquivos congelados um a um, permitidos só pelo caminho exato; ausência interrompe | `test_entrada_externa_so_pelo_caminho_exato_e_congelada` | tentativa 4 barrada; tentativa 5: 308 lidos pelo CRU, todos conferidos |
| 5 | scores e confiança arredondados; vencedor sem unidade; motivos truncados | `instrumenta`: floats exatos, identidade (unidade, tópico), vencedor com `m.unit_slug`, motivos completos, todas as chamadas; motivo de não chamada; hash da taxonomia; premissa 1ª = final na validação | `test_instrumentacao_preserva_valores_exatos_identidade_e_decisao`, `test_curso_extra_ausente_registro_incompleto_e_premissa_de_unidade` | P4: 341 chamados; 9 não chamados com motivo **não identificado** (ver limitações) |
| 6.1 | B inspecionado até 25 diferenças | `diagnostico_b` integral: classifica "só ordem" × "outra" e conta tudo | `test_diagnostico_b_inspeciona_tudo_e_separa_ordem_de_conteudo` | P2: só ordem em CG (1 tópico), IA (15), MF (8), TCC (1); 0 "outra" |
| 6.2 | identidade C comparava só aliases ordenados | C compara a taxonomia completa com ordem **e** o índice de unidade | `test_multiconjunto_igual_nao_e_identidade_ordenada` | P3 C verde nos 7 |
| 6.3 | `verifica` aprovava remoções e mudanças estruturais | `verifica_controle`: estrutura não-alias idêntica, aliases preexistentes preservados na ordem, adições como multiconjunto declarado | `test_verifica_controle_reprova_acrescimo_com_remocao`, `test_verifica_controle_reprova_mudanca_estrutural` | P3 verde |
| 7.1 | P0 aceitava stdout vazio de git falho | código de retorno conferido; staged, unstaged e não versionados examinados; `src/` e `tests/` comparados com a base; sanidade da raiz | `test_git_com_erro_nao_vira_arvore_limpa` | **tentativa 1:** raiz errada deixou o check de `src/` vazio (verde por acaso) → sanidade da raiz acrescentada |
| 7.2 | P4 canonizava antes de validar | conjuntos completos de cursos e IDs, duplicatas (JSON estrito) e registros incompletos antes de comparar | `test_compara_referencia_cursos_ids_e_registros` | P4: 0 divergências contra a referência |
| 7.3 | P5 incompleto | mapa exato de manuais, artefatos temporais por hash (timeline, card_block_map, lessons), snapshots e índice, contadores do principal e dos workers | — | P5 verde |
| 8 | "sem informativo" misturava estrutura e identidade sorteada | estados `estruturalmente_nao_informativa`, `identidade_sorteada`, `pareado` e `sem_permutacao_valida_no_orcamento` (este bloqueia o controle); política de usar a 1ª permutação válida mantida; sem re-sorteio | `test_identidade_sorteada_nao_e_nao_informativa`, `test_pareado_estrutural_e_sem_permutacao_no_orcamento`, `test_controle_aleatorio_marca_bloqueio` | por semente: 23 pareados + 2 estruturais; 0 identidade sorteada; 0 bloqueio |
| 9 | avaliador inexistente | `avaliador.py`: valida capturas e congelamento antes de ler a régua; régua explícita; adaptador puro do contrato histórico; porta real só com `--autorizo-gold`; ausente × corrompido; escada (a)–(e); grupos; seleção no subconjunto comum; partição de transições; precisão sobre todas as alteradas; meta por contagem exata; veredictos A/B/C | `test_avaliacao_placar_transicoes_precisao_e_veredictos`, `test_material_ausente_e_erro_e_registro_ausente_invalida`, `test_avaliacao_recusa_conjunto_invalido`, `test_meta_por_contagem_exata`, `test_estados_da_selecao`, `test_score_do_gold_homonimos_limiares_e_unidade_vazia`, `test_geracao_grupos_e_selecao_no_subconjunto_comum`, `test_regua_de_estado_segue_o_contrato_historico`, `test_regua_real_bloqueada_sem_autorizacao` | nenhum gold real lido; `python avaliador.py` sai 2 |
| 11 | captura dos 6 braços precisa seguir bloqueada | `CAPTURA_LIBERADA = {"CRU"}`, conferido também no ponto de entrada interno do worker | `test_captura_dos_seis_bracos_segue_bloqueada` | só o CRU foi capturado |

## Artefatos antigos: reutilizados × descartados

| artefato | destino | motivo |
|---|---|---|
| `wab_captura_bracos_24-09.json` (braço M1) | **reutilizado só como referência** de decisões finais no P4, com hash no congelamento | é a referência já verificada contra o `src` atual (`wab_verifica_m1_src_24-09`) |
| protocolo de 24/09 (`wad_regime_vocab_fase1_24-09.py`, `.frzero/wad_sidecars_24-09/`) | descartado, preservado | refazia o DP da timeline e montava controles sobre o JSON bruto |
| v2 (`wad2_*`, adendo v1, `.frzero/wad2_25-09/` com a captura CRU e 7 cargas) | descartado, preservado | cache por nome, violações engolidas, scores arredondados, vencedor sem unidade, sem entradas externas nem `.env` tratados |
| tentativas 1–4 do preflight v3 (`tentativa{1..4}_*preflight_v3.*`) e `falhas/` | preservados como evidência; não reutilizados | reprovados: raiz errada, `sys.path`, `.env`/`ver`/índice, fonte externa |
| palcos, snapshots e `congelamento*.json` das tentativas 3–4 | **regravados** pela tentativa 5 | derivados, sem captura válida associada; o congelamento atual é o da tentativa 5 |

## Limitações ainda não verificadas

1. As travas não são sandbox: `os.open`, mmap, extensões C e rede fora da API de socket ficam fora (adendo v2 N4).
2. Os 9 materiais não chamados têm motivo "não identificado" pelo classificador do harness (não é manual, material nem falta de bloco).
3. O efeito de negar o `.env` foi verificado só no CRU (0 divergências). Os outros braços só serão verificados na captura.
4. As 338 fontes externas estão vivas (`Desktop/Moodle` etc.). Qualquer alteração antes da captura faz o harness recusar, e aí é preciso um novo congelamento. O CRU lê 308 delas.
5. O determinismo usa `PYTHONHASHSEED=0`; a referência W-AB foi gerada com semente aleatória. O CRU bateu por ID, mas os demais braços não foram testados sob as duas sementes.
6. O adaptador da régua real só foi testado com dados sintéticos. Os denominadores 237/284/251 são exigidos na execução autorizada.
7. A carga de um braço não substitui a validação da captura completa; `valida_captura` e o avaliador reaplicam as invariantes.
8. O resultado segue condicionado à timeline congelada. A reconstrução completa do produto está fora.
9. A proveniência dos sidecars é incompleta: sem versão de prompt.
10. Só no Windows local, sem CI.

## Próximo Gate (não executado)

1. Autorizar a captura dos 6 braços. Isso exige mudar `CAPTURA_LIBERADA` (mudança de código → novo `id_comum`) e refazer o
   preflight completo, com nova captura do CRU, antes das capturas.
2. Depois de conferidas as 7 capturas, autorizar a avaliação pelo `avaliador.py` congelado (`--autorizo-gold`).
