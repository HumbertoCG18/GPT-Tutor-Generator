# Resposta do Codex astra (gpt-6-astra, high, read-only), Fase 1, sessão 01a0920a-5de7-7d22-97ca-cfb83b4393d6, 2026-09-11

**Não fecharia a Fase 1 ainda: subunidade passou; “sem regressão em unidade” depende da baseline.** MEDIDO abaixo = conferência do brief e leitura do código; não reexecutei o motor.

1. **Padrões omitidos.** **MEDIDO — §3:** CG concentra 11/18 erros, mas a descrição mistura grupos: são **8 HTML, 7 abaixo de 2.013 bytes, apenas 4 com score 1,3–4,8**. `desenho-de-linhas` aparece em 3 HTML + 1 ZIP. “Alias por acaso” continua **HIPÓTESE**: tamanho e score não mostram qual alias decidiu.

   **MEDIDO — §3:** os 4 gold vazios têm confiança 0,23; 0,43; 0,91; 1,00. Portanto, `conf < 0,35` captura apenas um; `< 0,50`, dois. **HIPÓTESE:** falta distinguir “qual candidato vence?” de “algum candidato se aplica?”. `tiposindutivos` (score 0,12/conf 0,86) exemplifica essa separação. Encaminhar à fila contém o erro; não implementa abstenção.

   **HIPÓTESE — §3:** ES2 pode exigir contexto pedagógico para distinguir “estudo de caso” do assunto tratado. A lista de erros, sozinha, não identifica a causa.

2. **Varredura: válida como simulação local, insuficiente como validação externa.** **MEDIDO — §4:** a precisão aumenta porque decisões saem do denominador; nenhuma atribuição fica mais correta. Cálculos conferidos:

   | Regra | Precisão restante | Recall da fila, subunidade | Fila total |
   |---|---:|---:|---:|
   | Hoje | 90,6% | 51,4% | 78/348 |
   | `conf < 0,30` | 94,3% | 73,0% | 104/348 |
   | `conf < 0,35` | 95,3% | 78,4% | 111/348 |

   **MEDIDO — §4:** passar de 0,30 para 0,35 captura mais 2 erros, envia mais 3 acertos e acrescenta 7 materiais à fila; 2 ficam fora dessas contagens de qualidade. A combinação `conf < 0,35 ou score < 1,5` supera `< 0,50` nesta amostra: mesmos 12 erros capturados, 4 acertos preservados, 15 revisões a menos.

   **HIPÓTESE:** a escolha pode falhar em curso novo por diferenças de vocabulário, candidatos, formatos e distribuição dos scores. Usar o gold “uma vez” não elimina ajuste: comparar vários limiares já usa seus resultados para escolher. Próxima validação: separar por curso, mantendo lista/gabarito juntos; escolher nos demais e avaliar no curso reservado. Isso testa transferência interna; um curso intocado ainda seria evidência mais forte.

   **HIPÓTESE:** margem + score é candidato justificável, não regra superior demonstrada. Pode operar sem gold; sua qualidade não pode ser comprovada sem rótulos. Evitaria condições específicas para HTML/tamanho antes dessa validação.

3. **Unidade: investigar o par antes de criar limiar global.** **MEDIDO — §3:** são lista e gabarito da mesma atividade, ambos abaixo de 0,30. **HIPÓTESE:** podem representar uma única falha compartilhada, não duas evidências independentes. Sem distribuição dos acertos de unidade abaixo de 0,30, o custo do limiar é desconhecido. Medir captura e fila adicional antes de adotá-lo.

4. **Gate: não confundir meta atingida com detector resolvido.** **MEDIDO — §1:** 174/192 = 90,625%, mas 18/37 erros continuam fora da fila. Contra 08/09, unidade caiu de 100% para 98,8%: o gate histórico não passou. Se a baseline acordada é o produto de 11/09, falta comparar bloco/unidade após a regra; a fila compartilhada pode mudar suas precisões mesmo preservando as atribuições.

   **HIPÓTESE/recomendação:** o item 1.3 tem benefício mensurável, mas não é obrigatório apenas para ultrapassar 90%. Testaria **0,30 primeiro**, pelo menor custo absoluto; aceitação da fila continua necessária. Não declararia “sabe quando está inseguro” com base apenas na média agregada.

5. **Riscos concretos da medição.**

   - **MEDIDO:** a régua enumera **7 cursos**, enquanto o custo informado cobre 8; confirmar a composição das populações. Também soma somente entradas presentes no manifest com gold aplicável. [Régua:23–25,58–67](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/calibra_fila_como_regua.py:23).
   - **MEDIDO:** em `< 0,30`, 26 novas revisões excedem 8 erros + 8 acertos em **10**; em `< 0,35`, a diferença é **12**. **HIPÓTESE:** são entradas sem gold elegível de subunidade; a qualidade desse custo permanece desconhecida (§4).
   - **MEDIDO:** “confiante” inclui ausência de predição; vazio pode acertar gold vazio ou errar gold preenchido. A regra simulada exige subunidade gravada e não captura essas omissões. [Régua:60–67](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/docs/reports/_harness-2026-09-04/c1-3/calibra_fila_como_regua.py:60); §4.
   - **MEDIDO:** `sync_changed` põe na fila qualquer valor textual não vazio; pino manual suprime dúvida de subunidade. `ambiguous=True` sozinho também não basta: o motivo `revisao-sem-assunto-dominante` do §2 não corresponde aos gatilhos aceitos. **HIPÓTESE:** histórico de sincronização, revisão manual e abstenções podem distorcer a leitura de “confiança do motor”. [revisar.py:39–43,69–75](C:/Users/Humberto/Documents/GitHub/GPT-Tutor-Generator/src/builder/routing/revisar.py:39).
hook: Stop
hook: Stop Completed
