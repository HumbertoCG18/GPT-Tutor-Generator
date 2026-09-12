**HIPÓTESE — A inclinação por conteúdo se sustenta para navegação curricular; isso não valida automaticamente as 17 etiquetas de `material_gt`.** Evidência: finalidade do tutor e diferença entre fontes descritas no brief §1.

MEDIDO abaixo = dado fornecido no brief; recalculei apenas a aritmética. Não executei motor, replay ou Gemini.

1. **HIPÓTESE — Adotar unidade curricular nos 8 cursos; preservar bloco como vínculo temporal.** Derivar unidade do bloco impõe uma unidade comum a materiais que podem tratar de assuntos diferentes. Porém, chamar esse gold de “data” simplifica demais: os blocos também têm conteúdo, inclusive misto, como SO bloco-06, “sincronização deadlock”. **Evidência:** §1; §2, descrições dos blocos. Usar `|` somente para pertencimento curricular múltiplo comprovado, nunca para esconder divergência entre fontes. Se a régua aceita qualquer unidade do conjunto, `|` também enfraquece o critério de acerto.

2. **HIPÓTESE — Adjudicação por família:**

| Família | Parecer | Evidência e limite |
|---|---|---|
| SO threads/sincronização, 8 | Favorecer `material_gt`: u03. Sustentação mais forte. | §2: plano coloca explicitamente multithreads e comunicação/sincronização em 4.1/4.2, u03; seções concordam. Blocos agregam outros assuntos. |
| ES2 microsserviços, 4 | Aceitar u01 como ruling explícito; não como conclusão independente sobre todo o conteúdo. | §2: ruling de 19/08. O próprio plano inclui implantação em u02; “implantação microserviços contêineres” no bloco-08 torna fraca a regra “microsserviços ⇒ u01”. Seção sozinha não resolve. |
| MF eth2/aws, 2 | Favorecer u02 pelo ruling confirmado. | §2: confirmação de 31/08; bloco-01 “disciplina”, confiança 0,4, oferece pouca evidência curricular. Títulos e ausência de seção não comprovam u02 independentemente. |
| MF t1/t1-thy, 2 | u01 plausível; manter provisório até conferir enunciado e vínculo entre arquivos. | §2: funções recursivas/provadores pertencem a u01, mas a fonte está marcada `proposto-claude`. |
| MF t2, 1 | u02 plausível; manter provisório até conferir enunciado. | §2: invariantes e software de suporte em u02; rótulo `proposto-claude`. **Não existe gold por bloco nessa linha:** é lacuna mais divergência com o produto, não contradição entre dois golds. |

3. **HIPÓTESE — A precedência honesta é adjudicação curricular confirmada → fonte curricular validada → desconhecido.** `material_gt` não deve mandar só por existir: mistura rulings confirmados e propostas. Bloco pode preencher lacunas apenas com validação de equivalência curricular; senão, reportar sua avaliação separadamente. **Evidência:** §1–2. Se o bloco vencer por decisão de produto, a métrica deve se chamar unidade do bloco; preservar os rulings como verdade curricular separada, não rebaixá-los a notas históricas. Aplicar a mesma definição ao CG e aos cursos novos.

4. **MEDIDO — As contas fecham condicionalmente:** 174/190 = **91,6%**; 258/278 = **92,8%**, mantendo a população fixa e trocando os 16 rótulos (§3). **HIPÓTESE:** se t2 passar a integrar essa população como erro, será **258/279 = 92,5%**. Já **23/35 versus 12/35** exige confirmar que os 11 conflitos pertencem aos mesmos 35 casos e mudam exatamente esses acertos; contar 11/17 não comprova essa interseção. Para comparar com 08/09, reavaliar ambos os snapshots no mesmo gold versionado e na mesma população. Queda causada por mudança de gold não é regressão do motor.

5. **HIPÓTESE — Testar exceção curricular verificável, não “texto vence” genericamente.** Candidata: seção específica mapeada ao plano, corroborada pelo material, pode superar unidade herdada de bloco misto ou genérico. “É código/lista” sozinho não discrimina unidade. **Evidência:** SO favorece a candidata; ES2 expõe seu limite (§2). Os 11 conflitos são oportunidades de correção, não evidência independente do gold. A medição anterior favorece estruturalmente “bloco vence”, mas circularidade causal exigiria investigar como o gold foi produzido (§1–3). Adjudicar sem consultar a preferência do motor → congelar régua → replay completo, incluindo perdas fora das 17 e casos independentes → só então código.
