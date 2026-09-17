# Categoria prova em cópia nova (17/09)

Item 4.2 do handoff de 16/09: reconstruir MF (3 positivos conhecidos) e IA (controle) desde
as fontes, com a categoria prova corrigida na entrada, e medir os quatro eixos. Só depois
disso abrir `orch-fix-defect` em `src/utils/helpers.py:682`. Restrições: 0 chamadas de
LLM ou rede, `src/` intocado, destinos novos em `.frzero/`.

Plano aprovado em Gate 1 (17/09) após revisão estática da Astra, APROVAR COM AJUSTES,
8 ajustes e 4 notas, 0 bloqueios (`c1-3/astra_revisao_plano_4-2_17-09.md`). Nesta página,
`c1-3` significa `docs/reports/_harness-2026-09-04/c1-3`.

## Resultado

Referência = `.frzero/pacote_fontes_15-09` (mesmas fontes, mesmo extrator, mesma captura
Moodle). Novo = `.frzero/pacote_categoria_17-09`. Os dois lados recalculados contra o gold;
ausentes permanecem no denominador. Medido em `c1-3/verificacao_pacote_categoria_MF_IA_17-09.json`.

| curso | categorias alteradas | bloco | unidade | sub_aceito | sub_primário | perdas | aceite |
|---|---:|---:|---:|---:|---:|---:|---|
| MF | 3 (os 3 alvos) | 50 → 53/66 | 61 → 61/66 | 29 → 29/58 | 25 → 25/58 | 0 | ACEITO |
| IA (controle) | 0 | 38 → 38/42 | 39 → 39/42 | 5 → 5/39 | 4 → 4/39 | 0 | ACEITO |

Hipótese de 15/09 (replay temporal: MF 50 → 53) confirmada em build real. Unidade e
subunidade, que o replay não reavaliava, ficaram idênticas.

## MF em detalhe (medido)

- Os 3 alvos `ProvasIndutivas_EspecificaçõesRecursivas{,_Arvores,_Listas}.pdf` passaram de
  `provas` para `material-de-aula` na entrada (`_categoria_17-09.json`: 67 inputs, 3 alterações,
  ZIPs incluídos). No placar, os 3 saíram de bloco vazio para `bloco-05` (gold); unidade
  `unidade-01-metodos-formais` e subunidade `especificacao-de-funcoes-recursivas` já eram
  corretas nos dois lados. 0 previsões alteradas fora dos alvos (comparação individual,
  inclusive errado → errado).
- Controles internos `revisao-p1` e `revisao-p1-gabarito`: categoria `provas` e previsões
  invariantes.
- Derivados: `exams/EXAM_INDEX.md` e `.deeptutor/knowledge/EXAM_INDEX.md` com os 3 alvos
  fora (3 → 0) e os 2 controles dentro (2 → 2), 0 links quebrados. `course/FILE_MAP.md`: 6
  linhas divergentes = linhas 29–31 dos alvos (categoria e grupo "provas e revisão" →
  "teoria base"). `course/FILE_MAP_TRACE.md`: 6 linhas = caminho `raw/pdfs/provas/` →
  `raw/pdfs/material-de-aula/` e tag `tipo:prova` → `tipo:material`. PDFs movidos para
  `raw/pdfs/material-de-aula/`.
- Texto extraído: 19 entradas com texto diferente, 16 só pelo caminho do repositório e 3
  só pela linha `source_pdf` com a categoria; 0 mudanças de conteúdo. Nenhum texto vazio
  fora de ZIP. Estrutura temporal, taxonomia (`units[].slug`, `topics[].slug`) e `options`
  do manifest idênticas; 0 pinos manuais.
- Build: 2.053,77 s (15/09: 3.980,57 s), `calls={}`, `failed_entries=[]`, `completed=true`,
  67 fontes com SHA-256 conferido, captura Moodle com o mesmo hash de 15/09.

## IA em detalhe (controle)

- 0 categorias alteradas (`_categoria_17-09.json`: 61 inputs, 0 alterações). As 4 entradas
  de prova reais (`p2-202401`, `p2-202402`, `prova-1-2024-02`, `prova-1-202402`, 3 PDFs
  distintos) seguem `provas`, com previsões invariantes.
- Placar idêntico nos 4 eixos e 0 previsões alteradas (40 comuns, 2 ausentes, como em 15/09).
- `EXAM_INDEX.md` sem diferença (4 controles → 4, 0 links quebrados); `FILE_MAP*.md` idênticos.
- Texto: 20 entradas diferentes só pelo caminho do repositório; 0 mudanças de conteúdo.
  Estrutura temporal, taxonomia e `options` idênticas; 0 pinos.
- Build: 3.371,18 s (15/09: 3.502,43 s), `calls={}`, `failed_entries=[]`, 61 fontes conferidas.

## Método

1. Driver `c1-3/pacote_categoria_17-09.py`: carrega `pacote_fontes_15-09.py` (captura Moodle
   validada por hash, backfills, rede e Datalab bloqueados) e envolve `pacote.base.main` para
   trocar o destino no momento em que `pacote_fontes_15-09.py:59-62` reescreve `sys.argv`.
   `candidate()` copiado literal de `verifica_categoria_prova_15-09.py:21-26` (importar de lá
   arrastaria `diagnostica_perdas`), com self-check nos 3 alvos e nas 6 sondas sintéticas de
   15/09. Wrapper em `stash_import.auto_detect_category` e em `scan_stash_cards`, restaurados
   em `finally`; registro por input com origem, nome efetivamente classificado, categoria
   original e proposta. `OMP/OPENBLAS/MKL_NUM_THREADS=1` antes dos imports.
2. Inventário sem build antes de gastar os builds: MF 3 alterações, IA 0.
3. Scorer `c1-3/verifica_pacote_categoria_17-09.py`: gates de build (`completed`, `calls`,
   `failed_entries`), fontes/perfil/captura/`skipped`/`html_image_cap` iguais aos de 15/09,
   `options` do manifest iguais, origens iguais e únicas, sem pinos, categorias alteradas
   exatamente iguais ao alvo, controles de prova invariantes, estrutura temporal e taxonomia
   idênticas (divergência marca o eixo não comparável e bloqueia aceite), texto idêntico
   após normalizar caminho do repositório e segmento `raw/pdfs/<categoria>`, texto vazio
   nos dois lados = falha, lado de referência recalculado igual ao JSON de 15/09, perdas
   em qualquer eixo = reprovado, `EXAM_INDEX` sem os alvos e com os controles e sem links
   quebrados, PDFs movidos. Publica sempre; `accepted` só com todos os gates.
4. Hashes protegidos: `c1-3/hashes_protegidos_antes_17-09.json`, 86 arquivos (manifests e
   índices de `pacote_fontes_15-09/*`, `cru_fontes_serial_15-09/*`, `.motor3eixos/*`); os 56
   hashes registrados em 15/09 conferem; drift após os builds: nenhum.

## Limites

- 3 positivos conhecidos antes da regra, sem holdout: o resultado confirma o efeito nos
  casos que motivaram a regra, não valida uma heurística geral.
- Só 2 cursos reconstruídos. SO, ES2, TCC, CG e FR (210 entradas) ficam de fora; o replay
  de 15/09 mostrou 0 mudanças temporais neles, mas replay não é build. Completar custa
  ~110 min seriais (soma dos logs de 15/09).
- MF terminou em 2.054 s contra 3.981 s em 15/09 com as mesmas entradas; a diferença de
  tempo não foi investigada (hipótese: carga concorrente diferente em 15/09).
- A sessão Claude `78faa17a` caiu com "Connection lost mid-response" às 01:15 antes de
  escrever qualquer arquivo; zero efeito colateral, retomada de `active-task.md`.

## Próximo passo

`orch-fix-defect` em `src/utils/helpers.py:682` com Gate 1 próprio e teste vermelho
primeiro; Astra revisa o diff (única chamada da tarefa). Escopo do teste: os 3 nomes MF,
as 6 sondas sintéticas, as 4 provas de IA e as 338 classificações de 15/09.

## Evidências

- `c1-3/pacote_categoria_17-09.py`, `c1-3/verifica_pacote_categoria_17-09.py`
- `c1-3/pacote_categoria_{MF,IA}_17-09.log`
- `c1-3/hashes_protegidos_antes_17-09.json`
- `c1-3/verificacao_pacote_categoria_MF_IA_17-09.json`
- `.frzero/pacote_categoria_17-09/<tutor>/{_categoria_17-09.json,_build_result_15-09.json,_inputs_15-09.json,_capture_inputs_15-09.json}`
- `c1-3/astra_revisao_plano_4-2_17-09.md`
