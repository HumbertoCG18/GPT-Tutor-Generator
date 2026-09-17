# Resposta do astra ao brief v4 — revisar os achados e plano para a meta 90/90/90 (2026-09-12, noite)

Comando: codex exec --profile astra --sandbox read-only --skip-git-repo-check -C <repo> - < brief_codex_astra_plano_90.md
Perfil astra, read-only. 86.276 tokens. Brief: 256 linhas, com os 3 refutadores ja embutidos.
Abaixo a RESPOSTA FINAL, verbatim. O transcript de execucao fica fora do repo (dispara o guard de anti-padrao).

---

**Astra: 90/90/90 no cru não foi demonstrado; impossibilidade também não.** O produto passa apenas se “90%” significar precisão dos confiantes.

Consulta feita ao agente nativo `gpt-6-astra`. Reproduzi as três configurações, a alavanca de vocabulário, o diagnóstico lexical e a avaliação dos manifests. Nenhum arquivo alterado.

1. **Revisão dos achados: há outra correção além das já registradas.**

   **74/104 reproduziu, mas seis casos têm gold vazio.** Eles exigem ausência de atribuição; acrescentar vocabulário não é a correção indicada. Entre os 98 casos com tópico esperado, são **68/98 = 69,4%** sem o sinal lexical pesquisado.

   O instrumento considera frases dos aliases, mas tokens apenas do **label primário**, com corte de tamanho e prefixos genéricos. Ignora alternativas aceitas nesse diagnóstico. O scorer também usa tokens dos aliases, siglas e outros campos. Portanto, “nada” significa ausência segundo esse instrumento; **não prova ausência de sinal no scorer nem de informação semântica**. [Diagnóstico:66](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/onde_esta_o_rotulo_12-09.py:66), [scorer:1835](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/timeline/index.py:1835).

   **44% não é teto.** Na mesma base: detector alcança 100, motor acerta 99, interseção 79. Os 20 acertos exclusivos do motor e 21 exclusivos do detector invalidam a “folga” por subtração. “Fontes esgotadas” também excede a evidência: restam cinco casos de seção/título/headings sem experimento de regra. Pequeno potencial identificado; ganho ainda desconhecido. [Handoff:733](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/2026-09-12-handoff-regime-cru.md:733).

   SARC-A permanece negativo; perdeu onde decidiu. A abstenção do IA explica ausência de benefício ali, não a perda global. Vocabulário dirigido permanece positivo **dentro da amostra**: reproduzi 201/251 nos dez tópicos e 222/251 nos 36. A seleção usa gold; não demonstra reconstrução independente nem generalização. [Experimento:28](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/alavanca_vocab_por_topico.py:28).

2. **Cobrar 90% de acurácia aceita sobre todos os materiais avaliáveis de cada eixo.**

   Previsão correta = pertence ao conjunto adjudicado previamente. Abstenção não remove material do denominador; vazio conta como acerto quando o gold exige vazio. Publicar primário separadamente. Precisão dos confiantes precisa vir acompanhada de cobertura.

   A reavaliação dos manifests do produto permite calcular também a acurácia total:

   | Eixo | Produto: acurácia total | Produto: precisão dos confiantes | Cru: acurácia total |
   |---|---:|---:|---:|
   | Unidade | 263/284 = **92,6%** | 209/216 = 96,8% | Não medida |
   | Subunidade | 224/251 = **89,2%** | 178/193 = 92,2% | 147/251 = **58,6%** |
   | Bloco | 235/237 = **99,2%** | 188/189 = 99,5% | Não medida |

   Fonte reproduzida: [avaliação:52](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/calibra_fila_como_regua.py:52). Bases diferentes; isso não mede acerto simultâneo dos três eixos.

   Sobre 251, a meta exige **226 acertos**: cru precisa de **+79 líquidos**; produto, **+2**; vocabulário escolhido com gold, **+4**. Se cobrar primário, faltam **121** no cru.

   Unidade e bloco exigem execução integral por configuração. O replay conserva a unidade do manifest e recalcula a subunidade dentro dela; seus 58,6% tampouco são uma medição integral de um pipeline cru. [Replay:139](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/replay_subunidade.py:139).

3. **Seletor: testar uma fila por orçamento; ainda hipótese.**

   Desenho mínimo: priorizar tópicos **sem suporte nos componentes reais do scorer e ausentes do top-2 com score positivo**. Empates em zero não contam. Usar concentração das vitórias entre irmãos como sinal auxiliar; quantidade de materiais potencialmente afetados como desempate.

   Rótulo genérico e razão materiais/tópicos não devem disparar seleção sozinhos. Distribuição desigual pode ser legítima; tópico sem vencedor pode ainda não ter material. Calcular concentração por unidade apenas quando o vínculo material→unidade tiver evidência confiável, para não transformar erro de unidade em suposta carência lexical.

   Selecionar **top-K**, orçamento fixado antes do teste. Entregar ao curador tópico, contexto e trechos representativos; pedir relações termo→categoria justificadas. Não acrescentar aliases para equilibrar contagens.

   **Gold pode entrar na avaliação; não pode orientar seleção, curadoria ou ajuste do curso testado.** Congelar regra, orçamento e prompt; executar em cursos novos; revelar depois o gold independente. Comparar ganho líquido, regressões, esforço e custo contra nenhuma curadoria, seleção aleatória com mesmo orçamento e curadoria completa.

   Os sete cursos já examinados servem para desenvolvimento e regressão. LOCO ajuda, mas não recupera independência depois de desenhar a regra olhando todos. Sem adjudicação independente, mede-se estabilidade e cobertura; não acurácia.

4. **Plano: cinco passos, sem promessa antecipada.**

   1. Fixar contrato de “cru”, proveniência dos insumos e métrica.
   2. Medir o motor completo nos três eixos em cópias novas, separadas da `.ablacao/` congelada.
   3. Comparar curadoria seletiva com curadoria completa.
   4. Avaliar a configuração congelada em cursos externos com gold cego.
   5. Escolher pelo ganho líquido e custo observado.

   Descartar como justificativas: teto de 44%, abstinência como aumento de acurácia, precisão dos confiantes apresentada como acurácia total e ganho com oráculo apresentado como previsão para curso novo. Despriorizar SARC-A e as regras de margem já negativas, sem dado novo.

   Datalab: reproduzi **21/31 aceitos nos dois braços**, três previsões alteradas e primário 16→15. Isso não sustenta comprá-lo para melhorar essa atribuição; também não demonstra inutilidade geral da extração.

5. **Sem API em runtime é diferente de sem preparação por LLM.**

   **Medido:** o replay do produto manteve seus resultados de subunidade com conexões de rede bloqueadas e artefatos existentes. Isso demonstra reutilização local; não mede o custo de preparar um curso novo.

   A compilação já reutiliza cache. Quando precisa gerar vocabulário, o código faz uma chamada por **unidade elegível**, não uma chamada por curso. [Cache:230](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/core/vocabulary_compile.py:230), [geração:252](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/core/vocabulary_compile.py:252).

   **Custo monetário por curso: não medido.** Faltam consumo faturado, tentativas/retries e tempo de curadoria. Não há base para prometer “uma passada offline entrega 90/90/90 por R$ X”.

   O próprio “cru” precisa de nome preciso: hoje remove aliases encontrados no sidecar LLM, mas conserva `code_curation.json` e outros insumos existentes. Não demonstra ausência de toda contribuição anterior de LLM. [Replay:129](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/replay_subunidade.py:129).

   Próximo passo concreto: medir os três eixos com o motor completo, insumos explicitamente classificados e chamadas pagas bloqueadas.
hook: Stop
hook: Stop Completed
tokens used
86.276
**Astra: 90/90/90 no cru não foi demonstrado; impossibilidade também não.** O produto passa apenas se “90%” significar precisão dos confiantes.

Consulta feita ao agente nativo `gpt-6-astra`. Reproduzi as três configurações, a alavanca de vocabulário, o diagnóstico lexical e a avaliação dos manifests. Nenhum arquivo alterado.

1. **Revisão dos achados: há outra correção além das já registradas.**

   **74/104 reproduziu, mas seis casos têm gold vazio.** Eles exigem ausência de atribuição; acrescentar vocabulário não é a correção indicada. Entre os 98 casos com tópico esperado, são **68/98 = 69,4%** sem o sinal lexical pesquisado.

   O instrumento considera frases dos aliases, mas tokens apenas do **label primário**, com corte de tamanho e prefixos genéricos. Ignora alternativas aceitas nesse diagnóstico. O scorer também usa tokens dos aliases, siglas e outros campos. Portanto, “nada” significa ausência segundo esse instrumento; **não prova ausência de sinal no scorer nem de informação semântica**. [Diagnóstico:66](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/onde_esta_o_rotulo_12-09.py:66), [scorer:1835](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/timeline/index.py:1835).

   **44% não é teto.** Na mesma base: detector alcança 100, motor acerta 99, interseção 79. Os 20 acertos exclusivos do motor e 21 exclusivos do detector invalidam a “folga” por subtração. “Fontes esgotadas” também excede a evidência: restam cinco casos de seção/título/headings sem experimento de regra. Pequeno potencial identificado; ganho ainda desconhecido. [Handoff:733](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/2026-09-12-handoff-regime-cru.md:733).

   SARC-A permanece negativo; perdeu onde decidiu. A abstenção do IA explica ausência de benefício ali, não a perda global. Vocabulário dirigido permanece positivo **dentro da amostra**: reproduzi 201/251 nos dez tópicos e 222/251 nos 36. A seleção usa gold; não demonstra reconstrução independente nem generalização. [Experimento:28](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/alavanca_vocab_por_topico.py:28).

2. **Cobrar 90% de acurácia aceita sobre todos os materiais avaliáveis de cada eixo.**

   Previsão correta = pertence ao conjunto adjudicado previamente. Abstenção não remove material do denominador; vazio conta como acerto quando o gold exige vazio. Publicar primário separadamente. Precisão dos confiantes precisa vir acompanhada de cobertura.

   A reavaliação dos manifests do produto permite calcular também a acurácia total:

   | Eixo | Produto: acurácia total | Produto: precisão dos confiantes | Cru: acurácia total |
   |---|---:|---:|---:|
   | Unidade | 263/284 = **92,6%** | 209/216 = 96,8% | Não medida |
   | Subunidade | 224/251 = **89,2%** | 178/193 = 92,2% | 147/251 = **58,6%** |
   | Bloco | 235/237 = **99,2%** | 188/189 = 99,5% | Não medida |

   Fonte reproduzida: [avaliação:52](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/calibra_fila_como_regua.py:52). Bases diferentes; isso não mede acerto simultâneo dos três eixos.

   Sobre 251, a meta exige **226 acertos**: cru precisa de **+79 líquidos**; produto, **+2**; vocabulário escolhido com gold, **+4**. Se cobrar primário, faltam **121** no cru.

   Unidade e bloco exigem execução integral por configuração. O replay conserva a unidade do manifest e recalcula a subunidade dentro dela; seus 58,6% tampouco são uma medição integral de um pipeline cru. [Replay:139](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/replay_subunidade.py:139).

3. **Seletor: testar uma fila por orçamento; ainda hipótese.**

   Desenho mínimo: priorizar tópicos **sem suporte nos componentes reais do scorer e ausentes do top-2 com score positivo**. Empates em zero não contam. Usar concentração das vitórias entre irmãos como sinal auxiliar; quantidade de materiais potencialmente afetados como desempate.

   Rótulo genérico e razão materiais/tópicos não devem disparar seleção sozinhos. Distribuição desigual pode ser legítima; tópico sem vencedor pode ainda não ter material. Calcular concentração por unidade apenas quando o vínculo material→unidade tiver evidência confiável, para não transformar erro de unidade em suposta carência lexical.

   Selecionar **top-K**, orçamento fixado antes do teste. Entregar ao curador tópico, contexto e trechos representativos; pedir relações termo→categoria justificadas. Não acrescentar aliases para equilibrar contagens.

   **Gold pode entrar na avaliação; não pode orientar seleção, curadoria ou ajuste do curso testado.** Congelar regra, orçamento e prompt; executar em cursos novos; revelar depois o gold independente. Comparar ganho líquido, regressões, esforço e custo contra nenhuma curadoria, seleção aleatória com mesmo orçamento e curadoria completa.

   Os sete cursos já examinados servem para desenvolvimento e regressão. LOCO ajuda, mas não recupera independência depois de desenhar a regra olhando todos. Sem adjudicação independente, mede-se estabilidade e cobertura; não acurácia.

4. **Plano: cinco passos, sem promessa antecipada.**

   1. Fixar contrato de “cru”, proveniência dos insumos e métrica.
   2. Medir o motor completo nos três eixos em cópias novas, separadas da `.ablacao/` congelada.
   3. Comparar curadoria seletiva com curadoria completa.
   4. Avaliar a configuração congelada em cursos externos com gold cego.
   5. Escolher pelo ganho líquido e custo observado.

   Descartar como justificativas: teto de 44%, abstinência como aumento de acurácia, precisão dos confiantes apresentada como acurácia total e ganho com oráculo apresentado como previsão para curso novo. Despriorizar SARC-A e as regras de margem já negativas, sem dado novo.

   Datalab: reproduzi **21/31 aceitos nos dois braços**, três previsões alteradas e primário 16→15. Isso não sustenta comprá-lo para melhorar essa atribuição; também não demonstra inutilidade geral da extração.

5. **Sem API em runtime é diferente de sem preparação por LLM.**

   **Medido:** o replay do produto manteve seus resultados de subunidade com conexões de rede bloqueadas e artefatos existentes. Isso demonstra reutilização local; não mede o custo de preparar um curso novo.

   A compilação já reutiliza cache. Quando precisa gerar vocabulário, o código faz uma chamada por **unidade elegível**, não uma chamada por curso. [Cache:230](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/core/vocabulary_compile.py:230), [geração:252](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/core/vocabulary_compile.py:252).

   **Custo monetário por curso: não medido.** Faltam consumo faturado, tentativas/retries e tempo de curadoria. Não há base para prometer “uma passada offline entrega 90/90/90 por R$ X”.

   O próprio “cru” precisa de nome preciso: hoje remove aliases encontrados no sidecar LLM, mas conserva `code_curation.json` e outros insumos existentes. Não demonstra ausência de toda contribuição anterior de LLM. [Replay:129](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/replay_subunidade.py:129).

   Próximo passo concreto: medir os três eixos com o motor completo, insumos explicitamente classificados e chamadas pagas bloqueadas.
