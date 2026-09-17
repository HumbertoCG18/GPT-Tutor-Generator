**A C1 ainda não sustenta fechamento integral. O corte de subunidade passa; o gate completo não está demonstrado.**

MEDIDO abaixo identifica contas conferidas ou registros citados; não reexecutei o harness. HIPÓTESE identifica julgamento ou recomendação.

1. **Fechamento item a item**

| Item | Julgamento e evidência | O que basta para encerrar |
|---|---|---|
| 1.1 | **MEDIDO:** diagnóstico registrado; 19 erros confiantes atuais não invalidam o diagnóstico anterior. Brief §2–3. | Fechado; atualizar o saldo. |
| 1.2 | **MEDIDO:** limiar não generalizou. O plano permite encerramento negativo. `plano*:78–82`. | Fechado como hipótese refutada. |
| 1.3 | **MEDIDO:** implementação era condicional: “Só se 1.2 achar ponto”. `plano*:84–85`. | Marcar **não aplicável**, com a refutação. Não exige inventar regra para completar checklist. |
| 2.1 | **MEDIDO:** existe decisão de não implementar; “+1 real” contradiz a correção posterior para “candidato”. `pendencias.md:20,36–40`. | Fechar como alternativa descartada; corrigir a alegação de ganho. Só exigir replay equivalente se quiser alegar ganho efetivo. |
| 2.2 | **MEDIDO:** regra 1 aplicada; regra 2 prejudicial no replay. Brief §2. | Fechado, com as duas decisões explícitas. |
| 2.3 | **MEDIDO:** manter bloco sustentado por 32/36 casos. Brief §2. | Fechado como manutenção da regra; não prova ausência de alternativa melhor. |
| 2.4 | **MEDIDO:** execução registrada, 16 chamadas. Brief §2. | Fechado. |
| 3.1 | **MEDIDO:** FR incluído, régua 251. Brief §2. | Fechado. |
| 3.2 | **MEDIDO:** rotulagem 93/93; avaliação integrada 88/93. Brief §2, linha 3.2. | Separar **gold concluído** de **cobertura incompleta**; pontuar os cinco conjuntos `|` conforme contrato aprovado. |
| `_load_truth` | **MEDIDO:** testes verdes, Gate 2 pendente. Brief §4. | Confirmar diff e commitar; testes não substituem esse gate. |

**MEDIDO:** há conflito de escopo: o plano ainda atribui 3.x à C5, enquanto o handoff cobra Fase 3 na C1. Reconciliar antes de declarar “100%”. Evidência: `plano*:149`; `docs/reports/_archive/2026-09-11-handoff-camada3.md:128–130`.

2. **Gate: passa o número, falta cumprir a conjunção**

**MEDIDO:** 173/192 = **90,104%**, margem **0,104 ponto percentual**. Uma correção confiante→errada dá 172/192 = **89,583%**; um novo erro confiante dá 173/193 = **89,637%**. Nenhum erro adicional cabe sem compensação. Evidência: brief §3, linha subunidade.

**MEDIDO:** o tracker registra unidade 157/157 → 160/162 e dois erros confiantes novos no SO, anteriores ao gold novo do CG. Portanto, atribuir toda ressalva do gate à expansão do gold seria errado. Evidência: `pendencias.md:50–56,64`.

**HIPÓTESE:** declarar “corte de subunidade atingido nesta régua”. Para fechar o gate original, comparar bloco/unidade nos mesmos materiais e gold, resolver regressões e registrar aceite da fila; alternativamente, obter mudança explícita do critério. O plano exige também fila declarada e aceita (`plano*:70–71`). Isso não demonstra generalização para outro curso.

**MEDIDO:** OpenGL explica **dois erros novos**, não cinco: três previsões já divergiam do gold vazio; as duas vazias passaram a divergir. Evidência: brief §3, parágrafo OpenGL.

3. **Próxima campanha: manter C5, corrigir sua justificativa**

**HIPÓTESE:** os dados não justificam trocar para C3. Tampouco demonstram superioridade atual da C5: falta comparação após as correções.

**MEDIDO:** a tabela histórica contém outra inconsistência: **8/71 = 11,3%**, não 14%; **84/277 = 30,3%**, não 34%. Corrigir denominadores ou percentuais antes de reutilizar o argumento. Evidência: `plano*:154–157`.

Ordem recomendada (**HIPÓTESE**); dívidas documentadas no brief §4:

| Ordem | Trabalho | Gate verificável |
|---|---|---|
| 1 | Atualizar artefatos, ainda no fechamento da C1 | Todos exibem mesma versão de produto/gold, bases, exclusões e resultados. |
| 2 | Reconciliar replay CG | Zero divergências inexplicadas contra produto, com versões fixadas. |
| 3 | Adjudicar 16 contradições | 16 decisões com fonte; zero conflitos de oráculo sem resolução. |
| 4 | Gold FR/LR | 29 materiais adjudicados e avaliados; qualquer exclusão explicitada. |
| 5 | Revisão humana da fila CG | Todo item recebe decisão e fonte; remedição distingue mudança de gold e produto. |
| 6 | HTML/vídeo | Denominadores atuais + diagnóstico causal; verificar recuperação do insumo e delta de atribuição separadamente. |

4. **Riscos por dano potencial**

**HIPÓTESE**, com evidência no brief §4–5: **commits locais** primeiro, se forem a única cópia recuperável; falta de push não prova falta de backup. Depois: **gold sujeito a ancoragem**, **CG concentrando erros**, **exclusão dos `|`**, **artefatos antigos**.

**MEDIDO:** CG concentra **27/37 = 73%** dos erros de subunidade. Fonte documental do professor não equivale a confirmação pessoal; adjudicação do usuário continua válida como referência declarada, sem virar validação independente. Os cinco `|` acertam no placar amplo: excluí-los não infla esse resultado, mas deixa a cobertura incompleta. Evidência: brief §2–4.

**HIPÓTESE:** barato agora: atualizar publicações e estados contraditórios. Para commits, verificar recuperabilidade e separar decisão de backup/push da decisão de merge.

5. **Handoff em cinco linhas**

> **MEDIDO:** C1: itens implementados, refutados e não aplicáveis discriminados; Gate 2 ainda pendente (brief §2).  
> **MEDIDO:** subunidade 214/251; confiante 173/192 = 90,104%; gate integral exige resolver a ressalva de unidade (`pendencias.md:64`).  
> **MEDIDO:** CG rotulado 93/93; unidade 84/93, régua integrada 79/88; cinco conjuntos `|` excluídos (brief §2).  
> **MEDIDO:** C5 herda 29 sem gold, 16 contradições, fila CG, insumo e replay divergente; CG reúne 27/37 erros (brief §3–4).  
> **HIPÓTESE:** abrir C5 após fixar versões e reconciliar régua; prioridade sobre C3 mantida como decisão, ganho ainda não medido (`plano*:151,165–166`).

`plano*` = `docs/reports/2026-09-08-plano-confianca-antes-de-acuracia.md`; demais arquivos citados ficam em `docs/reports/`.
