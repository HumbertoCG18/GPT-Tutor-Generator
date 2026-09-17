**HIPÓTESE: corrigir a medição antes de escolher SARC; “cru ≤77%” não está demonstrado.** Evidência: §4 mistura cobertura lexical, taxonomia possivelmente contaminada e outra régua.

MEDIDO abaixo = dados fornecidos, aritmética conferida ou leitura estática; não executei o motor.

1. **MEDIDO — o “teto” mede o alcance de um detector específico.** O script testa frase literal em PLANO, limita HEADINGS aos primeiros 12 e chama o resolvedor nas demais fontes. `AL-HEADING` recebe aliases restantes, sem verificar sua origem; `SEM-CURADO` exclui a coluna curada, mas limpa a taxonomia das demais fontes somente com `--limpo`. O log apresentado não identifica esse modo. Evidência: [script:109](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/mede_fontes_do_professor.py:109), [script:118](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/mede_fontes_do_professor.py:118), §4.

   **HIPÓTESE — nem 77% garante atingibilidade, nem NENHUMA prova necessidade de conhecimento externo.** Há seleção da fonte correta com ajuda do gold, conflitos entre fontes e falsos negativos possíveis por radical, sigla, sinônimo do plano ou descarte de token. Ementa, bibliografia, arquivo e ordem do Moodle merecem inventário; pasta do stash só com proveniência anterior à atribuição. **MEDIDO:** complemento de SEM-CURADO = **51/222**, não 48; NENHUMA complementa QUALQUER. Evidência: §4.

2. **MEDIDO — predominam trocas: 95/112, ou 84,8%.** Famílias relevantes:

   | Família | Evidência medida (§3) | HIPÓTESE a testar |
   |---|---|---|
   | Colapso num candidato | IA: 34 erros → introdução; SO: cinco → escalonamento | Prior, desempate ou pontuação domina evidência específica |
   | Competição entre níveis | TCC: variações → máquinas de Turing; ES2: microsserviços → estilos | Rótulo amplo vence filho explícito |
   | Ponte entre código e conceito | FR: quatro exemplos TCP/UDP → cliente/servidor | Evidência de implementação não chega a sockets |
   | Literal aparentemente perdido | MF: hoare; ES2: microsservicos; TCC: variacoes | Auditar candidatos, normalização e veto da regra já existente |
   | Resíduo pouco ajudado pelo produto | CG: 23 dos 33 erros compartilhados | Separar extração, granularidade do gold e material multitemático |

   **MEDIDO — falta a coluna gold; produto errado não informa o destino correto.** Não dá para confirmar pares predito×gold nem afirmar defeito na regra de título. Os slugs truncados também impedem identificação inequívoca. Evidência: §3.

3. **HIPÓTESE — SARC posicional merece experimento, condicionado à sobrevivência dos 95% sem aliases contaminados.** Evidência: §4 e limpeza acima. Fixar vínculos material→bloco→unidade produzidos sem gold; separar pinos manuais; comparar com/sem SARC e avaliar contra gold independente. Reusar SARC em dois eixos não constitui circularidade sozinho; gold ou vínculo derivados da resposta esperada constituem.

   **HIPÓTESE — sessão que nomeia pai não autoriza escolher filho.** Medir correspondência única, ambiguidade e conflito com título; manter resultado indeterminado quando necessário. Perda numérica não é estimável aqui; sobreposição indiscriminada já perdeu 13 em outro sinal. Evidência: §5.

4. **HIPÓTESE — ordem: auditoria da régua → SARC limpo → regra existente de título → headings → Datalab → léxico.** Evidência: §§4–6. Descartaria a proposta de **peso global adicional** ao título sem rastrear por que a precedência existente falhou.

   Datalab: comparar os mesmos materiais com extração básica/avançada, **vocab ausente**, voter desligado e demais sinais fixos. “Vocab fixo” contendo LLM mede outro regime. Os 163 disponíveis exigem resultado separado da cobertura total; oito cursos exigem régua de LR. FR não sustenta ganho geral: mostrou zero sem vocab. Evidência: §§5–6.

   **HIPÓTESE — LR↔FR testa transferência, não independência de LLM.** Congelar léxico e mapeamento antes de examinar gold/erros do destino; proibir ajustes no destino. Se gerado por LLM, descrevê-lo assim: determinístico em execução, origem LLM. Evidência: §6.3.

5. **MEDIDO — o ponto de partida primário é 38,6%, contra 55,4% aceito: 42 materiais diferem.** Produto recupera 79, mas ganha 78 líquidos: há **uma regressão inversa** omitida da triagem. Logo, examinar todos os 251, não só os 79. Evidência: §2.

   **HIPÓTESE — separar curadoria válida, curadoria derivada do gold e ausência de curadoria.** A remoção atual por igualdade textual pode apagar alias legítimo coincidente; não prova limpeza por proveniência. Evidência: [replay:35](/C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/replay_regime_cru_12-09.py:35).

   **HIPÓTESE — resolver primeiro as duas divergências CG declaradas no §7.6; depois congelar avaliação primária e aceita, incluindo perdas individuais.** “≥+3 sem perda” serve como filtro inicial, não como garantia após ajustar várias regras na mesma régua.
