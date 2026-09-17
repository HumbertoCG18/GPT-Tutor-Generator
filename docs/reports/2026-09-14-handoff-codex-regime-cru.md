# Handoff para o Codex: frente "regime cru" do motor de atribuição (14/09/2026)

Documento autocontido para continuar a discussão e o desenvolvimento no Codex. Escrito pelo Claude no fim de 14/09.
"Medido" = rodado e com log no repositório. "Hipótese" = não medido. "Leitura de LLM" = julgamento de modelo, não medição.

## 0. Leia nesta ordem

1. `.mex/AGENTS.md` (identidade, não-negociáveis) e `.mex/ROUTER.md` (onde mora cada fato).
2. Este arquivo inteiro.
3. Sob demanda: `docs/reports/2026-09-12-handoff-regime-cru.md`, a referência detalhada. Todo "§N" citado aqui é seção dele.
4. Estado vivo: `docs/reports/pendencias.md`, blocos "HANDOFF PARA O CODEX", "META REVISTA E AS 3 OPCOES", "ESTADO DA FRENTE
   REGIME CRU EM 14/09" e "MAPA DE CONSOLIDAÇÃO".

Artefato citado sem pasta mora em `docs/reports/_harness-2026-09-04/c1-3/` (abreviado `c1-3/`).

## 1. Em uma frase

O motor cru honesto está em **93,7% bloco, 89,1% unidade e 39,8% subunidade primário**. A subunidade é o buraco. A alavanca que
funciona, a relação termo → tópico no vocabulário, hoje só existe via LLM. As opções sem LLM medidas não fecham o elo. E a medição do
braço LLM ficou inválida: o glossário tem teto de 14.000 caracteres que apaga aliases, um defeito que já afeta o CG em produção.

## 2. Estado do repositório

- Branch `feat/motor-atribuicao`, árvore limpa, 34 commits locais **não enviados** ao `origin`. Push, merge e PR só por ordem
  explícita do usuário.
- **Nenhuma mudança em `src/` nesta frente.** Tudo é harness em `c1-3/` e documentação. Suite registrada no tracker: 2348 passed,
  4 skipped (não rodei de novo em 14/09).
- Cópias de trabalho, gitignored, na raiz do gerador:
  - `.motor3eixos/`: motor dos 7 cursos, **uma configuração por vez**, e `_CONFIG_ATUAL.txt` diz qual. **Hoje contém o braço C
    (LLM), contaminado pelo teto do glossário.** Rodar a baseline de novo antes de qualquer comparação.
  - `.frzero/`: FR construído do zero, um braço por subpasta (`base`, `label`, `sem2a`, `relacoes-relacoes_A_14-09` etc.).
- Tutores-produto são pastas irmãs em `GitHub/`: `Metodos-Formais-Tutor`, `Sistemas-Operacionais-Tutor`, `Inteligencia-Artifical-Tutor`,
  `Engenharia-Software-2-Tutor`, `TCC-Tutor`, `Computacao-Grafica-Tutor`, `Fundamentos-de-Redes-Tutor`. **Não escrever neles.**
- Cursos por sigla: MF, SO, IA, ES2, TCC, CG, FR. São os 7 de desenvolvimento; **nada medido neles é validação inédita**.

## 3. A meta

### 3.1 A meta do usuário (13/09, literal)

> "A ideia é que, o motor fique preciso o suficiente (3 eixos e primário > 95%), mas de maneira crua, ou seja, que o aluno consiga
> apenas processar o arquivo, e com base nas informações que o sistema coleta quando é criado uma matéria (SARC, Plano de Ensino,
> Cards moodle e etc) consiga categorizar tudo, e quando o repo sofre um resync, a mesma coisa acontece com o arquivo novo. O uso de
> LLM ou APIs externas tem que ser totalmente opicional, nenhum eixo ou precisão pode se sustentar com LLM ou APIs [...] E também as
> informações e eixos não podem se sustentar nos gold [...] Outra coisa, o motor tem que ser modular, pois, cada professor tem uma
> maneira de rotular os arquivos. Busco tanto o bloco, unidade e subunidade >= 95%, depois disso, é apenas polimento."

### 3.2 Meta revista proposta pelo astra (14/09): DECISÃO DO USUÁRIO, NÃO ADOTADA

> "Motor local sem modelos nem APIs obrigatórios; buscar ≥95% de precisão nas atribuições automáticas, com ≥80% de cobertura por
> eixo, em cursos inéditos; declaração do professor e LLM serão regimes opcionais, avaliados separadamente."

Veredito sobre a meta original: *"não está demonstrada; os experimentos não provaram impossibilidade"*. O que acompanha a proposta:

- Três regimes, mesma régua: cru automático, cru com declaração do professor, LLM opcional.
- Métricas sempre publicadas por eixo e por regime:
  - acurácia total;
  - precisão automática;
  - cobertura;
  - erros liberados por 100 materiais;
  - acerto conjunto por material.
- Subunidade: primário continua a métrica principal.
- Os 17 erros de desenho da unidade continuam erros.
- Contrato numérico só depois de validar em 6 cursos de professores ainda não usados (≥ 300 materiais) com dois avaliadores.

Fontes: `c1-3/resposta_codex_astra_rever_meta_14-09.md` e §40.1.

## 4. Decisões do usuário: não reabrir

- LLM e API totalmente opcionais: nenhum eixo nem precisão se sustenta neles (§33).
- Nada se sustenta no gold. **Gold só avalia; nunca alimenta aquisição, seleção ou filtro.**
- Motor modular: cada professor rotula de um jeito.
- Resync categoriza arquivo novo pelo mesmo caminho. O aluno só processa o arquivo; curadoria pelo aluno viola esse caminho (§33.6).
- O motor segue o **plano**, não o bloco (§25).
- **Embedding conta como LLM.** O motor roda em máquina fraca: modelo local não é pré-requisito (§39.1).
- Para depois, não agora:
  - OAuth da conta do provedor do próprio usuário no lugar de chave API;
  - fundir os "eixos" de fonte de sinal (datas, SARC, título etc.) seguindo o mapa de 4 camadas (§9 deste arquivo).

## 5. Leis de processo

1. **0 chamadas de LLM nas medições.** O driver bloqueia a rede e conta as tentativas; o log mostra o contador.
2. **Astra (`gpt-6-astra`) só por ordem explícita do usuário**, nunca por decisão do agente.
3. Nunca tocar `.ablacao/` (régua congelada) nem os tutores-produto. Cópias só em `.motor3eixos/` e `.frzero/`.
4. Nada em `src/` sem Gate 1 (plano aprovado) do `orch-*` correspondente. Defeito começa por teste vermelho (`orch-fix-defect`).
5. **Corte declarado antes de rodar.** Protocolo congelado; a primeira resposta de LLM vale; nada é ajustado depois de ver o placar.
6. Comparar material a material, não somas. Publicar os 3 eixos, a base (subunidade = 251), o regime, aceito e primário.
7. **Só conta ganho transferível.** Autodoação (o material que ganha é o próprio documento de onde a relação saiu) é entrada legítima,
   mas não transfere para curso novo.
8. agy: nunca liberar a permissão `command`, nunca `--dangerously-skip-permissions`.

## 6. Placar medido (7 cursos de desenvolvimento)

| eixo (base) | cru honesto | VOCAB (sidecar LLM, sem voter) | PRODUTO (com voter) | 95% exige |
|---|---|---|---|---|
| bloco (237) | **222 = 93,7%** | 221 = 93,2% | 235 = 99,2% | 226 |
| unidade (284) | **253 = 89,1%** | 255 = 89,8% | 263 = 92,6% | 270 |
| subunidade aceito (251) | **142 = 56,6%** | 220 = 87,6% | 224 = 89,2% | 239 |
| subunidade primário (251) | **100 = 39,8%** | 184 = 73,3% | 186 = 74,1% | 239 |

**Cru honesto** = `motor_3eixos_12-09.py --config regua --sem-curadoria-benchmark puro` (§29):
- sem sidecar LLM;
- sem a curadoria que foi escolhida medindo contra a régua;
- com o ruling humano do OpenGL (sem ele: unidade 248, primário 95);
- parte de cópia do produto, e **nunca foi certificado como construível do zero**.

Log `c1-3/bracoC_baseline_14-09.log`, snapshot `c1-3/snapshot_bracoC_14-09.csv`.

Outros números que decidem:
- **Braço V** (18 termos em 2 tópicos do IA, vindos do sidecar LLM), §32:
  - aceito 142 → 175, primário 100 → 134, IA 5/39 → 38/39, zero regressão nos outros eixos e cursos;
  - prova o efeito da relação **fornecida**, não aquisição automática;
  - os 2 tópicos saíram da análise de erro, que usa gold.
- **FR construído do zero** (18 materiais, 0 chamadas): primário 6/18 no cru e 16/18 com vocabulário compilado por LLM (§33.4, §34).
- **Unidade:** dos 31 erros do cru, 17 são divergência de desenho adjudicada (§26).
- **Subunidade:** o IA concentra 34 dos 109 erros (§31).

## 7. Alavancas fechadas por medição

"Fechada" vale **para a versão testada**, não para toda técnica determinística (astra, §40.2).

| alavanca | resultado medido | § |
|---|---|---|
| precedência "texto vence sempre" | −15 cru, −7 produto contra a régua curricular | §25 |
| precedência por método do bloco | +38 dentro da amostra; LOCO fora: −3 cru, −4 produto | §27 |
| regra do título (unidade) | −9 cru, −14 produto | §24 |
| SARC posicional | cru aceito 147 → 141; produto 224 → 209 | §16 |
| abstenção / fronteira | zona grátis tira 20 erros confiantes por 1 entrega; teto 66,3% de precisão com 44,6% de entrega | §15 |
| limpar tokens de mídia da doação | −2 aceito cru, −3 produto | §14.3 |
| Datalab | 0 sem vocabulário no FR do zero; +1 com | §33.4 |
| seletor de tópicos carentes | não seleciona: o baseline "maior unidade" empata ou ganha | §23 |
| engenharia de bundle | 0 no cru: o scorer já lê o corpo inteiro | §31.2 |
| `moodle_label` na subunidade | 0 no FR do zero | §34.3 |
| desligar propagação de headings (`sempropag`) | +2 no FR do zero; nos 7 cursos, 5 ganhos e 5 perdas (CG −3) | §34.4 |
| singular × plural | 0 de 5 | §35 |
| regra de parentesco pai × filho | 8 de 109 erros; nos 8 o filho tem 0 token distintivo | §36, §37 |
| extrator de relações explícitas (braço R) | 3 relações novas, +1 primário, e o +1 é autodoação | §39 |
| regra lexical fraca A | saldo transferível −3, 6 perdas | §40.6–§40.8 |

## 8. As 3 opções do astra, medidas (§40)

O elo que falta é: **nome da categoria do professor → rótulo do plano**. Exemplo: nos slides, "perceptron/MLP" fica sob "tarefas
supervisionadas"; no plano, o tópico é "modelos preditivos", com 0 arquivos literais (§38, §39.7).

Protocolo, com os mesmos elementos em todos os braços, que são independentes:
- **candidatos:** o inventário antes da âncora, `inventario_relacoes_14-09.jsonl`;
- **filtro:** automático, o `classify` do extrator congelado;
- **consumidor:** alias na taxonomia mais o sidecar manual, via `--relacoes`.

**Corte** (fixado antes): ≥ 5 ganhos no primário, ≥ 5 ganhos no aceito e 0 perdas em qualquer eixo.

| braço | relações | bloco | unidade | aceito | primário | perdas | primário transferível | veredito |
|---|---|---|---|---|---|---|---|---|
| base (cru honesto) | 0 | 222 | 253 | 142 | 100 | — | — | — |
| **estrito automático** | 11 | 222 | 253 | 144 | 102 | **0** | **+1** (ES2 `roteiro8`) | ENCERRA; **o único fora de suspeita** |
| A (lexical fraca) | 163 | 222 | 253 | 142 | 99 | 6 (ES2 roteiro4/5/6) | −3 | ENCERRA; pode ter sido atingido pelo teto |
| B (declaração do professor) | — | — | — | — | — | — | — | **bloqueado** |
| C (LLM) | 3.705 | 219 | 237 | 120 | 96 | 87 | −2 | **inválido como medida de efeito** |

- **A** também move 5 materiais **sem gold** do SO (threads, semáforos, sockets) para `5.2 Caracterização`. É dano que a régua não vê.
  No FR do zero, A dá resultado idêntico à base.
- **B** está bloqueado porque:
  - o pacote tem cerca de 1.900 categorias, o que torna irreal a sessão de 30 min por curso;
  - quem simula o professor precisa ser especialista não contaminado, e Claude e astra estão contaminados.

  Formulários prontos: `c1-3/pacotes_mapeamento_14-09/B_<curso>.md`.
- **C** rodou em 20 lotes com `gemini-3.8-flash-high` via agy, cerca de 1,94M tokens, 0 código inventado. Desvios registrados:
  - os tópicos do IA não têm `code`, então o identificador passou a ser o `slug`;
  - 2 lotes saíram inválidos (ES2 120 categorias, TCC 64) e viraram SEM pela regra congelada. No ES2 e no TCC, o C pode subestimar.
- **Auditoria de correção.** Juiz: `claude-opus-4-6-thinking` via agy, sem placar e sem gold. É leitura de LLM.

  | relações auditadas | corretas | ruído | incorretas | indeterminadas |
  |---|---|---|---|---|
  | A: todas as 163 | 68 | 89 | 6 | — |
  | C: amostra de 400, semente 14 fixada antes | 93 | 305 | 1 | 1 |

  A ligação categoria → tópico erra pouco. O que polui é a prosa que o filtro deixa passar.

### 8.1 Por que o braço C não mede o efeito do LLM

A cadeia medida:
1. O reprocess reescreve `.content_taxonomy.json` a partir do glossário (`src/builder/ops/pedagogical_regeneration.py:462`).
2. O `GLOSSARY.md` passa por `clamp_navigation_artifact` com `max_chars=14000` fixo (`src/builder/artifacts/repo.py:1136` e `:1854`),
   e esse corte remove o fim do arquivo.
3. Com milhares de sinônimos, o começo do plano incha o arquivo, e **os tópicos do fim perdem todos os aliases**, inclusive os que já
   tinham.

Tópicos com 0 alias na cópia do braço C: SO 21 de 36, FR 23 de 32, CG 20 de 59, ES2 10 de 21, TCC 8 de 26, IA 5 de 20 (os de
aprendizado de máquina). O MF não foi truncado.

**O braço C mediu o corte, não o LLM.** O CG unidade −14 e o IA 0/0 com 956 relações vêm do corte. O braço A pode ter sido atingido
(o SO recebeu 102 aliases), mas **não verifiquei**: a cópia foi sobrescrita. No FR do zero, o C foi de 6 para 10/18 primário; não
verifiquei se o teto atingiu aquela cópia.

### 8.2 Defeito do produto, independente do experimento

| produto | GLOSSARY.md (chars) | truncado | tópicos com 0 alias |
|---|---|---|---|
| **CG** | **13.974** | **sim** | **14 de 59** |
| SO | 11.665 | não (perto do teto) | 0 |
| TCC | 10.714 | não | 0 |
| FR, MF, IA, ES2, LR | 3,7k a 9,8k | não | 0 |

No CG em produção, o vocabulário de 14 tópicos do fim do plano não chega ao scorer. **O efeito no placar do CG não foi medido.**

## 9. Mapa de consolidação em 4 camadas (astra, 14/09): mapear, não fundir agora

| camada | mecanismos atuais | o que precisa sobreviver à fusão |
|---|---|---|
| **aquisição de vocabulário** (de onde vêm os termos) | seed em `repo.py:1464`; sidecar "do professor" gerado por script; compilação LLM (`src/builder/core/vocabulary_compile.py`); doação de headings (`content_taxonomy.py:603`) | origem, tipo de relação e evidência rastreável; uma origem não valida outra circularmente |
| **vocabulário do curso** (o que o motor lê) | canal do glossário (`repo.py:1713`, `content_taxonomy.py:431`) e aliases espalhados | separar sinônimo, associação curricular (`topic_terms`) e parte literal do rótulo; deduplicar sem apagar proveniência |
| **evidência do material** | título, headings, corpo, `moodle_label` (`entry_signals.py:173`), resumo de código (`code_summarization.py`) | são o **mesmo documento**, não confirmações independentes |
| **estrutura e decisão** | datas/SARC, seção, card, heranças, correções humanas (`src/models/tag_profile.py:159`), precedências (`src/builder/routing/file_map.py:785`) | tempo, pertencimento e autoridade humana **não são vocabulário**; não viram peso único |

Candidatos a sair (§38.5):
- regras de curso em `src/` (`repo.py:1464`, `content_taxonomy.py:258`);
- `domain_cues` e `tool_aliases` sem consumidor;
- doação de headings sem evidência;
- propagação apoiada só na confiança da própria previsão.

Cada retirada exige ablação individual.

## 10. Decisões em aberto (do usuário)

1. **Meta:** adotar ou não a meta revista (§3.2).
2. **Remedição de A e C** com o teto do glossário contornado **só na cópia**: monkeypatch no driver, `src/` intocado, 0 LLM, só tempo de
   motor.
3. **Defeito do glossário no produto:** `orch-fix-defect`, teste vermelho primeiro, Gate 1 antes de tocar `src/`.
4. **Opção B:** conseguir professor ou especialista não contaminado, ou reduzir o pacote de ~1.900 categorias.
5. **Certificar a construção do zero** dos outros 6 cursos (passo 1 do astra, §33). Hoje só o FR foi construído do zero.

## 11. Próximo passo recomendado (recomendação do Claude, não decisão)

1. **Medir o teto no cru.** Rodar a baseline com o teto desligado só para o glossário, na cópia. Único curso truncado hoje: CG.
   **Hipótese, não verifiquei:** `repo.py:1854` chama `clamp_navigation_artifact` pelo global do módulo, então um monkeypatch em
   `builder.artifacts.repo.clamp_navigation_artifact` no driver bastaria.
2. **Remedir estrito, A e C** contra essa nova baseline, com o mesmo corte. Só então o C diz algo sobre o LLM.
3. **Só depois, Gate 1 do fix em `src/`.** O teto existe porque o `GLOSSARY.md` é artefato de navegação do tutor.
   **Hipótese:** o conserto certo é a taxonomia não ser reconstruída de uma vista truncada, e não simplesmente subir o teto.

## 12. Onde está no código (lido, não alterado)

| o quê | onde |
|---|---|
| clamp dos artefatos de navegação / teto do glossário | `src/builder/artifacts/repo.py:1136`, `:1854` |
| seed com conhecimento de curso (28 regras de termo + 8 dicas de unidade, MF e IA) | `src/builder/artifacts/repo.py:1464-1678` |
| leitura do sidecar de curadoria do glossário | `src/builder/artifacts/repo.py:1713` |
| glossário → aliases do tópico | `src/builder/extraction/content_taxonomy.py:431` (`_glossary_aliases_for_topic`) |
| doação de headings (auto-envenenamento) / cues de MF hardcoded | `src/builder/extraction/content_taxonomy.py:603-646`, `:258` |
| reprocess reescreve a taxonomia | `src/builder/ops/pedagogical_regeneration.py:462` |
| scorer da subunidade: 8 campos, maior peso em headings 4,4 e título 3,8 | `src/builder/timeline/index.py:1797-1943` |
| segunda passada: propagação por headings, partes do rótulo | `src/builder/routing/resolver_apply.py` (`propagar_vocabulario_por_headings`) |
| cascata da unidade (7 saídas; unidade explícita vence o bloco) | `src/builder/routing/file_map.py:785-807` |
| coleta do `moodle_label` | `src/builder/extraction/entry_signals.py:173` |
| hash do resumo de código só olha o bundle, então o cache desatualiza quando o vocabulário muda | `src/builder/core/code_summarization.py:134` |
| correções humanas (só unidade) | `src/models/tag_profile.py` (`learned_corrections`) |

Inventário completo do motor: `c1-3/inventario_motor_2026-09-07.md`.

## 13. Como rodar o harness

Em Git Bash, a partir da raiz do gerador:

```bash
cd docs/reports/_harness-2026-09-04/c1-3
export PYTHONUTF8=1   # obrigatório no Windows para o extrator e os scripts de 14/09

# 1. baseline cru honesto (reescreve .motor3eixos/ inteiro; conferir _CONFIG_ATUAL.txt depois)
python -B motor_3eixos_12-09.py --config regua --sem-curadoria-benchmark puro > bracoC_baseline_14-09.log
python -B snapshot_3eixos_14-09.py --raiz .motor3eixos --saida snapshot_bracoC_14-09.csv

# 2. relações por regime (a partir do inventário antes da âncora)
python -B inventario_relacoes_14-09.py
python -B relacoes_por_regime_14-09.py estrito      # ou A; C exige mapa_C_14-09.json

# 3. braço no motor, snapshot, corte, autodoação
python -B motor_3eixos_12-09.py --config regua --sem-curadoria-benchmark puro --relacoes relacoes_estrito_14-09.json > braco_estrito_7cursos_14-09.log
python -B snapshot_3eixos_14-09.py --raiz .motor3eixos --saida snapshot_braco_estrito_14-09.csv
python -B compara_snapshots_14-09.py --base snapshot_bracoC_14-09.csv --braco snapshot_braco_estrito_14-09.csv
python -B autodoacao_14-09.py estrito

# 4. o mesmo braço no FR construído do zero (.frzero/)
python -B braco_frzero_13-09.py --braco relacoes --relacoes relacoes_estrito_14-09.json
```

Outras flags do `motor_3eixos_12-09.py`:

| flag | efeito |
|---|---|
| `--config nu\|regua\|vocab\|produto` | configuração |
| `--cursos TCC,SO` | subconjunto de cursos |
| `--so-medir` | remede a cópia sem reprocessar |
| `--veto texto\|fonte` | origem do veto |
| `--devolve-vocab "IA:..."` | braço V |
| `--braco-motor sempropag` | desliga a propagação de headings |

`braco_frzero_13-09.py --braco` aceita `base`, `label`, `sem2a`, `sempartes`, `sempropag` e `relacoes`.

Braço C e auditoria:

```bash
python -B pacote_mapeamento_14-09.py            # gera pacotes_mapeamento_14-09/ (B_, C_, ids_)
# um lote (forma da receita; a linha exata usada não ficou gravada em arquivo):
{ cat prompt_C_mapeamento_14-09.md; cat pacotes_mapeamento_14-09/C_IA_1.md; } \
  | agy --model gemini-3.8-flash-high --output-format json --json-schema schema_C_mapeamento_14-09.json \
  > respostas_C_14-09/C_IA_1.json
python -B monta_mapa_C_14-09.py                 # regras congeladas -> mapa_C_14-09.json (ignora os FALHOU arquivados)
python -B relacoes_por_regime_14-09.py C
python -B auditoria_relacoes_14-09.py monta relacoes_C_14-09.json   # >400 relações: amostra de 400, semente 14
# juiz via agy: auditoria_C_entrada.md inline pelo stdin + auditoria_schema_14-09.json -> auditoria_C_resposta.json
python -B auditoria_relacoes_14-09.py consolida C
```

## 14. Delegação e armadilhas conhecidas

Receita completa: `.mex/patterns/delegar-codex-agy.md`.

- **Astra, só por ordem do usuário:**
  `codex exec --profile astra --sandbox read-only --skip-git-repo-check -C "<gerador>" - < c1-3/brief_codex_astra_<tema>.md > c1-3/resposta_codex_astra_<tema>.md`.
  Para esforço menor, acrescentar `-c model_reasoning_effort=low`. O brief leva a tabela pronta de um script reproduzível: o astra
  julga, não explora. Quando a cota acaba, o `codex exec` trava sem saída.
- **agy em tarefa de contagem ou classificação:** mandar o insumo **inline pelo stdin** e escrever "não use nenhuma ferramenta". Com
  `-p` e leitura de arquivo, Gemini e Opus tentam rodar `command`, que é negado.
- **`status: SUCCESS` não prova saída.** Conferir `denied_actions` vazio e fazer parse do `response`. Já veio JSON dentro de cerca
  `json`, fragmento duplicado e raciocínio vazado; pela regra congelada, isso é inválido e vira SEM.
- **Cota do agy:** `MSYS_NO_PATHCONV=1 agy -p "/quota"`. A cota é por grupo (Gemini × "Claude and GPT"), não por modelo.
- **Git Bash:** crases e heredoc quebram `python -c`. Escrever o script em arquivo e rodar o arquivo.
- **`.git/index.lock`:** o hook do graphify às vezes segura o lock. Esperar; não apagar.
- **Identificadores de tópico:** os tópicos do IA não têm `code`, então o identificador é o `slug`. E o slug **não** é único no curso:
  o SO repete `conceitos-basicos` e `estudo-de-casos`.
- **Extrator:** `extrator_relacoes_14-09.py:123` só ancora `kind == "topic"`, então nenhum subtópico pode ser alvo. As 25 candidatas
  da §39 foram contadas depois da âncora (`:171`).

## 15. Índice de relatórios e artefatos

### Documentos vivos
| arquivo | para quê |
|---|---|
| `docs/reports/pendencias.md` | tracker vivo; estado, alavancas fechadas, mapa de 4 camadas |
| `docs/reports/2026-09-12-handoff-regime-cru.md` | referência detalhada §1–§41, com número, log e verificação de cada rodada |
| `docs/reports/2026-09-08-plano-confianca-antes-de-acuracia.md` | plano de 08/09 a revisar antes de executar |
| `.mex/context/audit-2026-09-07.md` | retrato verificado do sistema (o que existe, o que é inerte) |
| `c1-3/inventario_motor_2026-09-07.md` | quem decide cada eixo |
| `.mex/patterns/delegar-codex-agy.md` | receitas e armadilhas de Codex, astra e agy |

### Drivers de medição (0 chamadas)
| arquivo | para quê |
|---|---|
| `motor_3eixos_12-09.py` | motor inteiro em `.motor3eixos/`, por configuração e braço, rede bloqueada e contada |
| `mede_3eixos_12-09.py` | agregados dos 3 eixos e natureza dos erros de unidade |
| `snapshot_3eixos_14-09.py` | 3 eixos material a material (CSV) |
| `compara_snapshots_14-09.py` | ganhos e perdas por eixo e curso, e o corte |
| `autodoacao_14-09.py` | separa autodoação de ganho transferível; lista mudanças em material sem gold |
| `braco_frzero_13-09.py` | braços no FR construído do zero (`.frzero/`) |
| `congela_sidecars_13-09.py`, `sem_curadoria_benchmark_13-09.*` | cru honesto: sidecars por entrada e proveniência (§29) |

### Relações e mapeamento (14/09)
| arquivo | para quê |
|---|---|
| `extrator_relacoes_14-09.py` | extrator congelado do astra, verbatim (§39) |
| `inventario_relacoes_14-09.{py,jsonl,log}` | candidatos antes da âncora; ligações estrita e A (§40.4) |
| `relacoes_por_regime_14-09.py` → `relacoes_{estrito,A,C}_14-09.json` | relações por braço: 11, 163 e 3.705 |
| `relacoes_auditadas_14-09.json` | as 3 relações do braço R, com auditoria manual do astra (§39) |
| `pacote_mapeamento_14-09.py`, `pacotes_mapeamento_14-09/` | pacote comum de B e C: `B_<curso>.md`, `C_<curso>_<n>.md`, `ids_<curso>.json` |
| `prompt_C_mapeamento_14-09.md`, `schema_C_mapeamento_14-09.json` | prompt e schema congelados do C |
| `respostas_C_14-09/` | 20 respostas do C e as falhas arquivadas (`*.FALHOU-ferramenta.*`, `*.FALHOU-sem-codigo.*`) |
| `monta_mapa_C_14-09.py` → `mapa_C_14-09.json` | mapa categoria → tópico do C, com contagens por curso |
| `auditoria_relacoes_14-09.py`, `auditoria_{A,C}_14-09.{json,log}`, `auditoria_C_ids.json`, `auditoria_schema_14-09.json` | auditoria de correção sem placar |

### Logs e snapshots dos braços (14/09)
| arquivo | braço |
|---|---|
| `bracoC_baseline_14-09.log`, `snapshot_bracoC_14-09.csv` | base (cru honesto) |
| `bracoR_7cursos_14-09.log`, `snapshot_bracoR_14-09.csv`, `compara_bracoR_x_C_14-09.log` | R (§39) |
| `braco_estrito_7cursos_14-09.log`, `snapshot_braco_estrito_14-09.csv`, `compara_braco_estrito_x_C_14-09.log` | estrito automático |
| `braco_A_7cursos_14-09.log`, `snapshot_braco_A_14-09.csv`, `compara_braco_A_x_C_14-09.log` | A |
| `braco_C_7cursos_14-09.log`, `snapshot_braco_C_14-09.csv`, `compara_braco_C_x_C_14-09.log`, `autodoacao_C_14-09.log` | C (inválido, §8.1) |
| `braco_frzero_relacoesA_14-09.log`, `braco_frzero_relacoesC_14-09.log` | FR do zero com A e com C |

### Subunidade, vocabulário e FR do zero (13/09)
| arquivo | § |
|---|---|
| `teto_aquisicao_13-09.{json,csv}`, `erros_subunidade_cru_honesto_13-09.*`, `dossie_erros_subunidade_13-09.py` | §30 |
| `evidencia_fora_do_bundle_13-09.py` | §31 |
| `braco_V_13-09.log` | §32 |
| `diagnostico_frzero_13-09.py`, `braco_frzero_{base,label,sem2a,sempartes,sempropag}_13-09.log` | §34 |
| `sempropag_7cursos_13-09.log`, `transicoes_sempropag_7cursos_13-09.*` | §34.4 |
| `scores_pai_filho_13-09.py`, `pai_filho_topicos_13-09.csv`, `brief_agy_pai_filho_13-09.md`, `pai_filho_schema_13-09.json` | §36–§37 |
| `loco_texto_vence_13-09.*`, `texto_x_bloco_curricular_13-09.*`, `texto_vence_{cortes,janela}_13-09.*` | §25–§27 |

### Pareceres do astra (`brief_codex_astra_<tema>.md` → `resposta_codex_astra_<tema>.md`)
| tema | § |
|---|---|
| `aquisicao_vocabulario` (e `_corrida2`) | §28 |
| `motor_cru_95` | §33 |
| `plural_subunidade` | §35 |
| `revisa_pai_filho_13-09` | §36 |
| `relacao_termo_topico` | §38 |
| `extrator_relacoes` | §39 |
| `rever_meta_14-09` | §40 |

Anteriores a 13/09: `regime_cru`, `regime_cru_v2`, `3eixos`, `plano_90`, `cru_como_subir`, `atacar_subunidade`, `contradicoes_unidade`,
`regressao_unidade`, `fr_sem_gold`, `gold_unidade_cg`. Históricos: `camada3`, `estado_c1`, `fase1`, `fase2`.

### Leituras do agy
| arquivo | para quê |
|---|---|
| `brief_agy_refuta_hipotese_vocabulario.md` → `resposta_agy_{gemini-3.1-pro-high,gpt-oss-120b-medium,claude-opus-4-6-thinking}.json` | 3 refutadores (§31) |
| `resposta_agy_pai_filho_*.json` (com `*.FALHOU-command.json` arquivados) | contagem pai × filho (§36) |
| `brief_agy_atualiza_pendencias_14-09.md` → `resposta_agy_pendencias_14-09.json` | bloco de estado do tracker redigido pelo Gemini 3.8 |

## 16. Afirmações já corrigidas (não repetir)

| afirmação errada | correção | § |
|---|---|---|
| "a única dependência de gold é o prompt v2" | +4 de subunidade vinham de curadoria escolhida medindo contra a régua | §29 |
| "os 10 da unidade são vocabulário" | régua → vocab = +2; o voter dá +8 | §28 |
| "teto da aquisição = 32" | era piso; o braço V deu +33 | §32 |
| "23 erros com evidência fora do bundle" | 12 no teste determinístico; bundle entrega 0 no cru | §31 |
| "15 zips sem texto" | recebem resumo determinístico `determ-v3` | §34.1 |
| "a unidade não tem cascata" | tem 7 saídas | §33.2 |
| "singular × plural recupera 5" | recupera 0 | §35 |
| "36 regras seed" | 28 de termo + 8 dicas de unidade | §38.2 |
| "slug é único no curso" | o SO repete slugs | §36.3 |
| "o scorer não lê `moodle_label`" | em zip, o sintetizador põe o label no título | §38.2 |

## 17. Primeira mensagem sugerida para o Codex

```
Leia .mex/AGENTS.md, .mex/ROUTER.md e docs/reports/2026-09-14-handoff-codex-regime-cru.md inteiro.
Estamos na frente "regime cru" do motor de atribuição. Não mude src/ nem rode medição ainda.
Resuma em 5 linhas o estado e as decisões em aberto da §10, e diga qual atacaria primeiro e por quê,
separando o que está medido do que é hipótese. Medições com 0 chamadas de LLM; astra só por ordem minha.
```
