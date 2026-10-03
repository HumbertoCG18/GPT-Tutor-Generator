# Regime VOCAB — pré-registro da validação externa (versão para revisão, 29/09/2026)

**Estado: preparação concluída, NÃO assinado.** Nenhum gold novo, nenhum replay dos cursos novos, nenhuma chamada LLM.
Assinatura e congelamento definitivo só depois da revisão independente e do Gate 1. Até lá, mudanças só por decisão
registrada da revisão; depois, nenhuma.

Artefatos da preparação: `docs/reports/_harness-2026-09-04/c1-3/validacao_externa_29-09/` (hashes em
`manifesto_preparacao.json`). Substitui o desenho de 27/09 (`2026-09-27-regime-vocab-validacao-cursos-novos-desenho.md`).

<!-- NORMATIVO:INICIO -->

## 1. Pergunta e tipo de estudo

1.1. **Validação de generalização:** o compilador de vocabulário congelado (o mesmo da rodada VOCAB_LIMPO) melhora a
subunidade primária em cursos que não participaram de nenhum desenvolvimento, sem perda de unidade e sem mudar blocos?

1.2. **Piloto externo (descritivo):** a mesma medição em cursos com exposição só estrutural (N1). Nunca produz
veredicto de generalização; relata números e transições.

1.3. **Smoke descritivo (LR):** só verifica que a cadeia roda num curso fora da população. Nunca produz veredicto.

1.4. Nenhum resultado desta validação é significância estatística. Se houver veredicto de generalização, ele vale
para cursos do mesmo contexto institucional (PUCRS, planos no mesmo formato, Moodle).

## 2. População

2.1. **Regra:** `populacao/enumera_candidatos.py` e `populacao/regra_selecao.md` (sha256 no manifesto). Níveis N0–N3
por evidência no commit fixo `bf46d51f`; critérios E2 (plano local), E3 (≥ 10 adjudicáveis), E4 (≥ 90% com fonte local
congelável); orçamento de 6 cursos por população, ordenado por `sha256("vocab-validacao-externa-2026-09-29|<sigla>")`.

2.2. **Mínimo amostral da generalização:** 3 cursos N0 e 100 materiais adjudicáveis no total (pré-gold). Depois do
gold: pelo menos 80 materiais na população da subunidade primária (soma dos cursos). Abaixo de qualquer desses
mínimos, não há veredicto de generalização; os números são relatados como descritivos.

2.3. **Resultado em 29/09:** generalização = nenhum curso; piloto externo = nenhum; smoke = LR. O mínimo NÃO foi
atingido.

2.4. **Tratamento do mínimo não atingido:** a validação de generalização não começa. O protocolo fica congelado
esperando cursos N0. Fonte de novos candidatos: downloads do Moodle de disciplinas nunca processadas, feitos pelo
usuário ou pelo produto, sob Gate de rede próprio (sem LLM). A população é recalculada pela MESMA regra e pelo MESMO
script (hash congelado), sem consultar nenhuma saída do motor. Nenhum limiar muda para acomodar os cursos disponíveis.

2.5. **Exclusões fixas:** os sete cursos de desenvolvimento (N3); LR (N2) só como smoke; cursos sem plano ou abaixo
de E3/E4 ficam fora até terem as fontes.

## 3. Eixos

3.1. Oficiais: **unidade** e **subunidade primária**. Auxiliar: **subunidade aceita** (relatada; nunca veta nem aprova).

3.2. **Bloco não é rotulado** nos cursos novos: o espaço de rótulos de bloco é produzido pelo motor de timeline, e
entregá-lo ao adjudicador quebraria o cegamento. No lugar das perdas de bloco, vale a **invariância de bloco por ID**
entre CRU e candidato (§11.2).

## 4. Gold

4.1. Schema `gold-externo-1` (`gold/gold_schema.md`, `gold/gold_schema.json`); validação automática
(`generico/gold_externo.py`, `valida`). Arquivo inválido volta ao adjudicador só para correção de forma.

4.2. **Vazio:** `-` = "vazio é a resposta certa" (régua `{""}`). **Meta** (documento do curso inteiro): unidade
avaliada, subunidade fora do denominador. **Excluído** (ilegível, vazio, fora do curso): fora de todos os eixos,
contado e relatado.

4.3. **Material ausente:** material do gold sem entry no build = linha com `eid` None, conta como erro (contrato das
rodadas anteriores).

4.4. **Ligação material ↔ entry:** pelo sha256 dos bytes brutos (`gold_externo.mapa_por_hash`), lendo do manifest do
build só `id` e o arquivo bruto (`raw_target`). Vários entries com os mesmos bytes: a linha do gold é replicada para
cada um (`gold_id = material@eid`). A ligação é feita e congelada depois do gold e antes de qualquer replay.

4.5. **Links externos** não entram no gold (conteúdo não congelável).

4.6. **Denominadores** por curso e eixo: calculados da régua traduzida (`gold_externo.denominadores`) e gravados na
configuração da rodada antes do preflight. Não mudam depois.

## 5. Espaço de rótulos

5.1. `rotulos.json` do pacote cego: `content_taxonomy.build_content_taxonomy` com o texto do plano e nada mais
(sem glossário, headings, materiais ou mapa do curso), com os slugs do produto.

5.2. **Condição de parada:** depois do build, as unidades e tópicos da taxonomia do build (slugs) têm de ser
exatamente os de `rotulos.json`. Qualquer diferença interrompe antes do preflight; o gold não é editado e o caso
volta à revisão.

## 6. Adjudicador e cegamento

6.1. Adjudicador único: o usuário. Sem segundo rotulador; a concordância entre avaliadores não é medida (limitação).

6.2. Pacote cego (`pacote_cego/gera_pacote_cego.py`, versão `pacote-cego-1`): só fontes brutas permitidas; auditoria
negativa (padrões e campos de predição), allowlist positiva de arquivos e chaves, procedência por arquivo e
regeneração byte a byte.

6.3. Instruções (`gold/instrucoes_adjudicador.md`): proibido consultar tutor, build ou saída do motor; proibido usar
LLM ou assistente; proibido discutir materiais com executor, revisor ou terceiros; uma passada; declaração assinada.

6.4. Declaração com qualquer caixa não marcada invalida o gold daquele curso.

6.5. Ordem obrigatória: o build do curso novo só acontece depois do gold congelado. Antes disso não existe saída do
motor para o curso.

## 7. Sequência e condições de parada

1. Revisão independente desta preparação → Gate 1 (população, pacote cego, pré-registro).
2. Geração e auditoria do pacote cego de cada curso selecionado; sha256 do `pacote_manifesto.json` no pré-registro.
3. Entrega ao adjudicador → gold → validação de forma → congelamento (blob + sha256) com a declaração.
4. Build do tutor pelo aplicativo, com o compilador de vocabulário desligado (flag de curso `compile_vocabulary`
   desligada e `TUTOR_NO_VOCAB_COMPILE=1`). Mudança necessária em `src/` = parada.
5. Pacote congelado do build (formato de `.frzero/pacote_fontes_15-09/`), conferência do espaço de rótulos (§5.2),
   ligação material ↔ entry (§4.4), denominadores (§4.6), configuração da rodada congelada.
6. Preflight e captura CRU (harness genérico, sem gold).
7. Staging a partir do manifest do build congelado (`staging_fonte.tipo = "manifesto_do_build"`: a unidade de cada
   entry é a do build, feito com o compilador desligado, como o produto faria), ensaio sem rede, congelamento da
   recompilação (§8).
8. **Gate de rede** → geração única → sanidade sem gold.
9. Captura dos braços; recaptura do CRU com decisões idênticas por ID (§10.3).
10. **Gate de avaliação** → espelho da régua por blob → avaliador congelado + uma execução de conferência idêntica.

Qualquer falha de integridade antes do gold do avaliador: parar, preservar, relatar. Depois da abertura da régua:
preservar o resultado, registrar que o gold foi visto, parar; correção só com Gate novo.

## 8. Compilador, prompt, schema, modelo

Conforme `politicas.md` §1: `src/` `c2c4fe30…`, `vocabulary_compile.py` `60c83080…`, `gemini_client.py` `9635f6aa…`,
prompt `99221b05…`, schema `49e06e9e…`, modelo `gemini-3.5-flash` (alias), parâmetros default, sem semente. Todas as
respostas com o mesmo `model_version`; retries só os do produto, relatados; unidade com erro = geração incompleta e
parada; uma geração, sem escolha.

## 9. Controles e sementes

Conforme `politicas.md` §2: `CTRL_MAIOR_NOVO` e `CTRL_ALEAT_NOVO_1/2/3` (sementes 1, 2, 3), algoritmos idênticos aos
da rodada VOCAB_LIMPO, orçamento de 2000 tentativas, bloqueio relatado sem nova semente.

## 10. Pipeline de captura

10.1. Harness genérico (`generico/`): cópia da rodada VOCAB_LIMPO com cursos, caminhos, braços, denominadores e régua
vindos da configuração (`rodada.py`, `rodada-generica-1`); diff completo em `diff_vocab_limpo_para_generico.patch`.

10.2. Suíte herdada da VOCAB_LIMPO (87 testes, idêntica byte a byte) passa contra o genérico com a configuração
equivalente; saídas do avaliador idênticas às da VOCAB_LIMPO com qualquer nome de braço; 29 testes novos
(`test_generico.py`). Escolhas fixas da rodada em `generico/rodada_modelo_validacao_externa.json`.

10.3. Sem placar publicado do CRU: o P4 registra a captura; na fase de captura o CRU é recapturado num worker novo e
tem de repetir todas as decisões por ID (`confere_determinismo_cru`).

## 11. Avaliação e veredictos

11.1. **A_novo:** VOCAB_NOVO > CRU_NOVO, CTRL_MAIOR_NOVO e cada CTRL_ALEAT_NOVO na subunidade primária total dos cursos
da população. Sinal exploratório; não é significância.

11.2. **B_novo:** ganho positivo de primária; zero perda nos eixos oficiais (unidade e subunidade primária); nenhum
curso regredindo; E nenhuma predição de bloco diferente entre CRU_NOVO e VOCAB_NOVO por ID (`B_rodada` do avaliador
genérico). Qualquer perda ou mudança de bloco reprova. Nenhuma exceção por a perda aparecer nos controles.

11.3. **C_novo:** acertos × 10 > 9 × n, por contagem, em unidade e subunidade primária de cada curso avaliado.

11.4. Métricas, transições, precisão (sobre TODAS as alteradas), geração e seleção: as da rodada VOCAB_LIMPO.

## 12. Proibido depois do gold

Alterar prompt, filtros, aliases, sidecars ou compilador; gerar de novo; mudar sementes, braços ou limiares; excluir
perdas; alterar denominadores, régua, mapeamento ou avaliador; adjudicar o gold de novo.

## 13. LR

Fora da população. No máximo smoke test descritivo, com pacote cego e gold próprios e Gate próprio, sem veredicto.

<!-- NORMATIVO:FIM -->

## 14. Limitações conhecidas

- Adjudicador único, que conhece o experimento (cego às predições, não à hipótese).
- Sem gold de bloco nos cursos novos; bloco só por invariância.
- O mesmo contexto institucional (PUCRS) limita a generalização.
- Alias do modelo sem versão imutável; parâmetros de geração nos defaults do serviço.
- O harness genérico foi testado só com fixtures sintéticas; o caminho de ponta a ponta (build, preflight, captura,
  geração) só é exercido depois dos Gates.
- A regra N1 é conservadora (menções incidentais também contam).
- O diagnóstico pós-gold de 27/09 (e sua errata) viu o gold dos sete cursos; nada dele entra neste protocolo.
