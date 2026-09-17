# Resposta do astra ao brief v2 do regime cru (2026-09-12, tarde)

Comando: codex exec --profile astra --sandbox read-only --skip-git-repo-check -C <repo> - < brief_codex_astra_regime_cru_v2.md
Modelo gpt-5.6-terra, perfil astra, read-only. 107.729 tokens. Brief: 348 linhas.
Abaixo a RESPOSTA FINAL, verbatim. O transcript de execucao (4.6k linhas de leitura de arquivo) nao entra no repo:
ele ecoa o .mex/AGENTS.md e dispara o guard de anti-padrao Gemini no staged.

---

**A meta deve ser precisão aceita do confiante, com cobertura explícita e proteção da unidade. Primário da subunidade continua como diagnóstico.**

Conferi código e recontabilizei o CSV; não rodei o motor nem alterei arquivos. **MEDIDO** abaixo significa verificado nesses artefatos; proposta de ganho permanece **HIPÓTESE**.

## 1. O problema está bem posto?

**O objetivo do produto, sim. A formulação “maximizar primário no cru”, isoladamente, não.** Um extra validado pelo professor também organiza corretamente um material multitemático. Penalizá-lo como erro operacional confunde preferência editorial com atribuição inválida.

Usaria precisão aceita do confiante como critério principal, acompanhada obrigatoriamente de cobertura automática e tamanho da fila. Unidade errada recebe prioridade sobre subunidade errada; cobertura por unidade revela onde o tutor ficou incompleto. Primário permanece publicado para detectar escolhas excessivamente secundárias. Sem custo de revisão e tolerância a erro definidos, os dados não sustentam um limiar ótimo.

**MEDIDO:** no produto, 178 dos 193 confiantes são aceitos; 154 são primários. Portanto, 24 decisões confiantes são válidas, embora não principais. A cobertura correspondente é 193/251 = **76,9%**. Essa tabela lê o manifest do produto: **não mede a precisão do confiante do cru**. [Placar:5](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/calibra_fila_como_regua_12-09.log:5), [leitura do manifest:54](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/calibra_fila_como_regua.py:54).

Há três correções adicionais no enquadramento:

- **147/251 é uma ablação de aliases, condicionada ao produto.** O replay mantém a unidade calculada e, no modo utilizado, incorpora `code_curation`. “Só código” também mantém esses insumos; apenas restringe aliases. Os números estão reproduzíveis no CSV, mas ainda não representam a execução completa de um curso novo sem LLM. [Regimes:73](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/congela_regua_cru_12-09.py:73), [insumos:146](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/replay_subunidade.py:146).
- **O “teto limpo” continua contaminado na taxonomia.** `--limpo` remove os aliases encontrados no sidecar **manual**; não remove os do LLM. Recontagem da taxonomia atual: 83 aliases de IA coincidem com o sidecar LLM e sobrevivem a essa limpeza. Portanto, corrigir PLANO de 27 para 26 não basta para validar os 87% do SARC como alcance cru. [Limpeza:70](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/mede_fontes_do_professor.py:70).
- **Os 24 transversais não ficam todos fora da régua de unidade.** O carregador primeiro preenche pelo bloco; depois ignora a sobreposição multivalorada. Recontagem: **19 conservam uma unidade do bloco; 5 ficam fora**. Isso limita a interpretação dos 96,7% como precisão curricular. [Carregador:71](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/scripts/eval_entry_unit.py:71).

Preservaria o placar congelado como benchmark de ablação. Não o promoveria a benchmark de autonomia em curso novo.

## 2. Quais padrões novos aparecem? O que são os 24 residuais?

**MEDIDO:** as cinco famílias sobrevivem como descrição, mas precisam de refinamento causal.

A primeira novidade é a **regressão inversa ainda existente**. A matriz completa é:

| Cru → produto | Produto acerta | Produto erra |
|---|---:|---:|
| Cru acerta | 144 | **3** |
| Cru erra | 80 | 24 |

As três perdas são ES2 `microsservicos2`, `microsservicos3` e CG `pagina-com-videos-sobre-manipulacao-de-imagens-61ddde`. Portanto, **80 recuperados − 3 perdidos = 77 líquidos**. Resolver `exercicioduascores` não eliminou todas as regressões. [CSV:123](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/congela_regua_cru_12-09.csv:123), [CSV:223](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/congela_regua_cru_12-09.csv:223).

Outros padrões:

- **Colapso pode nascer ou crescer na segunda passada.** Em IA, há materiais inicialmente sem sinal que terminam em `introducao`. Em TCC, `variacoes` já vence a primeira passada, ambiguamente, e perde depois. Em ES2, `microsservicos` passa de estudo de caso para estilos. Logo, “literal perdido” não significa necessariamente que o scorer nunca encontrou o literal. [CSV:88](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/congela_regua_cru_12-09.csv:88), [segunda passada:331](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/routing/resolver_apply.py:331).
- **Confiança alta pode refletir ausência de concorrência.** `exemplo-com-k-nn` erra com score 0,11 e confiança 1,000. O código calcula confiança pela margem relativa; isso não é probabilidade calibrada de acerto. Não estou propondo novamente piso global de score. [CSV:80](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/congela_regua_cru_12-09.csv:80), [cálculo:245](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/routing/file_map.py:245).
- **Estrutura visual presente, mas ausente do campo de headings.** No HTML de modelagem, `TÉCNICAS DE MODELAGEM` está em negrito; abaixo aparecem CSG e varredura. O extrator de headings só reconhece `#`. **HIPÓTESE:** o detalhe recebe vantagem sobre o agrupador estrutural. Isso merece rastreamento antes de pedir extração melhor. [Material:16](/C:/Users/Humberto/Documents/GitHub/Computacao-Grafica-Tutor/staging/markdown-auto/html/paginas-com-videos-sobre-modelagem-geometrica-f2614a.md:16), [extrator:67](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/extraction/content_taxonomy.py:67).

A família “competição entre níveis” também precisa distinguir **hierarquia curricular declarada** de mera relação semântica amplo/específico. Os slugs sozinhos não provam pai e filho.

Os 24 compartilhados distribuem-se assim:

| Grupo | Quantidade | Evidência | Conclusão sustentada |
|---|---:|---|---|
| CG | 17 | Mistura código, páginas multitemáticas e casos do ruling u04 | Não constitui uma causa única |
| IA | 3 | Java k-NN, MLP-XOR e agrupamento hierárquico | Falhas residuais dentro de famílias em que o produto melhora outros materiais |
| MF | 3 | AFP, `exemplos`, `tiposindutivos` | Ponte ferramenta/conceito e granularidade curricular permanecem candidatas |
| TCC | 1 | Revisão com gold explicitamente vazio | Nenhuma subunidade é resposta válida |

**Seis dos 24 têm gold vazio: cinco CG e um TCC.** Nesses casos, preencher subunidade é precisamente o erro; “achar o primário” não é a tarefa. O ruling de TCC registra isso expressamente. [Gold TCC:7](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/subunit_gt_TCC.csv:7).

Não classificaria os demais como teto de dados ou defeito do motor só pela coincidência dos erros. Inclusive, notas do gold de páginas do CG ainda mencionam login, mas os três Markdown atuais que inspecionei contêm conteúdo acadêmico. **A descrição antiga da captura não serve para diagnosticar a entrada atual.** [Gold CG:90](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/subunit_gt_CG.csv:90), [conteúdo atual:8](/C:/Users/Humberto/Documents/GitHub/Computacao-Grafica-Tutor/staging/markdown-auto/html/paginas-com-videos-sobre-modelagem-geometrica-f2614a.md:8).

Os nove casos u04 permanecem sob a decisão estabelecida. Isso não estende automaticamente o mesmo teto aos outros residuais.

## 3. SARC posicional: circularidade e experimento mínimo

**Reusar SARC nos dois eixos não é circular por si.** É dependência entre sinais. O problema aparece se a subunidade candidata ajuda a escolher o bloco e depois o SARC desse bloco é apresentado como confirmação independente dessa mesma candidata.

O desenho mínimo proposto:

1. **Produzir vínculos sem gold e sem artefatos LLM de atribuição.** Registrar origem de bloco e unidade; separar resultados com pinos manuais.
2. **Congelar esses vínculos entre os braços.** Controle sem SARC na subunidade; tratamento com SARC. Nenhum retorno da nova subunidade para o bloco nessa comparação.
3. **Gerar a proposta SARC contra rótulos do plano e aliases de origem comprovada.** Registrar sessão, trecho discriminante, candidatos e motivo da decisão ou abstenção.
4. **Avaliar depois das decisões.** Precisão aceita do confiante, cobertura, primário e ganhos/perdas nominais, por curso e nos três eixos.
5. **Validar depois pela rota integrada.** A comparação com vínculos fixos isola a contribuição; o rollout completo verifica efeitos sobre bloco e unidade.

A regra de abstenção deve depender de **identificação insuficiente**, não de outro piso global: sessão nomeia só o pai, múltiplos filhos ou sessões discordantes → **SARC não escolhe filho**. Evidência própria do material pode continuar decidindo; sem ela, manter a unidade e deixar a subunidade indeterminada. Concordância entre bloco e subunidade apoiados na mesma sessão não deve contar como duas confirmações.

Os atuais 34/39 do SARC não sustentam previsão de recuperação: a avaliação usa aliases sobreviventes e prefere `manual_timeline_block_id` antes do temporal. [Seleção:117](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/mede_fontes_do_professor.py:117).

Se o gold foi adjudicado pelo próprio SARC, reportar **concordância com a adjudicação curricular**, sem chamar isso de validação independente. A ausência de circularidade também exige rastreabilidade dos insumos; ganho de acurácia sozinho não a prova.

## 4. O que descartar da fila de implementação?

**Os +1/+3/+6 medem alcance adicional do detector, não acertos líquidos de rollout.** Também não são automaticamente somáveis: fontes adicionais podem alcançar os mesmos materiais.

| Fonte | Decisão proposta | Motivo |
|---|---|---|
| `/Title` PDF | Arquivar o resultado; retirar da implementação prioritária | +1 relatado, forte contaminação por template |
| Filename original | Adiar promoção a sinal | Reusar o casador existente quando essa frente entrar; +3 ainda não demonstra benefício operacional |
| `moodle_week_label` | Manter como próximo candidato após SARC | Campo já disponível, com vínculo temporal e conteúdo do professor |
| Ementa/bibliografia | Não abrir implementação nesta frente | Não há ganho material demonstrado para distinguir subunidades |
| `indent`, datas e ordem isolados | Manter no inventário | Existência do campo não estabelece como ele identifica o subtópico |

A concentração do `week_label` em ES2/MF **não prova sobreajuste**. Haveria sobreajuste se a regra dependesse desses cursos, IDs ou respostas esperadas. Uma regra genérica pode ter cobertura concentrada porque os professores fornecem dados diferentes. Sua transferência ainda precisa ser medida. [Inventário:188](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/2026-09-12-handoff-regime-cru.md:188).

“Ementa inútil” é mais forte que a evidência: ausência de consumo pelo parser não prova impossibilidade de ajudar. Ainda assim, não há motivo demonstrado para priorizá-la aqui.

## 5. Como deve nascer o léxico embarcado?

**Determinismo de execução, origem sem LLM e transferência são três alegações distintas.** Um JSON gerado por LLM pode ser consumido deterministicamente. Isso não torna sua origem independente de LLM.

Para o requisito do produto, congelar o conhecimento **antes de receber o curso novo**. Compilar um sidecar com LLM para cada nova disciplina continua exigindo LLM na atribuição dessa disciplina, mesmo que reexecuções usem cache. O compilador atual faz exatamente essa distinção entre cache existente e chamada por unidade. [Compilador:230](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/core/vocabulary_compile.py:230).

Proponho um arquivo versionado pequeno, com termo, relação, contexto de uso, fonte verificável, autoria/revisão e versão. Não uma coleção de associações `palavra → slug` dos sete cursos.

**Relação importa:** “k-NN é um modelo preditivo” não equivale a “k-NN é sinônimo universal do rótulo curricular Modelos Preditivos”. O léxico fornece conhecimento; o plano do professor continua definindo os destinos. Relações ambíguas não autorizam escolher um filho específico.

Para alegar transferência: congelar léxico, normalização e regras antes do gold do curso alvo; excluir desse congelamento aliases e decisões curadas do alvo; avaliar sem ajustes posteriores. LR↔FR testa transferência próxima. Uma avaliação futura deve incluir disciplina ou professor ainda não usado no desenvolvimento. Os sete cursos já examinados continuam úteis para regressão, mas perderam condição de teste cego.

Para alegar determinismo: mesmas entradas, versão e configuração produzem mesmas decisões com rede bloqueada e sem caches de atribuição do curso. **Se houve LLM na autoria, registrar isso; não renomear a proveniência.**

## 6. O que mudaria na ordem aprovada?

O “teto” deve virar **cobertura do detector de nomeação**. `nomeia()` devolve vazio quando há múltiplos candidatos; portanto, “NENHUMA” também pode significar ambiguidade, não ausência de informação. [Detector:249](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/routing/resolver_apply.py:249).

Ajustaria a sequência assim:

1. **Preparar o controle limpo do SARC**, preservando o benchmark congelado e explicitando insumos herdados.
2. **Executar SARC posicional em IA**, com ganhos/perdas e cobertura; depois verificar transferência nos demais cursos.
3. **Rastrear primeira → segunda passada nos literais**, incorporando a higiene de tokens de mídia antes de ampliar doação de headings.
4. **Comparar base × advanced efetivamente consumidos**, com vocab ausente e voter desligado; distinguir ausência de conteúdo de estrutura textual mal aproveitada.
5. **Só então testar léxico congelado**, sobre lacunas identificadas e com curso alvo reservado.

Datalab permanece na fila, mas o tratamento precisa comprovar qual arquivo entrou no scorer: hoje `base_markdown` precede `advanced_markdown`. Sem essa verificação, “Datalab ligado” não identifica a intervenção medida. [Seletor:71](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/artifacts/navigation.py:71).
