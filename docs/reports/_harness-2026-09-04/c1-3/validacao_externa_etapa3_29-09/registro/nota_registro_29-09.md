# Nota de registro sobre a etapa 2 (29/09/2026)

Os artefatos da etapa 2 ficam como estão (`../../validacao_externa_etapa2_29-09/`); esta nota os complementa.

1. **A correspondência parcial de nomes estendeu o manifesto.** `manifesto_aquisicao.json` (sha256 `e0c541cc…`) diz
   só "corresponde a curso conhecido". A implementação usou nome normalizado igual e, na falta, nome contido/contendo
   o de um curso conhecido; esse segundo critério não está no manifesto e foi decidido pelo executor. Ele excluiu um
   curso (Engenharia de Software I, id 89045).
2. **Engenharia de Software I não foi demonstrada equivalente a ES2.** A exclusão foi por cautela, pelo critério do
   item 1. A verificação local desta etapa (`../exposicao/resumo_exposicao.md`) acha 221 ocorrências do nome, todas
   continuando em "Engenharia de Software II", e nenhuma do id ou do código de ES I. Isso não prova equivalência nem
   independência; a exclusão continua até decisão explícita.
3. **Campos permitidos do catálogo podem conter texto excedente dentro do valor.** O manifesto permitiu o campo de
   nome e excluiu o professor, mas em 2 cursos o valor do nome traz turmas, semestre, modalidade e, em um deles, nomes
   de professores (ids 93730 e 94492). Esse texto está nos originais `catalogo.json` e `triagem.json` da etapa 2, que
   ficam preservados. Cópias redigidas para divulgação, geradas por `redige_divulgacao.py` com o sha256 do original
   em cada uma: `catalogo_divulgacao.json`, `triagem_divulgacao.json` e `../exposicao/exposicao_local_divulgacao.json`.
4. **O resultado de seleção vazia pertence à regra já executada.** "Nenhum curso elegível" vale para a regra v2 da
   etapa 2 (N0–N3, E2–E4, mesmos limiares, E4 com links no denominador) aplicada ao lote de 29/09. Não é resultado de
   nenhuma regra proposta depois; a proposta normativa desta etapa (`../proposta_normativa_populacao.md`) não foi
   aplicada ao lote.

A exceção do gitleaks (commit 71dff722) continua fora deste patch; nenhuma allowlist nova foi criada.
