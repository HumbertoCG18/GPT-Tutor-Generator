# Handoff 26/09/2026 — regime VOCAB: Fase 1 avaliada e encerrada; rodada VOCAB_LIMPO capturada, aguardando revisão e Gate de avaliação

> **Atualização 26/09 (sessão seguinte):** Gate de avaliação da rodada limpa executado. Resultado em `c1-3/vocab_limpo_avaliacao_26-09/relatorio_avaliacao_vl.md`: VOCAB_LIMPO 174/251 na primária; A_limpo verdadeiro, B_limpo e C_limpo não atendidos. Os §§4–5 abaixo descrevem o estado ANTERIOR à avaliação. Em 27/09 o Gate 2 documental commitou localmente os artefatos da frente (sem push); os §§7–8 ficaram superados nesse ponto. Também em 27/09: diagnóstico das perdas (`c1-3/vocab_limpo_diag_perdas_27-09/`) e desenho da validação em cursos novos (`2026-09-27-regime-vocab-validacao-cursos-novos-desenho.md`), cuja §6 é o próximo ponto de entrada.

Sessão Claude Code `ee4dd19b-7491-4289-baf7-43a7b14dfb38`, de 25/09 a 26/09, com o usuário via Remote Control. Coordenador
único da frente "regime VOCAB" do motor. Branch `feat/motor-atribuicao`, HEAD `2589ed5a`, em dia com a origin.

**Ponto de entrada da próxima sessão:**
1. Este arquivo.
2. A entrada "Rodada VOCAB_LIMPO" no topo de `docs/reports/pendencias.md`.
3. O estado local `.workflow/local/regime-vocab-fase1-20260925.md`.

Detalhes técnicos da rodada ficam em `c1-3/vocab_limpo_26-09/relatorio_vocab_limpo.md`. Não releia os pacotes W-AD2 a
W-AD5 sem necessidade: os manifestos dizem o que existe.

---

## 1. Regras de trabalho que valem aqui (do usuário e do projeto)

- Toda resposta começa com "[Humberto]", em PT-BR compacto ("troglodita"); ações primeiro.
- Gates:
  - Gate 1 = plano ou autorização antes de executar;
  - Gate 2 = antes de commit;
  - push, PR e merge exigem autorização própria.
- **Nada desta frente foi commitado** (ver §7).
- As autorizações do usuário chegam como mensagens coladas, geralmente redigidas com o GPT a partir de uma revisão
  independente. Elas definem escopo, proibições e condições de parada com precisão; siga-as literalmente. Uma falha
  nova → preservar a evidência e parar; não virar sequência aberta de correções.
- **Entregas para revisão externa (GPT):**
  - pasta + ZIP em `C:\Users\Humberto\Desktop\para-gpt\<entrega>\`;
  - prompt em `para-gpt\prompt_revisao_<entrega>.md`;
  - envio pelo `SendUserFile`;
  - o usuário move o que já mandou para `para-gpt\Já_Mandados\`;
  - conteúdo acadêmico bruto (requests e responses do LLM, staging, sidecars, capturas) NÃO vai no ZIP sem Gate 2
    documental.
- Sem revisão Astra/LLM nesta frente, salvo pedido explícito; a revisão adversarial é do GPT, via usuário.
- Segurança:
  - nunca ler, imprimir ou hashear `.env` nem `~/.gpt_tutor_config.json`. A chave Gemini fica nesse arquivo; a
    recompilação o leu como JSON puro, antes das travas, só para criar o cliente;
  - nunca `git add -A`, reset, clean ou stash automático; preservar alterações alheias e os 4 stashes.

## 2. Linha do tempo desta sessão

1. **Segurança:** PR #83 mergeado (`d815e205`), #81/#82 fechadas, fase 1 da #80, check `secrets` obrigatório, hook
   reinstalado, setup de nuvem.
2. **Motor (commitado e pushado):**
   - #50 `15ea8c4a`;
   - W-AB e M1 `eebc698c` (texto confiante vence o bloco do resolvedor antigo na unidade);
   - W-AC e teto do regime cru `3c8f26d9`;
   - desenho do regime VOCAB `2589ed5a`.
3. **Regime VOCAB, Fase 1 (histórica, offline, sem src):** harness em versões sucessivas, cada uma revisada pelo GPT.

   | versão | pasta | resultado |
   |---|---|---|
   | W-AD2 | `wad2_*` | preflight 13/13 |
   | W-AD3 | `wad3_25-09/` | 20/20 |
   | W-AD4 | `wad4_25-09/` | cadeia de congelamento fechada, 68 testes, 23/23 |
   | W-AD5 | `wad5_25-09/` | dois ajustes da revisão independente, 87 testes, preflight 24/24, **sete capturas congeladas** (congelamento `3fe5d1ff…`) |

4. **Avaliação da Fase 1** (`c1-3/wad5_avaliacao_26-09/`):
   - A primeira execução parou por integridade: a régua na cópia de trabalho tem CRLF e o blob congelado tem LF.
   - O usuário autorizou o **espelho endereçado por conteúdo**, e o avaliador rodou byte-idêntico.
   - Resultado válido com ressalvas (§3). Errata final com três correções de redação.
5. **Limpeza de `docs/reports`:** 14 arquivos movidos com `git mv` (11 para `_archive/`, 3 para `_archive/`), referências
   atualizadas, renames só staged (§7). Criada a convenção `Desktop\para-gpt\`.
6. **Rodada VOCAB_LIMPO** (`c1-3/vocab_limpo_26-09/`): recompilação limpa única e seis braços capturados SEM GOLD (§4).
7. **Estado final:** prompt de revisão da rodada entregue (`para-gpt\prompt_revisao_vocab_limpo.md` +
   `vocab_limpo_26-09.zip`). **Aguardando a resposta do GPT.**

## 3. Fase 1 — resultado congelado (não reavaliar)

Pergunta da fase: "efeito do vocabulário sobre a cadeia de atribuição, condicionado à timeline histórica congelada".

| braço | bloco | unidade | sub primária | sub aceita |
|---|---:|---:|---:|---:|
| CRU | 223/237 | 249/284 | 86/251 | 109/251 |
| VOCAB_LLM (histórico) | 223/237 | 248/284 | **166/251** | 190/251 |
| VOCAB_ATUAL (referência mista) | 223/237 | 251/284 | 171/251 | 197/251 |
| CTRL_MAIOR | 223/237 | 249/284 | 67/251 | 96/251 |
| CTRL_ALEAT_1/2/3 | 223/237 | 249/248/248 | 70/82/67 | 90/110/84 |

- **Transições do VOCAB_LLM:**
  - primária: 87 correções e 7 perdas (+80); precisão sobre todas as saídas alteradas 87/124;
  - unidade: 3 correções e 4 perdas (−1; CG cai de 74 para 72).
- **Veredictos:** A verdadeiro; **B não atendido** ("sinal exploratório observado; candidato reprovado para
  integração"); C (primária > 90%) só no IA.
- **Revisão independente:** válida com ressalvas.
- **Errata** `wad5_avaliacao_26-09/errata_final_fase1_26-09.md`:
  - A: o CRU reproduzir os placares demonstra compatibilidade, não igualdade integral da régua;
  - B: a recompilação limpa não elimina o ajuste histórico no IA;
  - C: algumas transições de unidade se repetem entre braços, e a causa não foi isolada.
- **Artefatos:** `wad5_25-09/` (manifestos `manifesto_pacote_v5.json`, `manifesto_capturas_v5.json`),
  `wad5_avaliacao_26-09/` (`manifesto_avaliacao_26-09.json`), `.frzero/wad5_25-09/`, espelho em
  `.frzero/wad5_avaliacao_26-09/espelho/`.

## 4. Rodada VOCAB_LIMPO — estado exato

**Pergunta:** o compilador atual, executado uma vez com entradas e configuração congeladas e sem manual, mantém o sinal
exploratório? **Não prova** generalização, ausência de overfitting do prompt nem independência dos sete cursos, que
continuam contaminados.

| etapa | resultado | artefato-chave |
|---|---|---|
| Pré-registro | bloco NORMATIVO, `protocolo_sha` `42e52218…` | `docs/reports/2026-09-26-regime-vocab-recompilacao-limpa.md` |
| Staging a partir do CRU | 350 entries, 305 markdowns, unidade = decisão CRU (7 trocas: SO 6, CG 1), árvore `040fe431…` | `.frzero/vocab_limpo_26-09/staging/`, `staging_manifesto.json` |
| Ensaio sem rede (2×) | 26 chamadas previstas, requests determinísticas | `inventario_chamadas.json` |
| Congelamento da recompilação | `62b45e38750efc300fcc03da89f874def35e611054946d273b52d86d93cff676` | `congelamento_recompilacao.json` |
| Geração oficial única | 26/26, 1ª tentativa, 0 falhas, 0 violações, só o host Gemini, `model_version` = `gemini-3.5-flash` (alias) | `compilacao.json`, `chamadas/` (52 arquivos, locais) |
| Sanidade sem gold | aprovada | `sanidade.json`, `c1-3/vocab_limpo_26-09/sanidade_vocab_limpo.md` |
| Harness da rodada | cópia do W-AD5 via `adapta_rodada.py`; diff real +152/−131 (`diff_w5_vl.patch`); suíte 93/93 | `c1-3/vocab_limpo_26-09/` |
| Preflight | 24/24; CRU_LIMPO = referência por ID (350/0); controles sem bloqueio | `preflight_vl.{json,md}`; congelamento da captura `6a0f9652fb8cfaffde15cd9d113705536c7fcc5f9b303474a74438ceee8c0e81` |
| Capturas | 6 braços, 14/14, 0 violações, os mesmos 9 meta-materiais não chamados | `manifesto_capturas_vl.json`, `.frzero/vocab_limpo_26-09/captura/capturas/` |
| Avaliador da rodada | cópia do avaliador da Fase 1 com SÓ os nomes trocados (prova em `test_rodada_limpa.py`); congelado; **não executado** | `c1-3/vocab_limpo_26-09/avaliador.py` |
| Manifesto geral | hashes de tudo, inclusive do que ficou local | `c1-3/vocab_limpo_26-09/manifesto_rodada_vl.json` |

**Braços:** CRU_LIMPO, VOCAB_LIMPO, CTRL_MAIOR_LIMPO e CTRL_ALEAT_LIMPO_1/2/3 (sementes 1, 2, 3; mesmas regras da
Fase 1).

**Veredictos pré-registrados (R8):**
- A_limpo: VOCAB_LIMPO > CRU_LIMPO, CTRL_MAIOR_LIMPO e cada aleatório na primária total;
- B_limpo: ganho de primária, zero perda nos três eixos oficiais, nenhum curso regredindo;
- C_limpo: > 90% por eixo e curso, por contagem exata.

## 5. Próximos passos (em ordem; nada disso está autorizado ainda)

1. **Receber a revisão do GPT** sobre `vocab_limpo_26-09.zip`. Condição apontada → corrigir só o registro ou o que for
   autorizado, sem regenerar o vocabulário.
2. **Gate de avaliação da rodada limpa** (autorização própria, com `--autorizo-gold`). Procedimento que funcionou na
   Fase 1, a adaptar e **só com autorização**:
   1. **Validar antes da régua**, no ambiente controlado: modelo `c1-3/wad5_avaliacao_26-09/valida_pre_regua.py`, com os
      caminhos da rodada:
      - código: `vocab_limpo_26-09/avaliador.py` e `comum.py`;
      - congelamento: `.frzero/vocab_limpo_26-09/captura/congelamento.json`;
      - capturas: `.../captura/capturas/capturar_<BRACO>_6a0f9652fb8cfaff_<insumos16>.json`;
      - snapshots: `.../captura/snapshots/`;
      - manifesto: `manifesto_capturas_vl.json`.
   2. **Espelho endereçado por conteúdo:** modelo `wad5_avaliacao_26-09/monta_espelho.py`.
      - A régua vem de `git cat-file blob <blob>` do descritor do congelamento (mesmos 38 blobs da Fase 1).
      - Os manifests de referência e os salvos são copiados com sha256 conferido. Cuidado: SO, ES2, TCC e FR usam o mesmo
        caminho nos dois papéis.
      - `avaliador.py` e `comum.py` **da rodada** são copiados byte a byte para `<espelho>/docs/reports/_harness-2026-09-04/c1-3/vocab_limpo_26-09/`.
   3. **Rodar o avaliador do espelho:** `avaliador.py --autorizo-gold <caps> <congelamento> <snapshots> <saida.json>`,
      via `roda_controlado.py`; depois, **uma** execução de conferência (tem de ser idêntica byte a byte) e
      `confere_resultado.py` adaptado aos nomes.
   4. **O CRU_LIMPO tem de reproduzir 223/249/86 por curso.** Senão a avaliação é recusada. Perda do candidato não é
      falha de integridade.
   5. **Relatar** placar, transições, precisão, geração e seleção e os veredictos A_limpo, B_limpo e C_limpo, com as
      mesmas limitações.
3. **Decisões posteriores** (não iniciar sem Gate): compilador v2, validação em cursos novos, integração no produto,
   commit dos artefatos documentais (§7).

## 6. Armadilhas aprendidas (evite repetir)

- **Régua × CRLF:**
  - `core.autocrlf=true` + `* text=auto`: bytes da cópia de trabalho ≠ blob do índice em 37 de 38 arquivos da régua;
  - `git status` diz "limpo" mesmo assim;
  - para conferir sem ler o conteúdo, use tamanho do disco × `git cat-file -s <blob>`;
  - para usar os bytes congelados, leia com `git cat-file blob`.
- **Bash tool no Windows:**
  - heredoc com `'''` ou crases às vezes quebra ("unexpected EOF"): grave o script num arquivo (Write) e rode-o;
  - `Path.write_text` converte `\n` em `\r\n`: para editar preservando o fim de linha, use bytes;
  - arquivos do harness têm fim de linha misto: gere os diffs com `diff --strip-trailing-cr`.
- **pytest:**
  - coleta `test*.txt` como doctest: grave `testes_*.txt` em UTF-8 (converta de cp1252), senão a coleta quebra;
  - rode com `python -B -m pytest ... -p no:cacheprovider` para não deixar `__pycache__`.
- **`test_regua_real_bloqueada_sem_autorizacao`** falha só sob `PYTHONIOENCODING=utf-8` (decodificação): a suíte
  oficial roda no terminal.
- **Assinatura das distribuições** (`sha_json(distribuicoes())`): só confere dentro do processo controlado. No terminal
  comum dá diferente por causa do site de usuário e do `sys.path`.
- **`K.grava_atomico`** cria um temporário na pasta-mãe: as travas precisam de "saída" na pasta-mãe, não só no arquivo.
- **Travas (`comum.Travas`):**
  - o import do produto tenta ler `.env` (negado) e grava `TESSDATA_PREFIX` em `os.environ`: o worker recebe o
    ambiente declarado montado do zero;
  - `rg` pula pastas ignoradas e ocultas (`.workflow/local/`): ao procurar referências, use `--hidden --no-ignore` ou
    liste as pastas.
- **Nomes de braço em testes:** um teste da Fase 1 usava "VOCAB_LIMPO" como braço inexistente e, na rodada limpa,
  disparou um worker de verdade. Ao renomear braços, procure literais com aspas simples e duplas.
- **Jobs em segundo plano:** Monitor expira em 30 min. Para esperar, use laços `until grep ...; sleep 5` de até
  600 s em Bash.
- **Tempos:** preflight de 7 a 12 min; captura de 5 braços cerca de 23 min; recompilação 26 chamadas em 265 s.

## 7. Worktree, pendências e o que NÃO está commitado

- **Index:** 14 renames da limpeza de `docs/reports` (25/09). Modificados e não staged:
  - `.mex/ROUTER.md`, `.mex/context/{setup,navigation-history}.md`, `.workflow/HANDOFF.md`;
  - 3 relatórios, 2 arquivos em `_archive/`;
  - `docs/reports/pendencias.md`, com as entradas W-AD2 a VOCAB_LIMPO, a limpeza e a parada;
  - este handoff.
  - Tudo espera o Gate 2 documental.
- **Não versionados desta frente:**
  - adendos da Fase 1 (v1 a v4) e o pré-registro da rodada limpa;
  - `c1-3/wad2_*`, `wad3_25-09/`, `wad4_25-09/`, `wad5_25-09/`, `wad5_avaliacao_26-09/`, `vocab_limpo_26-09/`;
  - `wad_regime_vocab_fase1_24-09.py`.
  - Arquivos de outras sessões, preservados: `c1-3/diagnostico_subunidade_17-09.*`, `astra_revisao_regime2_17-09.md`.
- **`.frzero/`** (ignorado pelo git) guarda todos os resultados brutos: `wad3`, `wad4`, `wad5_25-09`,
  `wad5_avaliacao_26-09` (espelho da régua) e `vocab_limpo_26-09` (staging, chamadas, sidecars, captura).
- **Pendências anteriores, não tocadas:**
  - link quebrado `../superpowers/plans/2026-09-15-workflow-tres-clis.md` no tracker;
  - índice Graphify desatualizado (backlog desde 16/09);
  - `c1-3/` (1.078 arquivos) só pode ser arquivado por experimento depois dos Gates de avaliação, porque os
    congelamentos apontam caminhos dali.
- **Stashes** (4, alheios): não tocar.

## 8. Autorizações vigentes (26/09)

- **Autorizado e concluído:** Gate 1 da rodada limpa (errata; pré-registro; uma geração; braços e capturas sem gold).
- **Não autorizado agora:**
  - ler ou avaliar a régua da rodada limpa;
  - gerar de novo;
  - compilador v2 ou cursos novos;
  - mudar `src/`, régua, denominadores ou timeline;
  - commit, push, PR ou merge;
  - publicar conteúdo acadêmico.
