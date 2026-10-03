# Políticas congeladas da validação externa: modelo, controles, hashes e fim de linha (29/09/2026)

Parte integrante do pré-registro (`docs/reports/2026-09-29-regime-vocab-validacao-externa-preregistro.md`, §§8–10).

## 1. Compilador, prompt, schema e modelo

| item | valor congelado | origem |
|---|---|---|
| árvore `src/` | `c2c4fe30ee365125e9d00e951c5dd872e4a6728727c0e92e81e234502fe7d33e` | congelamento da recompilação VOCAB_LIMPO; `src/` sem mudança desde `2589ed5a` (conferido em 29/09) |
| `src/builder/core/vocabulary_compile.py` | `60c830802ccb7f98d156ae9d429a2b1ba6c6cb121194cbc58d227fd98083ce05` | idem |
| `src/builder/runtime/gemini_client.py` | `9635f6aaca5d9a04b60ef38985761a334b55243cbfc0e5025554f45983f98ba1` | idem |
| prompt de sistema (`SYSTEM`) | `99221b05ff584e10a10292c8ccad3dd768d3d069f666b31f63990afb8736bfbc` | idem |
| schema de resposta | `49e06e9e8939a418baecff8be21ec4abdc8f8ae3a978c394a8301f2ddb769630` | idem |
| modelo | `gemini-3.5-flash` (alias, sem versão imutável) | configuração do usuário = default do código |
| parâmetros de geração | não definidos no código (defaults do serviço); sem semente | idem |

**Regras:**
1. Qualquer diferença em `src/`, prompt, schema ou modelo no momento do congelamento da nova recompilação interrompe
   antes da rede. Não se atualiza o esperado para o valor atual.
2. `model_version` é gravado em cada resposta. Todas as respostas da rodada têm de trazer o mesmo `model_version`;
   valores mistos invalidam a geração (sem nova tentativa). O valor é relatado, não comparado com o da VOCAB_LIMPO.
3. **Retries:** só os do próprio produto (5 tentativas em 429/`RESOURCE_EXHAUSTED` e 5xx, espera de 1 s dobrando até
   60 s). São registrados e relatados; não há retry do harness.
4. **Falhas:** uma unidade com erro (resposta sem `parsed`, retries esgotados) torna a geração incompleta. A rodada
   para; não há segunda geração nem complemento manual.
5. **Uma geração oficial**, conferida request a request contra o inventário congelado ANTES do envio; nenhuma escolha
   entre execuções.
6. **Rede:** só o host do Gemini, pelo caminho normal do SDK, com a instrumentação da rodada limpa (não é sandbox de
   rede; ressalva A da revisão de 26/09).

## 2. Controles e sementes

- **Braços:** `CRU_NOVO`, `VOCAB_NOVO`, `CTRL_MAIOR_NOVO`, `CTRL_ALEAT_NOVO_1/2/3` (nomes fixados na configuração da
  rodada; o harness genérico não depende deles).
- **Algoritmos:** `controle_maior`, `controle_aleatorio`, `embaralha_unidade`, `sidecar_de`, `relacoes`,
  `verifica_controle` e afins são os da rodada VOCAB_LIMPO. O teste `test_so_as_funcoes_declaradas_mudam` prova a
  identidade byte a byte de todas as funções que não mudam de nome de braço, e `test_funcoes_mudadas_so_por_nome...`
  prova que as demais só diferem em nomes e rótulos.
- **Sementes:** 1, 2 e 3; orçamento de sorteio `TENTATIVAS_ALEAT = 2000`; unidade sem permutação válida no orçamento =
  controle bloqueado e relatado, sem nova semente.
- **Controle "maior":** mesmas regras da Fase 1 (pares, estrutura e remoções verificadas).
- Nenhum braço, semente ou limiar novo depois do gold.

## 3. Hashes

- **Arquivo:** sha256 dos bytes em disco no momento do registro.
- **Conteúdo canônico:** `comum.sha_json` (chaves ordenadas, separadores fixos, conjuntos como listas ordenadas).
- **Arquivos versionados:** blob git além do sha256. Gold, rótulos e mapa entram no descritor da régua pelo blob, e o
  avaliador só interpreta bytes cujo blob confere (mesmo contrato da Fase 1 e da VOCAB_LIMPO).
- **Congelamentos em cadeia:** preparação (este `manifesto_preparacao.json`) → pacote cego (`pacote_manifesto.json`,
  sha256 no pré-registro assinado) → gold (blob + sha256 + denominadores) → pacote congelado do build → captura →
  recompilação → capturas → espelho → avaliação. Cada elo cita o anterior pelo hash.

## 4. Fim de linha (EOL)

- O repositório tem `core.autocrlf=true` e `* text=auto`: a cópia de trabalho do Windows pode ter CRLF e o blob, LF.
- **Gold:** CSV com LF obrigatório (o validador recusa CR) e sem BOM. Congelado pelo blob; o sha256 do disco é
  registrado junto. Se disco e blob divergirem na leitura, vale o blob, lido por `git cat-file blob`.
- **Régua na avaliação:** sempre pelo espelho endereçado por conteúdo (blob → `git cat-file` → raiz isolada →
  reconferência), desde a primeira leitura. Nunca da cópia de trabalho.
- **Manifestos desta preparação e das rodadas:** valem para os bytes da cópia de trabalho local. Um checkout novo pode
  mudar o EOL dos arquivos de texto; a conferência em outra máquina usa os blobs do git.
- **Pacote cego:** gerado por cópia byte a byte (materiais e plano) e por serialização determinística (JSON com LF,
  `sort_keys`, `indent=1`); o auditor regenera o pacote e exige bytes idênticos.
