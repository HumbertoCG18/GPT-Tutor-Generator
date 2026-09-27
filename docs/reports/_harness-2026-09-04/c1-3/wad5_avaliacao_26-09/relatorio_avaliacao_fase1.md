# Regime VOCAB, Fase 1 — avaliação das sete capturas (26/09/2026)

**Nome do resultado:** efeito do vocabulário sobre a cadeia de atribuição, condicionado à timeline histórica congelada.

- **Autorização:** Gate de avaliação do usuário (26/09) sobre as sete capturas W-AD5.
- **Protocolo:** `docs/reports/2026-09-25-regime-vocab-adendo-fase1-v4.md`.
- **Referências usadas:**
  - congelamento `3fe5d1ff97258644b3148860cbe235aa3e16acfac91e9a291ea3c3e63a8e355d`;
  - `avaliador.py` `aeac2996…`, `comum.py` `04a535b6…`;
  - capturas e snapshots em `.frzero/wad5_25-09/`.
- **Resultado bruto do avaliador:** `avaliacao_espelho_1.json` (sha256 `5a3b8aea…`).

## 0. Integridade e procedimento

1. **Validação pré-régua** (`valida_pre_regua.py`, ambiente controlado): **73/73**, sem gold. Cobriu:
   - código aprovado, congelamento, protocolo, intérprete e distribuições;
   - as 7 capturas (sha256, `conteudo_sha` recalculado, validador completo, identidade, 350 registros, sem mistura);
   - 49 snapshots de taxonomia e índice + palcos locais;
   - manifests de referência e salvos;
   - blobs dos 38 arquivos da régua no índice.
2. **Parada 1:** o avaliador congelado recusou `herancas_MF_15-09.json` (`bytes != blob congelado`).
   - Causa medida: o repositório tem `core.autocrlf=true` e `* text=auto`. A cópia de trabalho do Windows tem CRLF e o
     blob tem LF; o avaliador compara bytes crus com o blob normalizado.
   - Régua inalterada (`git status` limpo). Detalhe em `parada_avaliacao_26-09.md`.
   - Exposição registrada: único arquivo de régua aberto, lido e hasheado, não interpretado.
3. **Correção autorizada pelo usuário: espelho endereçado por conteúdo** (`monta_espelho.py`, `espelho_manifesto.json`):
   - régua materializada de `git cat-file blob <blob congelado>` (38 arquivos, blob reconferido);
   - manifests copiados com sha256 conferido;
   - `avaliador.py` e `comum.py` byte-idênticos. **Nenhuma linha do avaliador mudou.**
   - A 1ª montagem parou por colisão legítima de caminho (manifest salvo = de referência em SO/ES2/TCC/FR; log
     preservado). O script passou a aceitar o mesmo caminho só com bytes idênticos.
4. **Avaliação** pelo avaliador congelado a partir do espelho, com a interface existente (`--autorizo-gold`, caminhos
   explícitos das capturas, congelamento e snapshots): saída 0.
   - Passaram as verificações internas: código contra o congelamento, capturas, taxonomias, blobs, herança sem
     conflito, origem única, régua com denominadores por curso e totais.
   - **CRU = referência por curso: 223/249/86**, reproduzido exatamente. Confirma, empiricamente, que ler a régua
     normalizada (LF) equivale à leitura histórica.
   - O avaliador calcula os placares dos sete braços em memória e confere o CRU antes de comparar e gravar (ordem
     aceita no Gate).
5. **Execução de conferência** (`avaliacao_espelho_2_conferencia.json`): **idêntica byte a byte** (mesmo sha256).
6. **Conferência independente** (`confere_resultado.py`):
   - placares = registros por ID, e somas por curso = total, nos 7 braços;
   - denominadores = pré-registrados; CRU = referência;
   - células, correções, perdas, saldos e precisões = registros por ID;
   - `eid` no inventário congelado.
7. **Mapeamento da herança:**
   - 0 materiais ausentes em todos os cursos;
   - 13 correspondências pela "ponte" histórica (mesmo ID no manifest salvo): CG 7, MF 4, IA 2;
   - nenhuma origem ambígua.

## 1. Resultado observado

### Placar total (acertos/n)

| braço | bloco | unidade | subunidade primária | subunidade aceita (auxiliar) |
|---|---:|---:|---:|---:|
| CRU | 223/237 | 249/284 | **86/251** (34,3%) | 109/251 |
| VOCAB_ATUAL (referência de proveniência mista) | 223/237 | 251/284 | 171/251 (68,1%) | 197/251 |
| **VOCAB_LLM** | 223/237 | 248/284 | **166/251** (66,1%) | 190/251 |
| CTRL_MAIOR | 223/237 | 249/284 | 67/251 | 96/251 |
| CTRL_ALEAT_1 | 223/237 | 249/284 | 70/251 | 90/251 |
| CTRL_ALEAT_2 | 223/237 | 248/284 | 82/251 | 110/251 |
| CTRL_ALEAT_3 | 223/237 | 248/284 | 67/251 | 84/251 |

O bloco é idêntico em todos os braços. A tabela completa por braço, curso e eixo está em `placar_por_curso.csv`.

### Subunidade primária por curso (acertos)

| curso (n) | CRU | VOCAB_ATUAL | VOCAB_LLM | MAIOR | ALEAT_1 | ALEAT_2 | ALEAT_3 |
|---|---:|---:|---:|---:|---:|---:|---:|
| MF (58) | 25 | 38 | 38 | 16 | 3 | 14 | 9 |
| SO (15) | 7 | 11 | 11 | 7 | 4 | 7 | 7 |
| IA (39) | 4 | 36 | 36 | 4 | 11 | 14 | 4 |
| ES2 (28) | 7 | 20 | 18 | 10 | 6 | 6 | 7 |
| TCC (11) | 7 | 9 | 9 | 5 | 6 | 6 | 5 |
| CG (82) | 30 | 41 | 38 | 23 | 32 | 30 | 31 |
| FR (18) | 6 | 16 | 16 | 2 | 8 | 5 | 4 |

### Unidade — cursos com diferença entre braços (os demais iguais ao CRU)

| curso | CRU | VOCAB_ATUAL | VOCAB_LLM | MAIOR | ALEAT_1 | ALEAT_2 | ALEAT_3 |
|---|---:|---:|---:|---:|---:|---:|---:|
| MF (66) | 63 | 63 | 63 | 64 | 64 | 63 | 63 |
| SO (37) | 30 | 31 | 30 | 30 | 30 | 30 | 30 |
| IA (42) | 39 | 40 | 40 | 40 | 40 | 40 | 40 |
| CG (93) | 74 | 74 | **72** | 72 | 72 | 72 | 72 |

### Transições contra o CRU

Registro por ID em `transicoes_por_id.csv` e no JSON. As categorias se sobrepõem (por exemplo, abstenção → certa ⊂
correção) e não se somam como materiais distintos.

| braço | eixo | correções | perdas | erro → outro erro | abstenção → certa | abstenção → errada | decisão → vazio | precisão, TODAS as alteradas | precisão, alteradas não vazias |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| VOCAB_LLM | primária | 87 | 7 | 30 | 16 | 10 | 2 | **87/124** (70,2%) | 87/122 |
| VOCAB_LLM | aceita | 86 | 5 | 22 | 18 | 8 | 2 | 97/124 | 97/122 |
| VOCAB_LLM | unidade | 3 | 4 | 4 | — | — | — | 4/12 | 4/12 |
| VOCAB_LLM | bloco | 0 | 0 | 0 | — | — | — | 0/0 (não aplicável) | 0/0 |
| VOCAB_ATUAL | primária | 90 | 5 | 28 | 18 | 5 | 2 | 90/123 | 90/121 |
| VOCAB_ATUAL | unidade | 5 | 3 | 3 | — | — | — | 6/12 | 6/12 |
| CTRL_MAIOR | primária | 8 | 27 | 64 | 2 | 31 | 0 | 8/99 | 8/99 |
| CTRL_ALEAT_1 | primária | 30 | 46 | 67 | 4 | 19 | 9 | 30/143 | 30/134 |
| CTRL_ALEAT_2 | primária | 31 | 35 | 65 | 6 | 12 | 6 | 31/131 | 30/125 |
| CTRL_ALEAT_3 | primária | 19 | 38 | 94 | 7 | 22 | 3 | 19/151 | 19/148 |

Nas duas colunas de precisão, "correta → outra correta" conta como alteração certa. Por isso a precisão da aceita
(97) excede as correções (86).

### Concentração por curso (VOCAB_LLM contra o CRU)

- **Primária, correções (87):** IA 32, ES2 15, MF 14, CG 10, FR 10, SO 4, TCC 2.
- **Primária, perdas (7):** ES2 4, CG 2, MF 1. Saldo por curso: MF +13, SO +4, IA +32, ES2 +11, TCC +2, CG +8, FR +10.
- **Perdas por ID (primária):**
  - ES2 `roteiro5`, `roteiro6`, `roteiro7`, `roteiro7-history-service`: do tópico
    "estudo-de-caso-integracao-e-implantacao…" para "gerenciamento-da-configuracao" (as quatro também perdem na
    aceita);
  - CG `slab`: "algoritmos-de-geometria-computacional" → "algoritmos-de-poligonos";
  - CG `pagina-com-videos-sobre-manipulacao-de-i…`: "cores-e-tipos-de-imagens" → "segmentacao";
  - MF `exerciciosisabelle`: "provadores-de-teoremas" → "especificacao-de-funcoes-recursivas".
- **Unidade:**
  - correções MF 1, SO 1, IA 1;
  - perdas MF `t2-2026-1`, SO `0704-laminas-comunicacao-e-sincronizacao`, CG `opengl-cpp` e `opengl-py` (u01 → u02);
  - as mesmas 3 correções (IA `ia-responsável…`, MF `t1-2026-1-thy`, SO `laminas-sockets…`) e as perdas SO `0704…` e
    CG `opengl-*` aparecem, com os mesmos IDs, nos quatro controles;
  - as perdas CG `opengl-*` aparecem também no VOCAB_ATUAL;
  - é um efeito comum aos braços com taxonomia reconstruída a partir das relações do VOCAB_LLM, não específico do
    conteúdo LLM (observação, sem afirmação causal).

### Geração de candidatos e seleção (subunidade primária; 245 linhas com gold não vazio)

**Escada** (b–d só entre os chamados, 245 nos dois braços):

| degrau | CRU | VOCAB_LLM |
|---|---:|---:|
| (a) rótulo existe na taxonomia | 245 | 245 |
| (a) elegível na unidade usada | 229 | 227 |
| (b) score > 0 | 137 | 201 |
| (c) score ≥ 0,05 | 119 | 198 |
| (d) escolhido na 1ª passada | 62 | 155 |
| (e) final correto | 85 | 165 |

O (e) exclui as 6 linhas com gold vazio (1 certa em cada braço; total primária 86 e 166).

**Grupos de candidato:**

| corte | ambos | só CRU | só VOCAB_LLM | nenhum |
|---|---:|---:|---:|---:|
| > 0 | 136 | 1 | 65 | 43 |
| ≥ 0,05 | 118 | 1 | 80 | 46 |

**Seleção no subconjunto comum (ambos têm o gold como candidato):**

| corte | CRU, 1ª passada | CRU, final | VOCAB_LLM, 1ª passada | VOCAB_LLM, final |
|---|---:|---:|---:|---:|
| > 0 (136) | 62 | 77 | 97 | 106 |
| ≥ 0,05 (118) | 62 | 75 | 84 | 93 |

**Estados da 1ª passada (251):**

| estado | CRU | VOCAB_LLM |
|---|---:|---:|
| decidido | 177 | 223 |
| empate | 43 | 17 |
| candidatos com score zero | 22 | 5 |
| ambíguo com slug | 6 | 5 |
| abstenção | 3 | 1 |

Controles, 1ª passada escolhida (d): MAIOR 61, ALEAT 62/69/60. Final (e): 67, 70, 80, 67.

**Os 9 meta-materiais não chamados** (planos e apresentações):
- ficam fora da população da subunidade (0 linhas), sem chamada nem score inventados;
- estão nas populações de bloco (6) e de unidade (8), certos no CRU e no VOCAB_LLM.

## 2. Veredictos pré-registrados

- **A — sinal exploratório: VERDADEIRO.** Na primária total, VOCAB_LLM (166) > CRU (86), CTRL_MAIOR (67),
  CTRL_ALEAT_1 (70), CTRL_ALEAT_2 (82) e CTRL_ALEAT_3 (67). Não é teste de significância: são três controles
  aleatórios.
- **B — compatibilidade com o aceite: NÃO ATENDIDO**, logo "sinal exploratório observado; candidato reprovado para
  integração".
  - Ganho de primária: +80 ✓.
  - Perdas nos eixos oficiais: bloco 0, unidade **4**, primária **7** ✗.
  - Curso que regride: **CG na unidade** (74 → 72) ✗.
  - Aceita (auxiliar, não veta): 5 perdas; nenhum curso regride nela.
- **C — meta (>90% por eixo e curso, contagem exata), VOCAB_LLM:**
  - bloco atinge em todos os 6 avaliados;
  - unidade atinge em MF, IA, ES2 e TCC; não em SO (30/37) nem CG (72/93);
  - primária só atinge no IA (36/39); não em MF, SO, ES2, TCC, CG nem FR (16/18 = 88,9%).
  - FR sem bloco nem unidade (não aplicável).
  - Para comparação, o CRU não atinge a primária em nenhum curso.
- **VOCAB_ATUAL** (171) é referência histórica de proveniência mista. Não aprova o VOCAB_LLM.

## 3. Limitações

- **Os 7 cursos são desenvolvimento contaminado, não holdout.** Não há evidência de generalização para curso novo.
- **"Sem manual no carregamento" não é ausência de ajuste histórico ao benchmark.**
  - Os sidecars LLM têm proveniência incompleta.
  - O prompt do compilador foi calibrado no IA (registro histórico do tracker, cabeçalho de 15/09: "só no prompt do
    compilador, calibrado no IA"), e o IA concentra 32 das 87 correções.
- **O efeito está condicionado à timeline histórica congelada;** não é reprodução do produto integrado.
- **A régua usada é a histórica exata.** CG não foi adjudicado; na subunidade, a correspondência é por slug.
- **Homônimos:** um slug pode repetir entre unidades do mesmo curso. Uma correspondência por slug não é, por si, uma
  identidade conceitual inequívoca, e o placar histórico não foi alterado.
- **A avaliação rodou pelo espelho endereçado por conteúdo:** régua em LF, sem mudança de código. A equivalência com a
  leitura histórica foi confirmada pela reprodução exata do CRU por curso.
- **Ressalvas aceitas neste Gate:**
  - suíte 87/87 no terminal e 86/87 no ambiente controlado (falha só de decodificação do teste congelado
    `test_regua_real_bloqueada_sem_autorizacao`);
  - fase vermelha do W-AD5 = 14 falhas comportamentais + 2 `AttributeError` (`Travas.confere_congelados`,
    `captura.verifica_fim`) + 3 guardas que passam nas duas versões.
- **A mudança de unidade é comum a todos os braços com taxonomia reconstruída** (§1). A perda de CG na unidade não
  distingue o VOCAB_LLM dos controles.

## 4. Próxima decisão recomendada (não executada)

O candidato mostra o sinal exploratório pré-registrado, mas falha no aceite de integração. As perdas estão
concentradas:
- primária: 4 roteiros do ES2 levados a um único tópico, 2 do CG e 1 do MF;
- unidade: regressão de CG, que também ocorre nos controles.

Recomendação: **decidir se abre o Gate da recompilação limpa (VOCAB-limpo)**, prevista no desenho para depois da Fase 1.
- Ela remove a proveniência mista e a calibração no IA antes de qualquer conclusão sobre o compilador.
- Tem de ser medida com este mesmo protocolo, congelamento novo e o mesmo avaliador.
- As perdas por ID ficam como material de diagnóstico, sem ajuste dirigido pela régua.

Não recomendado agora: integração no produto, ajustes de aliases ou compilador v2 antes da decisão acima.

## 5. Artefatos desta entrega (hashes em `manifesto_avaliacao_26-09.json`)

| Grupo | Arquivos |
|---|---|
| Resultado | `avaliacao_espelho_1.json` (resultado), `avaliacao_espelho_2_conferencia.json` (idêntico) |
| Conferências | `validacao_pre_regua.json`, `conferencia_resultado.json`, `espelho_manifesto.json` |
| Tabelas por ID | `placar_por_curso.csv`, `transicoes_por_id.csv` |
| Logs | `log_validacao_pre_regua.txt`, `log_avaliacao_1.txt` (parada), `log_espelho_tentativa1_colisao.txt`, `log_espelho.txt`, `log_avaliacao_espelho_1.txt`, `log_avaliacao_espelho_2_conferencia.txt`, `log_conferencia_resultado.txt` |
| Scripts de conferência | `valida_pre_regua.py`, `roda_controlado.py`, `diagnostico_eol.py` + `.txt`, `monta_espelho.py`, `confere_resultado.py` |
| Relatórios | `parada_avaliacao_26-09.md`, este relatório |

Espelho (régua materializada, local e ignorado pelo git): `.frzero/wad5_avaliacao_26-09/espelho/`.
