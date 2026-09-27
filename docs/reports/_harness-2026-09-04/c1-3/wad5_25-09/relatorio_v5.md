# W-AD5 — Gate condicional de captura: dois ajustes, novo congelamento e sete capturas (25/09/2026)

**Sete capturas validadas e congeladas. Gold não lido. Aguardando Gate de avaliação.**

Autorização: Gate condicional do usuário (25/09), a partir da revisão independente do pacote W-AD4.
Protocolo: `docs/reports/2026-09-25-regime-vocab-adendo-fase1-v4.md` (bloco NORMATIVO, `protocolo_sha` conferido no
congelamento). Código: `c1-3/wad5_25-09/`. Resultados: `.frzero/wad5_25-09/`.

A versão revisada ficou intacta, conferida pelo próprio manifesto: `c1-3/wad4_25-09/` (15 arquivos), 221 resultados em
`.frzero/wad4_25-09/` e o adendo v3.

Não houve:
- leitura ou avaliação da régua;
- `--autorizo-gold`;
- rede, recompilação, compilador LLM ou embeddings;
- mudança em `src/` ou nos testes de produção;
- braços, sementes ou limiares novos;
- commit ou push;
- cálculo de acurácia, ganho, perda ou veredicto.

## 1. Base conferida antes de mudar

- HEAD `2589ed5a…` (= base do produto), index vazio, `src/` e `tests/` iguais à base.
- Contra o congelamento revisado `b3254509…`:
  - código, `src/` (136 arquivos), 7 árvores de pacote e 338 entradas externas: iguais;
  - assinatura das distribuições: igual (189 distribuições), conferida no ambiente controlado. No terminal, com site de
    usuário, ela difere — por isso a conferência só vale dentro do processo controlado.
- O ZIP `revisao_independente_wad4.zip` não está disponível localmente; os casos foram reproduzidos pela descrição do
  Gate.

## 2. Diff restrito e justificativa

`diff_v4_v5.patch` (wad4 → wad5): 416 linhas adicionadas e 28 removidas.

| Arquivo | Mudança | Por quê |
|---|---|---|
| `comum.py` | `Travas.verifica_acesso`: caminho no congelamento, ausente ou não arquivo → `insumo_desaparecido` + `Violacao`, antes de qualquer leitura | ajuste 1: antes retornava sem violação quando `isfile` era falso |
| `comum.py` | `Travas.confere_congelados()` (inventário congelado inteiro, lido ou não); `rehash_leituras()` passa a chamá-la; `_uma_vez` evita duplicar a mesma violação | ajuste 1: pega quem só consulta `exists()`/`is_file()` ou nunca abre |
| `comum.py` | `CAPTURA_LIBERADA` = os sete braços, escritos explicitamente; esquemas `wad5-*` | liberação autorizada; identifica a versão, e uma captura v4 não valida como v5 |
| `captura.py` | `verifica_distribuicoes(cong)`: recalcula `sha_json(distribuicoes())` e compara; ausente, inválido (não hex64 minúsculo) ou divergente reprova; nunca preenche o esperado | ajuste 2 |
| `captura.py` | chamada em `verifica_processo` (início do worker e do coordenador), em `verifica_fim` (fim do worker), em `roda_worker` (antes de reutilizar e depois do worker, antes de aceitar; recusada → sai do caminho de reúso para `falhas/rejeitada_*`) e na condição P5 do preflight | ajuste 2, nos três pontos pedidos |
| `captura.py` | worker: congela também palco e snapshots do próprio braço; `confere_congelados()` antes de qualquer import do produto; no fim, `verifica_fim` + `rehash_leituras` | ajuste 1: inventário antes e depois; nenhuma permissão nova |
| `captura.py` | `capturar_bracos()` + `--capturar`; caminhos `wad5`/`preflight_v5`; `test_ajustes_v5.py` no código congelado | execução autorizada (C e D) e caminhos de saída |
| `test_ajustes_v5.py` | 19 testes novos (reprodutores) | ajustes 1 e 2 |
| `test_wad4.py` | teste "seis braços bloqueados" → "exatamente os sete liberados + braço fora da lista rejeitado" | teste de autorização atualizado |
| `test_defeitos_v4.py` | teste de rejeição de braço não autorizado em cache fixa `CAPTURA_LIBERADA={"CRU"}` por monkeypatch | preserva a demonstração da rejeição |
| `avaliador.py` | **nenhuma** (byte-idêntico ao revisado) | avaliador congelado antes das capturas |

**Intocados:** métricas, controles, sorteio, reconstrução da taxonomia, decisões do motor, validador de captura (exceto
o esquema) e travas de rede, gold e compilador.

Na lógica herdada, só `rehash_leituras` mudou:
- as duas violações passam a ser registradas por `_uma_vez`, com os mesmos tipos;
- a função passa a chamar `confere_congelados`.

## 3. Reprodutores — vermelho na versão revisada, verde na corrigida

Vermelho (`testes_v5_vermelho.txt`, contra cópias byte a byte do código `b3254509…`): **16 falharam, 3 passaram**. Os 3
que passaram são guardas que devem passar nas duas versões: (d) entradas intactas, (e) opcional nunca congelado e (2c)
assinatura correta.

| Caso pedido | Teste | Vermelho (revisado) | Verde |
|---|---|---|---|
| 1a congelado some antes da 1ª leitura, consumidor captura `FileNotFoundError` | `test_a_…`, `test_a2_…` (vira pasta) | saída 0, nenhuma violação | saída 2, `insumo_desaparecido` |
| 1b só `exists()`/`is_file()` | `test_b_…` + `test_b2_…` (inventário antes do worker) | saída 0, nenhuma violação / sem conferência | saída 2; conferência acusa ausente e divergente |
| 1c congelado nunca aberto some durante a execução | `test_c_…` (+ `test_c2_…` alterado) | saída 0, nenhuma violação | saída 2, violação única |
| 1d intacto | `test_d_…` | passa | passa |
| 1e opcional nunca congelado ausente | `test_e_…` | passa | passa (não vira a mesma violação) |
| 2a divergente, demais parâmetros iguais | `test_2a_…` | `verifica_processo` → `[]` | reprova |
| 2b ausente / inválida (None, "", "abc", 123, não hex, maiúsculas) | `test_2b_…` (7 casos) | `[]` | reprova; esperado não preenchido |
| 2c correta | `test_2c_…` | passa | passa |
| 2d muda entre início e fim | `test_2d_…` (coordenador), `test_2d_fim_…` (worker) | captura ACEITA ("DID NOT RAISE") / sem conferência | recusada; sai do caminho de reúso para `falhas/` |

**Suíte final** (`testes_v5.txt`, Windows, Python 3.11.9, o intérprete da medição): **87/87** (68 herdados, 2 deles de
autorização atualizados, e 19 novos).

**Registro à parte** (`testes_v5_ambiente_controlado.txt`): no ambiente controlado da medição (`PYTHONIOENCODING=utf-8`),
86/87.
- A falha é do teste herdado `test_regua_real_bloqueada_sem_autorizacao`, que decodifica a saída do subprocesso pelo
  locale.
- A saída 2 e a mensagem "não autorizada" estão corretas; só a decodificação quebra.
- A v4 revisada falha igual nessas condições (67/68). É fragilidade anterior e fora do escopo, e não foi alterada.

## 4. Código e protocolo congelados (sha256)

| Arquivo | sha256 |
|---|---|
| `captura.py` | `7c5787cf39de736af121b158242233d9e186674c50686d8381c5e46e8d73b992` |
| `comum.py` | `04a535b678bfe6610701f0db91c43641c027275ea48fb1a111f4ef595e2a7e49` |
| `avaliador.py` | `aeac2996d96fd2085f7add91cfe20bc9c675bdd23ad0e144cdadd0f796978017` (= revisado) |
| `test_wad4.py` | `5333135194bc9f4d0d2a50ec7ffd3e39811bce37ffc000e2c1edbbb62a07d878` |
| `test_defeitos_v4.py` | `52def1c84cb340d8188327d6fea7fc4dc10bf832ca0bfd86ebff5fdf6d751514` |
| `test_ajustes_v5.py` | `62462c015837a57fec4df3f3b8a2d0b17c10c808e2de84c9666f94c2296ce334` |
| helpers `replay_bloco_21-09.py` / `replay_unidade_21-09.py` | inalterados (`86df7385…` / `a39e95af…`) |
| adendo v4, bloco normativo (`protocolo_sha`) | conferido igual pelo preflight e pela captura |

O arquivo do adendo v4 inteiro ganha o registro depois da execução, fora do bloco normativo. O hash final do arquivo
fica em `manifesto_pacote_v5.json`.

## 5. Novo congelamento e preflight

- **Congelamento comum:** `3fe5d1ff97258644b3148860cbe235aa3e16acfac91e9a291ea3c3e63a8e355d`
  (`.frzero/wad5_25-09/congelamento.json`, sha256 `fb44f399…`; entradas `91d88c2c…`).
- **Preflight** `preflight_v5.{json,md}`: **24/24, saída 0, 709 s**, na 1ª tentativa. As 23 condições da v4 mais "P5
  distribuições iguais à assinatura congelada".
- **Insumos por braço idênticos aos da v4** (snapshots reproduzidos): CRU `6689d5f0…`, VOCAB_ATUAL `b6bc6f52…`,
  VOCAB_LLM `eb322c73…`, CTRL_MAIOR `9a8a2d03…`, CTRL_ALEAT_1 `c593fc01…`, CTRL_ALEAT_2 `5cc5ff73…`, CTRL_ALEAT_3
  `7e88f881…`.
- **A/C, controles e isolamento:** A nos 7; B só ordem; C identidade = VOCAB_LLM; CTRL_MAIOR e aleatórios verificados;
  nenhum bloqueado; manual = mapa (VOCAB_ATUAL em CG, ES2, IA, SO e TCC); não-CRU sem leitura da taxonomia congelada.
- **Cada worker conferiu o inventário congelado inteiro** (cerca de 25,7 mil arquivos: pacotes, externos, palco e
  snapshots) no início e no fim.

## 6. Reprodução do CRU por ID (sem gold)

- O CRU foi recapturado neste congelamento (P4, origem "nova"); a captura antiga não foi reutilizada.
- Igual à referência W-AB por ID: 350 materiais, 0 divergências, 0 problemas de estrutura.
- 341 chamados; 9 não chamados (`nao_identificado`, meta-materiais). A unidade da 1ª passada é igual à final.

## 7. As sete capturas

Comando `captura.py --capturar`: 14/14 condições, saída 0, 2989 s. Ordem: CRU (o do preflight v5, revalidado) e depois
VOCAB_ATUAL, VOCAB_LLM, CTRL_MAIOR, CTRL_ALEAT_1, CTRL_ALEAT_2, CTRL_ALEAT_3 — um worker isolado por braço, em
sequência, na 1ª tentativa, sem falhas.

| braço | origem | materiais | chamados | não chamados | violações | manual | conteudo_sha | sha256 do arquivo |
|---|---|---:|---:|---:|---:|---|---|---|
| CRU | reutilizada (preflight v5) | 350 | 341 | 9 | 0 | — | `4a57c98e548ef9f4e0b8c9e6a71aa2d3f148b7c14f247f5b0a5be5310fb95ce0` | `07a24d96f85204c3b41472911be3ab28422419c624cadf6e562d07d65f3f6dd7` |
| VOCAB_ATUAL | nova | 350 | 341 | 9 | 0 | CG, ES2, IA, SO, TCC | `623aebcddff76712fae4b7803466733753b40b7a47c4224fbfaa347704c269c5` | `dd7303718e9d6487fa100193dbec005275518686ceb9129e6347ee0f3d8a7f85` |
| VOCAB_LLM | nova | 350 | 341 | 9 | 0 | — | `2695e0b60823ddb3ac6ca3150d86439299cf169f03261232494573e6865d2a3e` | `3fa6fda88f15b19f76ceaf9a0d70cebf60f9de6e5fab60e626c289cc63e69390` |
| CTRL_MAIOR | nova | 350 | 341 | 9 | 0 | — | `55b8d14ec2944a553e9619b8f07a5134b45549a5e23ec78f5d7ef957506cce73` | `4b79a2488a433cc23747e409cfdacdfa85c317ec6b1cfd8c701aa1964f11657d` |
| CTRL_ALEAT_1 | nova | 350 | 341 | 9 | 0 | — | `089c7824000edb0c4a4707767818579d1435c65bf0b10f1f3d87f34c34f47be9` | `ca1eaaba1f359ebef05ab6c2c49d33751ad6cd776569d87d5d4b816dba1cbc88` |
| CTRL_ALEAT_2 | nova | 350 | 341 | 9 | 0 | — | `b363497e2be8d5f8dc305cab5e7982d9cf0820a6cb0590be462ec5a2ac2e24b0` | `260e40980ba4cd380c6f00d53d82e3b7a43b41ce0fe5ee168c5aa2a668a8866a` |
| CTRL_ALEAT_3 | nova | 350 | 341 | 9 | 0 | — | `134ff2387dba05eb5a0425d7d9b3453427b20754977b547d4eaa3d94298bebe4` | `3922bb68e427ae21c7666de3db787460b481050c01d2bc7041d6bd9abb320a39` |

Validações, pelo coordenador e de novo num processo independente:
- validador completo (`valida_historica`) sem problemas nas sete;
- 350 registros por captura, com IDs = inventário congelado;
- mesmo `id_comum` e os insumos do próprio braço; esquema `wad5-captura-1`, modo `capturar`;
- 0 violações; só `.env` negado; hashes de arquivo e de conteúdo = manifesto;
- palcos e snapshots = insumos congelados;
- código, `src/` e distribuições = congelamento no fim; entradas comuns preservadas (árvores inteiras e inventário);
- nenhuma captura parcial, antiga ou misturada: `capturas/` só tem `3fe5d1ff…`, e `falhas/` está vazio;
- os mesmos 9 meta-materiais não chamados em todos os braços, sem chamadas nem scores inventados.

Nenhuma decisão foi comparada entre braços nem contra a régua.

## 8. Manifestos

- `manifesto_capturas_v5.json` (+ `capturas_v5.md`): manifesto final do conjunto, gravado pelo coordenador. Tem hashes
  completos das sete capturas (arquivo e conteúdo) e referências ao congelamento, às entradas, ao preflight, ao
  protocolo (arquivo e `protocolo_sha`), ao código, ao intérprete, ao ambiente declarado, aos insumos e aos snapshots
  por braço e curso.
- `manifesto_pacote_v5.json`: hashes de todos os arquivos deste pacote e dos JSON de `.frzero/wad5_25-09/`, gerado por
  último.

## 9. Worktree e preservação

- HEAD `2589ed5a…`, index vazio, `src/` e `tests/` limpos.
- Rastreados modificados: só `docs/reports/pendencias.md` (alterações anteriores preservadas e a entrada desta tarefa).
- Não versionados desta linha de trabalho: adendos v3 e v4, `wad4_25-09/` e `wad5_25-09/`. Os outros não versionados e
  os 4 stashes existentes ficaram intactos.
- Sem reset, clean, stash, `git add` ou commit. Nenhum processo alheio encerrado.

## 10. Limitações e próximo Gate

- Travas não são sandbox (`os.open`, `mmap`, extensões C, imports); o código importado é conferido por origem e hash.
- O teste herdado frágil ao `PYTHONIOENCODING` (§3) não afeta o harness.
- O Gate de avaliação continua com as pré-condições do W-AD4 (matriz v4 §7), verificadas só com autorização:
  1. bytes da régua = blobs congelados;
  2. herança sem destinos conflitantes;
  3. denominadores por curso;
  4. CRU = 223/249/86 com a régua lida.
- A régua não foi aberta para conferir 223/249/86.
