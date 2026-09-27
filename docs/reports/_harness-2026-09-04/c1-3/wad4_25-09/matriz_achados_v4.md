# W-AD4 — matriz de achados da 3ª revisão, evidências e conclusão (25/09/2026)

Protocolo: `docs/reports/2026-09-25-regime-vocab-adendo-fase1-v3.md` (bloco NORMATIVO, `protocolo_sha` `bad95c56…`).
Resultados: `.frzero/wad4_25-09/`. A v3 (`../wad3_25-09/`, `.frzero/wad3_25-09/`) e suas tentativas ficaram intactas.
Nada leu gold. Não houve captura dos seis braços não-CRU, rede, LLM, recompilação, mudança em `src/`, commit nem push.

**Conclusão: pronto para pedir o Gate de captura** (seis braços não-CRU). As condições estão na última seção. O Gate de
avaliação continua separado, e suas pré-condições estão listadas como bloqueantes daquela etapa, não desta.

## 1. Achado → teste que reproduz → correção → evidência

Fase vermelha: `test_defeitos_v4.py` rodado contra o código v3 copiado → `testes_v4_vermelho.txt` (23 falhas; 1 passou
porque a trava suportava somente leitura e o defeito estava na configuração, reproduzido pelo teste seguinte da
tabela). Fase verde: `testes_v4.txt`, 68/68 (26 de defeito + 42 herdados e novos em `test_wad4.py`).

### Bloqueio 1 — congelamento não conferido contra código e ambiente executados

| Achado | Teste | Correção | Evidência |
|---|---|---|---|
| Código alterado depois do preflight passava | `test_codigo_alterado_depois_do_preflight` | `K.verifica_codigo` antes dos imports do produto e no fim (worker e principal) | verde; P5 "código do harness, helpers e src/ iguais antes/depois" |
| Módulo de outra raiz/checkout passava | `test_import_de_outra_raiz` | `K.verifica_modulos`: origem dentro de `src/` e hash por arquivo depois dos imports | verde; 59 módulos `src.*` conferidos no preflight |
| Bytecode em cache podia divergir do fonte | estratégia (sem teste unitário) | relançamento com `-B -X pycache_prefix=<vazio isolado>`; área vazia conferida | P0 processo OK; `pycache_vazio` vazio depois da execução |
| Ambiente herdado do terminal (config e credenciais) | `test_ambiente_relevante_divergente` | ambiente montado do zero (`ambiente_controlado`), conferido (`verifica_ambiente`); só nomes de variáveis de sistema registrados | verde; congelamento guarda valores declarados + 22 nomes |
| Worker herdava `os.environ` mutado pelo import do produto (`TESSDATA_PREFIX`) — **achado desta execução** | `test_worker_recebe_ambiente_declarado_mesmo_com_os_environ_mutado` (vermelho em `tentativa1_teste_vermelho.txt`) | `roda_worker` passa o ambiente declarado montado a partir do ambiente de ANTES dos imports | tentativa 1 parou antes de capturar; tentativa 2 aprovada |
| Descritor de insumos alterado sem mudar o identificador | `test_descritor_de_insumos_alterado_sem_atualizar_identificador` | `valida_congelamento` confere normativo → `id_comum` e descritor → `insumos_braco` | verde |
| Validação histórica dependia do checkout | `test_validacao_historica_sem_checkout_original` | `valida_historica` só com captura + congelamento | verde; as 8 capturas desta execução revalidadas assim |
| Código gravável na configuração real das travas | `test_codigo_somente_leitura_na_configuracao_real`, `test_escrita_em_codigo` | `travas_worker`/`travas_principal`: código somente leitura | verde |

### Bloqueio 2 — validador aceitava registros fora dos invariantes

| Achado | Teste | Correção | Evidência |
|---|---|---|---|
| Captura sem `verificacoes`/`por_curso` passava | `test_verificacoes_ou_por_curso_ausentes` | expectativas tiradas do congelamento, campos obrigatórios | verde |
| Manual indevido no CRU | `test_manual_indevido_no_cru` | `manual_carregado` == mapa congelado do braço | verde; P5 manual = mapa |
| Hash de taxonomia/índice errado com `conteudo_sha` recalculado | `test_hash_de_taxonomia_ou_indice_errado_com_conteudo_sha_recalculado` | por curso, igual ao snapshot congelado do braço | verde |
| Curso/ID interno diferente da chave | `test_curso_ou_id_interno_diferente_das_chaves` | `valida_registro(r, sig, eid)` | verde |
| Pontuações em texto, candidato duplicado, sem vencedor, `chamado` não booleano, score infinito | `test_pontuacoes_string_score_nao_finito_candidato_duplicado` | `valida_chamada` estrita; `sha_json(allow_nan=False)` | verde |
| Pino manual fora da taxonomia virava erro | `test_saida_fora_da_taxonomia_nao_e_erro_estrutural` | estrutura ≠ correção | verde |
| Captura não-CRU em cache era aceita sem autorização | `test_captura_nao_cru_em_cache_sem_autorizacao` | autorização antes de lançar, de ler cache e de aceitar | verde |
| Fixture de teste incompleta escondia defeitos | `test_fixture_completa_e_valida` | fixtures completas nos dois arquivos de teste | verde |

### Bloqueio 3 — avaliador dependia de carregadores e mapeamentos fora da cadeia

| Achado | Teste | Correção | Evidência |
|---|---|---|---|
| Régua lida por módulos históricos importados, com resolução implícita de caminho | `test_carregador_local_segue_o_historico_com_bytes_conferidos`, `test_carregador_local_recusa_bytes_manifest_e_pendencias_divergentes`, `test_import_nao_carrega_produto_nem_avaliacao_historica` | cópias locais identificadas (`HISTORICO`), caminhos explícitos no congelamento, bytes conferidos pelo blob git antes de interpretar | verde; descritor sem pendências (§4) |
| `gold_id` ausente de `eid_de` virava material ausente | `test_gid_ausente_versus_none_explicito` | linha sem decisão de mapeamento = erro; `None` explícito = ausente | verde |
| Origem ambígua resolvida por `hits[0]` | `test_origem_ambigua_e_rejeitada` | unicidade obrigatória | verde; `diagnostico_origens_v4.txt`: 0 origens repetidas nos 14 manifests |
| Mesmo `eid` para dois `gold_id`; distribuição por curso não conferida | `test_duplicidade_de_eid_e_distribuicao_por_curso` | `valida_regua` por curso e total | verde |
| B vetado pela subunidade aceita | `test_veredicto_b_nao_veta_por_subunidade_aceita` | B nos 3 eixos oficiais; aceita relatada à parte | verde |
| Não chamado recebia elegibilidade com a unidade final | `test_material_ausente_ou_nao_chamado_sem_elegibilidade_ficticia` | `geracao_do_material`: "não aplicável" | verde |
| Agregados sem origem por ID | `test_registros_por_id_sao_a_origem_dos_agregados` | registros por (material, eixo) e por transição; somas conferidas | verde |
| Recaptura do CRU não amarrada à referência publicada | `test_cru_que_nao_reproduz_a_referencia_por_curso_recusa` | `confere_referencia_cru` por curso e eixo | verde |

### Correções delimitadas

| Achado | Teste | Correção | Evidência |
|---|---|---|---|
| Arquivo lido, alterado e reaberto | `test_arquivo_lido_alterado_e_reaberto` | toda abertura confere o hash | verde |
| Conteúdo restaurado antes do fim apagava o rastro | `test_conteudo_restaurado_antes_do_fim_preserva_violacao` | violação registrada no acesso | verde |
| Arquivo lido e removido | `test_arquivo_lido_e_removido` | `insumo_desaparecido` | verde |
| Caminho sensível autorizado por aparecer em `source_path` | `test_caminho_proibido_como_source_path_na_preparacao` | `checa_preparo` antes de ler/hashear | verde |
| Permissão de subprocesso aberta em exceção e genérica | `test_permissao_de_subprocesso_fecha_em_excecao` | `comandos({...})` nominal com `finally` | verde |
| Justificativa do `.env` ("só segredos") | adendo v3 N4 | negado sem leitura; o carregador não sobrescreve variáveis presentes; o ambiente declarado cobre as leituras do caminho medido | `negados` = `.env` no principal e nos 8 workers |

## 2. Execução (sem gold)

- **Tentativa 1** (`tentativa1_env_mutado_preflight_v4.{json,md,log}`, congelamento em `.frzero/wad4_25-09/tentativa1/`,
  falha em `falhas/capturar_CRU_1790366173.json`):
  - 10 condições OK, até P2;
  - o worker do CRU recusou a pré-execução por `TESSDATA_PREFIX` não declarado e parou antes de capturar;
  - causa: `src/utils/helpers.py` grava a variável no import e o worker herdava o ambiente do principal.
- **Tentativa 2** (`preflight_v4.{json,md}`): **23/23, saída 0, 247 s**.
  - Congelamento `b3254509f4efcf700a6d5f0f5a3488c9bfb1b41f0765081f1560f48d175da8ef`: 7 pacotes, 338 entradas externas,
    136 arquivos de `src/`, 7 arquivos de código.
  - CRU recapturado (`capturar_CRU_b3254509f4efcf70_6689d5f05bf10fc3.json`, conteúdo `afba449f…`): igual à referência
    W-AB por ID (350 materiais, 0 divergências), 341 chamados, 9 não chamados, unidade da 1ª passada = final.
  - Carga dos 7 braços: manual = mapa, temporais iguais, unidades do motor iguais, taxonomia e índice = snapshots, e
    não-CRU sem leitura da taxonomia congelada.
  - Revalidação independente (`valida_historica`) das 8 capturas: 0 problemas. Código e `src/` iguais ao congelado
    depois da execução.

## 3. Os nove não chamados do CRU

Todos com motivo `nao_identificado` no harness, `sub` final vazio e motivo de subunidade `meta-material`, isto é, o
material de apresentação é tratado pelo produto como meta antes do seletor.

| curso | ID | unidade final | motivo da subunidade |
|---|---|---|---|
| CG | cronograma2026-2 | unidade-01-introducao-ao-processamento-grafico | meta-material:meta |
| CG | planodeensino-4645z-04-fundamentos-de-computacao-grafica | unidade-01-introducao-ao-processamento-grafico | meta-material:meta |
| ES2 | plano | unidade-01-arquitetura-de-software | meta-material:meta |
| FR | plano-de-ensino-20262 | unidade-01-introducao-a-redes-de-computadores | meta-material:meta |
| MF | plano | unidade-01-metodos-formais | meta-material:meta |
| SO | apresentacao-da-disciplina | unidade-01-introducao-ao-estudo-de-sistemas-operacionais | meta-material:meta-por-conteudo |
| SO | plano-de-ensino | unidade-01-introducao-ao-estudo-de-sistemas-operacionais | meta-material:meta |
| SO | programa | unidade-01-introducao-ao-estudo-de-sistemas-operacionais | meta-material:meta-por-conteudo |
| TCC | plano-de-ensino | unidade-01-conjuntos-enumeraveis-e-funcoes-recursivas | meta-material:meta |

O rótulo `nao_identificado` do harness é conservador: a evidência (`meta-material` nos motivos) indica desvio de
meta-material. A classificação do harness não foi alterada depois de ver o dado. Na avaliação, esses materiais têm
elegibilidade "não aplicável".

## 4. Inventário da régua congelada (blob IDs do índice do git; nenhum arquivo aberto)

| papel | curso | caminho | blob |
|---|---|---|---|
| gold_units | ES2 | `tests/fixtures/eval/gold_units_ES2.csv` | `2bab8a260eefde20731c5a4b48e8c5189dea774e` |
| gold_units | IA | `tests/fixtures/eval/gold_units_IA.csv` | `8a3ecaeac4302d128ac877f7b96407d44edec905` |
| gold_units | MF | `tests/fixtures/eval/gold_units_MF.csv` | `b379a6a0377f16c69c1934fcb538a1af9f4de0bd` |
| gold_units | SO | `tests/fixtures/eval/gold_units_SO.csv` | `3fe893be9300b2d45bf976f791d1992a50fd7cee` |
| gold_units | TCC | `tests/fixtures/eval/gold_units_TCC.csv` | `1bdd8cdf9121dcc27b9a4eeac59705b5711b7ae9` |
| ground_truth | CG | `docs/reports/ground_truth_CG.csv` | `00d8a68768fd54129147229f1995565958bf77c3` |
| ground_truth | ES2 | `docs/reports/ground_truth_ES2.csv` | `79b677b9e83cd24dd92644994430c4b26f5777bf` |
| ground_truth | IA | `docs/reports/ground_truth_IA.csv` | `3375483476ea655a307906f43b1ff82e2a59b3bf` |
| ground_truth | MF | `docs/reports/ground_truth_MF.csv` | `e356ecfb57237b109917a79d193da3f8c7a2cad0` |
| ground_truth | SO | `docs/reports/ground_truth_SO.csv` | `3cbd5c6e7c8679564f23fd1b8d66443906d52442` |
| ground_truth | TCC | `docs/reports/ground_truth_TCC.csv` | `167c1dbe6237cbe2af7610bdacfafd4e420505a0` |
| herancas_csv | CG | `c1-3/herancas_CG_15-09.csv` | `7e61a1598158c479dd2d2b0ebd1bc9a34a727b80` |
| herancas_csv | ES2 | `c1-3/herancas_ES2_15-09.csv` | `2b2382a7365f3ed3ce309c469df3ec51820761eb` |
| herancas_csv | FR | `c1-3/herancas_FR_15-09.csv` | `a9077c8bb23ee79ba26062ad2dc3608446c1c71f` |
| herancas_csv | IA | `c1-3/herancas_IA_15-09.csv` | `36a04f9de5cf5b89664043b7efc524604c5a5872` |
| herancas_csv | MF | `c1-3/herancas_MF_15-09.csv` | `ae46ed184cc5e9d1f568985d27a202569d78d5a9` |
| herancas_csv | SO | `c1-3/herancas_SO_15-09.csv` | `0a045b97c3152864771d177b85bf6c11ee251d65` |
| herancas_csv | TCC | `c1-3/herancas_TCC_15-09.csv` | `b33d6f33bdaef7025b2daa9444466985e5db2dfa` |
| herancas_json | CG | `c1-3/herancas_CG_15-09.json` | `583036713ac63dbfe37f480235f31001be88b70e` |
| herancas_json | ES2 | `c1-3/herancas_ES2_15-09.json` | `40b7616629e74afc35f67238f204d5e643b804bf` |
| herancas_json | FR | `c1-3/herancas_FR_15-09.json` | `9a3afc33c4fbf8c7371b58801292e22ccc5d6f2a` |
| herancas_json | IA | `c1-3/herancas_IA_15-09.json` | `66e66547c951b7406351ca5c66d149bbb8a2568e` |
| herancas_json | MF | `c1-3/herancas_MF_15-09.json` | `a9b2110c583d8cd576a246caa037d7382feb5315` |
| herancas_json | SO | `c1-3/herancas_SO_15-09.json` | `54daeb7a94c96e53ba2479bc89d6d5f0bbf35bb6` |
| herancas_json | TCC | `c1-3/herancas_TCC_15-09.json` | `6981bd898c3b56e3cb5391a238c71d5b55c65b25` |
| material_gt | CG | `c1-3/wx_gold_v2_final_22-09/material_gt_CG.csv` | `a95694a8ac5c880f7d7905bf34ffaa337ce8b471` |
| material_gt | ES2 | `c1-3/wx_gold_v2_final_22-09/material_gt_ES2.csv` | `8aea65bf3ddb95b83e5c9a7f6039c741a9197cb7` |
| material_gt | IA | `docs/reports/material_gt_IA.csv` | `73fb9d43bd19b128e4e3cbaccd8e9bee2f481fcf` |
| material_gt | MF | `docs/reports/material_gt_MF.csv` | `9bd99a0a0337a38f2bfc5b73e17deb821eebb4ab` |
| material_gt | SO | `docs/reports/material_gt_SO.csv` | `9a066f3f8303ee638702df7cf06b92a45b90ce99` |
| material_gt | TCC | `docs/reports/material_gt_TCC.csv` | `2885a763a495e8bf64845ca4eefaa6b9270381ae` |
| subunit_gt | CG | `docs/reports/subunit_gt_CG.csv` | `60ea4f45d0e6c9d5600ca06dad12036448f904ac` |
| subunit_gt | ES2 | `docs/reports/subunit_gt_ES2.csv` | `ed9fd2e069e2beed534b8752c0fa90c7542bd169` |
| subunit_gt | FR | `docs/reports/subunit_gt_FR.csv` | `aa432f4f4c75a6447e9a2ed65a3eac28e8322505` |
| subunit_gt | IA | `docs/reports/subunit_gt_IA.csv` | `8d8c4698c3c11f748e78ac3fd116c7327e0ff020` |
| subunit_gt | MF | `docs/reports/subunit_gt_MF.csv` | `afe5edb76598591dbd140c4a873c402f974a751f` |
| subunit_gt | SO | `c1-3/wx_gold_v2_final_22-09/subunit_gt_SO.csv` | `99d2a8d8db2d99bc1986feffbf50629df2fb2644` |
| subunit_gt | TCC | `docs/reports/subunit_gt_TCC.csv` | `c55a7942edca9fccc7366c0b88ace7c09212ec2b` |

Manifests de referência (`.frzero/pacote_fontes_15-09/<curso>/manifest.json`, não são régua): sha256 no congelamento.
Código histórico cujas cópias locais o avaliador usa (blob do índice; cópia de trabalho = HEAD conferida por `git diff`):
`compara_herancas_15-09.py` `71429398…`, `mede_3eixos_12-09.py` `eb9a3c3b…`, `wx_regua_corrigida_22-09.py` `018fd8d1…`,
`wz_bloco_cobertura_22-09.py` `e248c063…`, `scripts/eval_entry_unit.py` `5b5fe800…`, `scripts/eval_ground_truth.py`
`e4cfa23e…`. Os caminhos reproduzem a escolha atual da resolução histórica `p(nome)` (pasta final v2 para
`material_gt` de CG/ES2 e `subunit_gt` de SO; o resto em `docs/reports`), lida no código sem executá-lo.

## 5. Nota histórica (sem reexecução)

As medições W-Z, W-AA, W-AB e KE não congelaram as entradas externas (`source_path` fora dos pacotes, por exemplo `.zip`
em `Desktop/Moodle`) e podem ter rodado com o `.env` carregado pelo produto no import. Elas não foram reexecutadas.

Evidência de equivalência para o caminho medido:
- o CRU v4, com as 338 entradas externas congeladas, o `.env` negado e o ambiente declarado, reproduz a referência W-AB por
  ID (350/0);
- o carregador do produto não sobrescreve variáveis presentes.

Isso vale para o CRU. Para os outros braços, a equivalência não foi medida contra a história, e não precisa ser: a Fase 1
compara braços dentro da mesma execução congelada.

## 6. Artefatos antigos

- **Reutilizados sem alteração, como insumo ou referência** (hash no congelamento):
  - pacotes `.frzero/wv_importacao_22-09/` e `.frzero/pacote_fontes_15-09/`;
  - captura de referência `.frzero/wab_captura_bracos_24-09.json`;
  - helpers `replay_bloco_21-09.py` e `replay_unidade_21-09.py`;
  - arquivos da régua (só blob IDs).
- **Código reaproveitado da v3 dentro de `captura.py`**: reconstrução, equivalências, controles, palcos, instrumentação,
  execução, comparação com a referência e snapshots. Única mudança de lógica: o registro dos temporais passou a cobrir
  todos os presentes, não só os lidos.
- **Não reutilizáveis** (esquema e `id_comum` diferentes, preservados como evidência): capturas, palcos, snapshots e
  congelamento de `.frzero/wad3_25-09/`, `preflight_v3.*`, `testes_v3.txt`, `manifesto_congelamento_v3.json` e a tentativa
  1 da v4.

## 7. Limitações

**Bloqueantes para o Gate de captura:** nenhuma.

**Bloqueantes para o Gate de avaliação** (verificadas só no momento autorizado, porque exigem abrir a régua):
1. bytes da régua = blobs congelados;
2. herança sem destinos conflitantes e sem o mesmo `eid` para dois `gold_id`. Origem ambígua não pode ocorrer: 0 origens
   repetidas, medido;
3. denominadores por curso = tabela N7;
4. CRU com a régua lida = referência por curso (223/249/86). Se falhar, a cópia local diverge da leitura histórica e a
   avaliação é recusada.

**Interpretativas:**
- As travas não são sandbox: `os.open`, `mmap`, extensões C e imports ficam fora. O código importado é conferido por
  origem e hash.
- A equivalência com a história é empírica e só do CRU (§5).
- `nao_identificado` agrupa os 9 meta-materiais (§3).
- Taxonomias de braço reconstruídas no mesmo intérprete; outro Python ou outras distribuições exigem novo congelamento.
- A revisão Astra do código não foi rodada nesta etapa. A revisão adversarial externa do usuário é o próximo filtro.

## 8. Condições da conclusão

| Condição | Estado |
|---|---|
| Três bloqueios com teste que reproduz (vermelho) e correção (verde) | ok — 68/68 |
| Correções delimitadas com teste | ok |
| Protocolo v3 e matriz atualizados | ok |
| Preflight sem gold aprovado no namespace novo | ok — 23/23 |
| CRU recapturado = referência por ID | ok — 0 divergências |
| Carga isolada dos 7 braços válida | ok |
| Avaliador no congelamento, descritor da régua sem pendências | ok |
| `CAPTURA_LIBERADA` = {CRU}; nada liberado automaticamente | ok |

**Pronto para pedir o Gate de captura.**

Consequência do Gate:
1. Liberar os seis braços muda `CAPTURA_LIBERADA` em `comum.py`. Isso muda o hash do código e, portanto, o `id_comum`.
2. A execução autorizada começa por um preflight novo, que recaptura o CRU e confere a referência.
3. Só depois vem a captura dos seis braços, sem reaproveitar capturas deste congelamento.
