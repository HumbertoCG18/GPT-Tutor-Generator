# Nota de registro sobre a etapa 2, v2 (29/09/2026)

Substitui, para leitura, `../../validacao_externa_etapa3_29-09/registro/nota_registro_29-09.md` (preservado). A única
mudança de conteúdo está no ponto 2: a v1 afirmava a ausência do id e do código de ES I a partir de uma busca que
guardava só o primeiro match de cada linha.

1. **A correspondência parcial de nomes estendeu o manifesto.** `manifesto_aquisicao.json` (sha256 `e0c541cc…`) diz
   só "corresponde a curso conhecido". A implementação usou nome normalizado igual e, na falta, nome contido/contendo
   o de um curso conhecido. Esse segundo critério não está no manifesto e foi decidido pelo executor. Ele excluiu um
   curso: Engenharia de Software I, id 89045.
2. **Engenharia de Software I não foi demonstrada equivalente a ES2.** A exclusão foi por cautela, pelo critério do
   item 1.
   - A verificação local v2 (`../exposicao/resumo_exposicao_v2.md`) registra todos os matches de cada linha e acha 221,
     todos do padrão de nome e todos continuando em "Engenharia de Software II". O id e o código de ES I não aparecem
     em nenhum match.
   - Isso vale só para as fontes pesquisadas: um commit e nomes de pastas.
   - Não prova equivalência nem independência. A exclusão continua até decisão explícita, e nenhum nível foi alterado.
3. **Campos permitidos do catálogo podem conter texto excedente dentro do valor.** O manifesto permitiu o campo de
   nome e excluiu o professor.
   - Em 2 cursos (ids 93730 e 94492), o valor do nome traz turmas, semestre, modalidade e, em um deles, nomes de
     professores.
   - Os originais `catalogo.json` e `triagem.json` da etapa 2 ficam preservados.
   - As cópias redigidas estão em `../../validacao_externa_etapa3_29-09/registro/` e aqui, em
     `../exposicao/exposicao_local_v2_divulgacao.json`.
   - A redação troca o nome inteiro; não é sanitização geral de fragmentos (limite E3-REG-02).
4. **O resultado de seleção vazia pertence à regra já executada.** "Nenhum curso elegível" vale para a regra v2 da
   etapa 2 (N0–N3, E2–E4, mesmos limiares, E4 com links no denominador) aplicada ao lote de 29/09. Nenhuma proposta
   posterior (P3 e P3.1) foi aplicada ao lote.

A exceção do gitleaks (commit 71dff722) continua fora deste patch; nenhuma allowlist nova foi criada.
