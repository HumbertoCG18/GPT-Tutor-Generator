# Validação externa do regime VOCAB — relatório de preparação (29/09/2026)

**Preparação da validação externa concluída. Nenhum gold novo produzido, nenhum replay dos cursos novos executado e
nenhuma chamada LLM realizada. Aguardando revisão independente do pacote cego, população e pré-registro antes do
Gate 1.**

- **Autorização:** pedido do usuário de 29/09 ("preparação completa antes do Gate 1").
- **Pré-registro:** `docs/reports/2026-09-29-regime-vocab-validacao-externa-preregistro.md` (bloco NORMATIVO, não
  assinado).
- **Artefatos:** esta pasta; hashes em `manifesto_preparacao.json`. Sem commit.

## 1. Resultado principal: a população de generalização está vazia

A regra pré-declarada, aplicada sem olhar nenhuma saída do motor, não seleciona nenhum curso.

| população | cursos | por quê |
|---|---|---|
| generalização (N0) | nenhum | os 5 candidatos N0 são pastas do aluno no OneDrive, sem plano de ensino |
| piloto externo (N1) | nenhum | LSO falha em E4 (21 de 28 com fonte local = 75%); UX falha em E2 (card do plano vazio) |
| smoke descritivo | LR | tutor já processado pelo motor (N2) |

O mínimo (3 cursos N0, 100 adjudicáveis) não foi atingido. Pelo pré-registro (§2.4), a validação de generalização não
começa; o protocolo fica congelado esperando cursos N0, que precisam vir de novos downloads do Moodle (Gate de rede
próprio, sem LLM). Por isso **nenhum pacote cego real foi gerado**: o gerador só foi exercido com fixtures sintéticas.

## 2. Respostas às oito perguntas da revisão

1. **Os cursos são novos e independentes?** Não há curso selecionado. Os dois candidatos novos no disco não são
   independentes:
   - LSO motivou e mediu os recursos F2/F3 (classificação de bloco) e F5 (segmentação de unidade) em 30/08;
   - UX forneceu o fixture de rótulo de seção nos testes do parser do Moodle (junho).
   Nenhum dos dois teve tutor, atribuição de material, gold ou vocabulário. Classificados N1.
2. **A regra foi aplicada sem olhar predição?** Sim. O enumerador lê nomes e bytes de arquivos brutos, tipos de
   módulo do `contents.json` e texto do repositório no commit fixo `bf46d51f`; não abre manifest, taxonomia, timeline,
   sidecar, captura ou placar. A evidência de exposição vem do commit fixo porque a cópia de trabalho já contém os
   documentos desta preparação.
3. **A população é suficiente?** Não. Zero cursos para generalização e zero para piloto.
4. **O pacote é cego?** O gerador só lê fontes brutas permitidas (leitor restrito), a auditoria combina lista negativa,
   allowlist positiva de arquivos e chaves e regeneração byte a byte. Os 12 testes plantam armadilhas reais: campos
   `computed_*`, `links.json` com `sinal/destino`, `manual-review`, tutor vizinho, autor e usuário na API, predição
   renomeada num campo permitido.
5. **O adjudicador tem evidência suficiente?** Recebe materiais publicados (bytes originais), páginas do Moodle, plano
   original e texto, estrutura de seções e rótulos do professor, e a lista de unidades e tópicos do plano. Não recebe
   links externos (não congeláveis), nem blocos (espaço de rótulos produzido pelo motor de timeline).
6. **O pré-registro elimina graus de liberdade?** Fixa antes do gold: população e mínimo, tratamento do mínimo, eixos,
   vazio, meta, excluído, ausente, replicação por hash, denominadores, adjudicador, cegamento, espaço de rótulos e sua
   condição de parada, compilador, prompt, schema, alias e `model_version`, retries, falhas, controles e sementes,
   fonte do staging, captura, determinismo do CRU, veredictos e proibições.
7. **O harness genérico preserva as métricas?** A suíte herdada da VOCAB_LIMPO (87 testes, idêntica byte a byte) passa
   contra o genérico. O avaliador da VOCAB_LIMPO e o genérico, este com dois conjuntos de nomes de braço, dão saídas
   idênticas byte a byte no mesmo cenário. Toda função que existe nas duas versões é idêntica, exceto as declaradas,
   que só mudam por nome de braço ou rótulo (provado por reversão textual).
8. **Geração, controles e avaliação estão congelados?** Compilador, prompt, schema e `src/` são os da VOCAB_LIMPO
   (`src/` sem mudança desde `2589ed5a`); controles com algoritmos idênticos e sementes 1–3; avaliador com os mesmos
   critérios; as escolhas da rodada estão em `generico/rodada_modelo_validacao_externa.json`, validado por teste.

## 3. O que foi feito

| item | arquivo | verificação |
|---|---|---|
| errata do diagnóstico pós-gold | `errata_diagnostico_pos_gold.md` | 6 correções de formulação; números intactos |
| população candidata completa e proposta | `populacao/populacao_candidata.{json,md}` | 16 candidatos, regra aplicada por script |
| regra de seleção | `populacao/regra_selecao.md`, `enumera_candidatos.py` | declarações no topo do script, sha256 no JSON |
| pré-registro | `docs/reports/2026-09-29-...-preregistro.md` | NORMATIVO delimitado |
| schema do gold | `gold/gold_schema.{md,json}` | validador em `generico/gold_externo.py` |
| instruções ao adjudicador | `gold/instrucoes_adjudicador.md` | proíbe LLM; declaração assinada |
| gerador do pacote cego | `pacote_cego/gera_pacote_cego.py` | 12/12 testes |
| estrutura e exemplo sintético | `pacote_cego/estrutura_pacote_cego.md`, `exemplo_sintetico/` | auditoria aprovada |
| pacotes reais | `pacote_cego/manifesto_pacotes_reais.json` | nenhum gerado (população vazia) |
| harness e avaliador genéricos | `generico/` (+ `diff_vocab_limpo_para_generico.patch`) | 116/116 (87 herdados + 29 novos) |
| políticas de modelo, controles, hashes, EOL | `politicas.md` | valores conferidos no congelamento da VOCAB_LIMPO |
| gitleaks | `gitleaks/test_gitleaks_excecao.py` | 3/3 nos modos `--staged` e histórico; sem correção necessária |

Suíte original da VOCAB_LIMPO rodada na pasta dela depois de tudo: 93/93 (nada foi alterado lá).

## 4. Decisões de protocolo tomadas agora (para a revisão contestar)

- **Níveis N0–N3 e E2–E4** com limiares declarados antes das contagens. O LSO entraria no piloto com E4 ≥ 75%; não
  mudei o limiar depois de ver o número.
- **Bloco não rotulado** nos cursos novos; B exige invariância de bloco por ID.
- **Sem referência do CRU**: o P4 registra e a fase de captura recaptura o CRU com decisões idênticas por ID.
- **Staging pelo manifest do build** (compilador desligado), como o produto compila de fato. Na VOCAB_LIMPO a fonte era
  a captura CRU da Fase 1, que não existe para cursos novos.
- **Ligação gold ↔ entry por sha256 dos bytes brutos**, com replicação quando vários entries têm os mesmos bytes.
- **Adjudicador único** (o usuário), cego às predições, não à hipótese; LLM proibido na adjudicação.

## 5. Defeitos achados e corrigidos durante a preparação (antes de qualquer uso)

1. Enumerador: a evidência lida da cópia de trabalho seria contaminada pelos documentos da própria preparação; passou
   a usar o commit fixo `bf46d51f`.
2. Gerador: a allowlist de chaves tratava caminhos do manifesto como campos; a trava de repositório casava por
   substring e recusava a pasta temporária da sessão. Ambos corrigidos, o segundo com teste próprio.
3. Harness: `DATA`/`C13` apontariam um nível acima (pasta mais funda); o staging lia o pacote antes de congelar;
   `rel()` não aceitava caminho fora do repositório. Corrigidos e cobertos por teste.

## 6. Desvio a declarar

- **Um `git fetch` da `origin/main`** (leitura, repositório do próprio usuário no GitHub) para localizar o job de
  segredos do CI e a versão fixada do gitleaks. Nada foi enviado. Nenhum outro acesso de rede.

## 7. Limitações

- Nada do caminho real (build, pacote congelado, preflight, captura, geração, avaliação) foi exercido com curso novo:
  só fixtures sintéticas. A recaptura do CRU e o espelho com gold externo só rodam depois dos Gates.
- A regra N1 é conservadora e mecânica (menções incidentais contam).
- A validação, quando houver cursos, fica restrita ao contexto institucional da PUCRS.
- O texto da revisão independente de 28/09 não estava disponível; a errata vem da reauditoria do executor.

## 8. Próxima decisão (não executada)

1. Revisão independente desta preparação.
2. Sem cursos N0 no disco, escolher a fonte deles: novos downloads do Moodle de disciplinas nunca processadas (Gate de
   rede próprio, sem LLM) e reaplicação da mesma regra.
3. Qualquer mudança de regra (limiares E3/E4, níveis) só pela revisão e antes do Gate 1.

## 9. Estado do worktree

- HEAD `bf46d51f`, sem commit novo; `src/` e `tests/` sem diff; nenhum arquivo rastreado alterado.
- Novos, não versionados: esta pasta e o pré-registro.
- Soltos de outras sessões (preservados): `c1-3/astra_revisao_regime2_17-09.md`, `c1-3/diagnostico_subunidade_17-09.*`.
- 4 stashes preservados.
