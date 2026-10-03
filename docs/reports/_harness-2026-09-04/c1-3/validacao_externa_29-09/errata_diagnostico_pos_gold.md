# Errata do diagnóstico pós-gold das perdas do VOCAB_LIMPO (29/09/2026)

Corrige formulações de `../vocab_limpo_diag_perdas_27-09/diagnostico_perdas_vl.md` (commit `bf46d51f`), que fica
intacto. Nenhum número, script, JSON ou resultado muda. Origem: reauditoria do executor em 29/09. O texto da revisão
independente sobre a entrega de 28/09 não estava disponível nesta sessão; itens que ela trouxer devem ser somados aqui.

O diagnóstico continua pós-gold: explica mecanismos e não autoriza ajuste. Nenhuma das hipóteses da sua §5 entra no
compilador, no motor ou no protocolo da validação externa (pré-registro, §9).

## E1. "Esses mecanismos estão no motor, não na geração" (§4) — afirmação forte demais

**Correção:** as perdas surgem da interação entre os termos gerados e mecanismos do motor (pontuador, regra "seção
nomeia subtópico", propagação por headings). O vocabulário gerado é a intervenção; sem ele, as 13 perdas não ocorrem.
Não se pode atribuir a causa só ao motor.

## E2. "As 7 recorrentes vêm dos mesmos mecanismos, não dos mesmos termos" — verificado em 5 de 7

**Correção:** a diferença de termos foi verificada nas 5 perdas recorrentes da 1ª passada:
- ES2 `roteiro5/6/7` e `roteiro7-history-service`: `Infraestrutura como código` não está no sidecar histórico;
- CG `slab`: `Slab` não está no sidecar histórico.

Nas 2 recorrentes da 2ª passada (CG `pagina-com-videos-…`, MF `exerciciosisabelle`), os termos que dirigem a
propagação não foram analisados (a ablação cobre só a 1ª passada). Para elas, "não dos mesmos termos" não foi medido.

## E3. Saldo por mecanismo (§3) — a tabela subestima a regra de seção

A tabela classifica cada transição pela origem da decisão final do VOCAB_LIMPO. Por isso as 4 perdas do ES2 aparecem
como "1ª passada", embora o mecanismo seja a 1ª passada impedindo a regra de seção que acertava no CRU_LIMPO.

**Correção:** contando os dois lados, a regra "seção nomeia subtópico" está envolvida em 5 das 13 perdas (4 em que o
CRU_LIMPO acertava por ela e o VOCAB_LIMPO não a acionou; 1 em que o VOCAB_LIMPO a acionou e errou) e em 0 das 101
correções. Os dados já estavam em `saldo_mecanismos_vl.json` (linhas `cru=2a:secao-nomeia-subtopico` e
`2a:secao-nomeia-subtopico`).

## E4. Redação ambígua no mecanismo B

"a unidade vira empate" (MF `exerciciosespecificacao`) deve ser lido como: sem os aliases novos do vencedor, três
tópicos da unidade empatam em 0,159 e a 1ª passada fica sem vencedor; o tópico certo, diluído, fica em 0,14.

## E5. "Tópico certo" na ablação

A ablação usou como tópico certo a predição do CRU_LIMPO, que pertence ao gold. Quando o gold primário tem mais de um
tópico, os demais não foram analisados. Nenhuma das 13 conclusões depende disso, mas a formulação da §1 deve dizer "um
tópico do gold (a predição certa do CRU_LIMPO)".

## E6. Escopo da fidelidade

A reexecução foi exigida idêntica à captura na 1ª passada, nas chamadas posteriores e na subunidade final. Bloco e
unidade finais não foram comparados na reexecução (fora do escopo do diagnóstico da subunidade).
