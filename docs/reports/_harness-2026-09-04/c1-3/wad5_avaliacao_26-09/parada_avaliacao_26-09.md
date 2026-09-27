# Gate de avaliação W-AD5 — PARADA por integridade antes de qualquer interpretação da régua (26/09/2026)

> Atualização (26/09): o usuário autorizou a opção recomendada (espelho endereçado por conteúdo). Ela foi executada
> sem mudar o avaliador, e o resultado está em `relatorio_avaliacao_fase1.md`. Este documento registra a parada tal
> como ocorreu.

**Resultado desta tentativa: avaliação NÃO realizada.** Nenhum placar foi calculado, gravado ou apresentado. Tentativa e logs
preservados nesta pasta. Nada foi ajustado (régua, código, mapeamentos) e nada foi recapturado.

## 1. O que rodou

1. **Estado:**
   - HEAD `2589ed5a`, `src/` e `tests/` limpos;
   - index só com os 14 renames documentais da limpeza de `docs/reports` (nenhum artefato da avaliação);
   - stashes e não versionados preservados.
2. **Validação pré-régua** (`valida_pre_regua.py`, ambiente controlado; `log_validacao_pre_regua.txt`,
   `validacao_pre_regua.json`): **73/73 condições**, sem abrir a régua. Cobriu:
   - `avaliador.py` `aeac2996…` e `comum.py` `04a535b6…`;
   - congelamento `3fe5d1ff…` (ligações, entradas, protocolo, intérprete, distribuições);
   - as 7 capturas: sha256, `conteudo_sha` recalculado, validador completo, identidade, 350 registros;
   - diretório só com as 7, sem falhas;
   - 49 snapshots de taxonomia e índice + palcos locais = congelamento;
   - manifests de referência e salvos;
   - blobs dos 38 arquivos da régua no índice do git = congelados.
3. **Avaliador congelado, execução 1** (`log_avaliacao_1.txt`; comando e ambiente no cabeçalho do log):
   ```
   python -B -X pycache_prefix=<vazio> wad5_25-09/avaliador.py --autorizo-gold .frzero/wad5_25-09/capturas
       .frzero/wad5_25-09/congelamento.json .frzero/wad5_25-09/snapshots <esta pasta>/avaliacao_1.json
   ```
   Saída 1 em 0,6 s: `ErroIntegridade: docs/reports/_harness-2026-09-04/c1-3/herancas_MF_15-09.json: bytes != blob
   congelado`. Nenhum `avaliacao_1.json` foi gravado.

## 2. Exposição do gold (registro exigido)

- O avaliador passou pelas próprias verificações (código, congelamento, entradas e capturas) e entrou na porta da régua.
- Os manifests de referência e o salvo do MF (não são régua) conferiram pelo sha256.
- **Único arquivo de régua aberto:** `herancas_MF_15-09.json` (mapeamento de herança do MF). Os bytes foram lidos em
  memória e hasheados; a divergência interrompeu antes de qualquer interpretação (sem `json.loads`, sem impressão).
- Nenhum outro arquivo da régua foi aberto. Nenhum acerto, placar ou comparação foi calculado.
- O diagnóstico abaixo usou só metadados da régua (tamanho no disco e tamanho do blob no git) e o conteúdo de scripts
  de código.

## 3. Causa (medida, sem abrir mais régua) — `diagnostico_eol.txt`

- O repositório tem `core.autocrlf=true` e `.gitattributes` com `* text=auto`. O git guarda o conteúdo normalizado com
  LF e grava a cópia de trabalho no Windows com CRLF.
- **Prova em código (não é régua)**, nos 6 scripts históricos:
  - nos 3 com CRLF no disco (`wx_regua_corrigida_22-09.py` 680, `eval_ground_truth.py` 344, `eval_entry_unit.py` 199),
    bytes do disco ≠ blob e bytes com CRLF→LF = blob exato;
  - nos 3 sem CRLF, disco = blob;
  - `git status` limpo em todos.
- **Régua (só metadados):**
  - 37 de 38 arquivos são maiores no disco que no blob (+4 a +2482 bytes, compatível com +1 byte por linha);
  - `git status` limpo nos 38 (conteúdo normalizado = índice).
- **Conclusão:** a régua não mudou. A verificação do avaliador congelado (`carrega_regua_historica.ler`) compara os
  bytes CRUS do disco com o blob do conteúdo NORMALIZADO. Nesta cópia do Windows ela falha em 37 de 38 arquivos por
  construção.
- **Por que passou despercebido:**
  - os testes sintéticos gravavam bytes exatos e calculavam o blob sobre eles, sem o git no caminho;
  - o preflight lê os blobs do índice sem abrir a régua, por desenho;
  - portanto o defeito só aparece na primeira leitura autorizada.

## 4. Proposta de correção (NÃO executada; exige autorização própria)

**Opção recomendada — espelho endereçado por conteúdo, avaliador byte-idêntico.**
1. Montar uma raiz-espelho em `.frzero/wad5_avaliacao_26-09/espelho/` com os mesmos caminhos relativos:
   - cada arquivo da régua materializado de `git cat-file blob <blob congelado>`, ou seja, exatamente os bytes que o
     congelamento identifica;
   - manifests de referência e salvos copiados com o sha256 conferido;
   - `avaliador.py` e `comum.py` copiados byte a byte e conferidos contra os hashes aprovados.
2. Rodar o MESMO avaliador congelado a partir do espelho, com a mesma interface e os mesmos caminhos de capturas,
   congelamento e snapshots.

Por que é a recomendada:
- não muda uma linha do avaliador;
- a régua interpretada é, por definição, o blob congelado;
- a conferência de blob do avaliador passa a ser exata.

Risco:
- o conteúdo interpretado é o LF normalizado. As medições históricas leram a cópia com CRLF, e a leitura de CSV
  (`newline=""`) e de JSON dá os mesmos valores nas duas formas;
- se não der, a própria referência do CRU (223/249/86 por curso) recusa a avaliação.

**Alternativa — corrigir o avaliador:** em `ler()`, ler o blob pelo git em vez do disco. Isso muda o hash do avaliador
(≠ `aeac2996…` e ≠ o do congelamento). Exigiria:
- aprovar um novo hash de avaliador;
- teste sintético com repositório temporário (`autocrlf`/`text=auto`), vermelho no congelado e verde no corrigido;
- registrar que o avaliador mudou depois da captura (as capturas não dependem dele).

**Não recomendado:** mudar `core.autocrlf` ou refazer o checkout dos arquivos da régua. Isso altera a cópia de trabalho
de outras sessões e da régua.

Em qualquer opção, ficam como estavam no Gate:
- o CRU tem de reproduzir a referência por curso antes de qualquer resultado ser aceito;
- uma execução de conferência;
- nada de ajuste de régua, código de medição ou mapeamentos.

## 5. Ressalvas registradas neste Gate (pedido do usuário)

- **Suíte sintética:** 87/87 no terminal; 86/87 no ambiente controlado. A única falha é o teste congelado
  `test_regua_real_bloqueada_sem_autorizacao`, por decodificação (saída 2 e mensagem corretas em UTF-8). Exceção
  aceita pelo usuário para este Gate; o teste não foi alterado.
- **Fase vermelha do W-AD5, qualificada:** 16 falhas contra o código revisado = 14 comportamentais + 2 `AttributeError`
  (funções inexistentes na v4: `Travas.confere_congelados`, `captura.verifica_fim`); 3 guardas passaram nas duas
  versões.

## 6. Estado dos artefatos depois da parada

- Conferidos: avaliador e `comum.py` nos hashes aprovados; 7 capturas = manifesto; pacote W-AD5 e resultados =
  `manifesto_pacote_v5.json`; pycache isolado vazio.
- Arquivos desta pasta:
  - `valida_pre_regua.py`, `roda_controlado.py`, `diagnostico_eol.py`: scripts novos de conferência; nenhum altera
    artefato congelado;
  - logs, `validacao_pre_regua.json`, `diagnostico_eol.txt` e este relatório.
