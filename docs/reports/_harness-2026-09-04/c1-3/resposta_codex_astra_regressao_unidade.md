**Causa local demonstrada nos dois blocos; recuperação dos materiais e gate global ainda não demonstrados.**

`MEDIDO` abaixo = evidência fornecida no brief, sem reprodução nesta revisão. `HIPÓTESE` = inferência ou proposta ainda não testada. Referências por seção e trecho, pois o brief não numera linhas.

1. **Causa raiz**

   **MEDIDO:** SO: retirar as duas doações troca o vencedor u02→u03; CG: acrescentar somente `OpenGL` em 1.4 restaura u01. Isso demonstra causalidade local da taxonomia, mantendo o motor do replay. Não demonstra que essas foram as únicas mudanças relevantes desde 07/09. [§4, variantes SO e CG]

   **HIPÓTESE:** `herdada_do_vizinho` e `reconciliada_do_bloco` propagam/amplificam o erro; não há evidência de uma terceira causa independente nesses exemplos. O score 39,74 pertence ao material; não valida a unidade do bloco nem é comparável diretamente ao 10,97 do replay. Além disso, manifesto SO mostra confiança 0,6; replay, 1,00: esclarecer a diferença antes de afirmar reprodução completa do caminho. TCC continua sem causa determinada. [§2, lâminas/bloco-09; §4, SO; §1, TCC]

2. **Correção: começar pela taxonomia; regra geral depende das ablações**

| Candidato | Diagnóstico e escolha | Risco / evidência |
|---|---|---|
| F1 | **HIPÓTESE:** defesa contra colisão com curadoria; insuficiência ou suficiência ainda desconhecida, pois mantém `Pipes`. | Contenção pode excluir termos legítimos compartilhados. Preferir comparação normalizada por palavras, evitando substring arbitrária. [§3, filtro; §4, remoção conjunta] |
| F2 | **HIPÓTESE:** exclusividade global não justificada. Não adotar agora. | Alias compartilhado não implica atribuição inválida; conflito LLM×LLM tampouco identifica o dono correto. [§3, `Processos` em tópicos distintos] |
| F3 | **MEDIDO:** retirar o par corrige o bloco no replay. Menor remediação local demonstrada. | **HIPÓTESE:** outros blocos podem perder âncoras úteis. Confirmar que o sidecar realmente exclui as doações da taxonomia mesclada e resiste à recompilação. [§4, SO] |
| F4 | **MEDIDO:** somente `OpenGL` em 1.4 basta para o bloco; respeita o ruling. Escolha para CG. | Recuperação dos materiais ainda pendente; `texturas-v3` continua exigindo u08. [§4, última variante; §1, CG] |
| F5 | **MEDIDO:** restaura u01 pelo tópico errado segundo o ruling. Rejeitar. | Reabre a associação com 1.2 e pode desfazer ganhos do M1. [§3, M1/ruling; §4, restauração em 1.2] |
| F6 | **HIPÓTESE:** trata a propagação, sem corrigir a âncora ausente. Adiar. | Pode privilegiar `auto_unit_slug` fraco e impedir heranças corretas; SO nem depende desse fallback no exemplo. [§2, ambos os blocos] |

   **HIPÓTESE — próxima ablação:** medir primeiro **só “Comunicação entre Processos” fora**, pois testa diretamente a suficiência de F1; depois **só “Pipes” fora**. Comparar com os extremos já medidos: nenhum removido e ambos removidos. [§4, SO]

3. **Teste vermelho mais barato**

   **HIPÓTESE:** começar com regressão parametrizada dos dois blocos, passando pela montagem real da taxonomia com dados locais congelados: SO→u03; CG→u01/Aplicações. Precisa falhar com os dados atuais. Fixture já contendo aliases corrigidos pode passar antes da correção e não proteger o defeito. Se escolher F1, acrescentar teste do filtro: rejeitar a colisão entre unidades e preservar um termo válido. Só o teste do filtro não cobre CG nem propagação aos materiais. [§2–4]

4. **Gate: diff + régua não bastam sem cobertura**

   **HIPÓTESE:** comparar **07/09×corrigido** e **pré-correção×corrigido**, nos oito tutores, com gold congelado, IDs estáveis e resultados regenerados localmente. Conferir unidade **e** subunidade por material; listar perdas individuais, ausências e mudanças sem gold. Ganhos agregados não compensam regressões. Usar `calibra_fila_como_regua` somente após conferir seu universo: os quatro SO precisam entrar na avaliação de unidade. [§1, exclusão da régua]

   **MEDIDO:** são 11 materiais com unidade alterada: nove perdas contra o gold apresentado, um erro persistente e um caso desconhecido. FR 22/LR 7 não têm definição no brief; §1 registra zero mudanças de unidade nesses cursos. Não classificá-los como regressões de unidade. Sem adjudicar mudanças sem gold, declarar apenas **“sem perdas na cobertura avaliada”**. [§1; §5.4]

5. **Risco restante: quantidade desconhecida**

   **HIPÓTESE — medição barata, zero chamadas:** comparar todos os blocos históricos e atuais, incluindo vazios→unidade, unidade→vazio, trocas de vencedor e materiais afetados. Separar blocos novos/removidos dos pareados. Depois, repetir a atribuição sobre entradas atuais fixas com vocabulário LLM ligado/desligado e M1 antes/depois, usando apenas caches locais. O diff mede mudança histórica; o replay separa efeitos das intervenções. Contar blocos alterados, materiais atingidos e cobertura de gold. Mudança de bloco pode ficar invisível no diff dos materiais. [§1, medição restrita a materiais; §3–4, duas intervenções]
