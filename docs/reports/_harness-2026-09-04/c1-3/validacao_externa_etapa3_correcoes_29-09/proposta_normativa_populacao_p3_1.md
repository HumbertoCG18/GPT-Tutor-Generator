# P3.1: proposta de redação normativa da população da validação externa (29/09/2026)

**Status:**

- É só uma proposta de redação; não foi aprovada nem aplicada.
- Nenhuma contagem foi calculada com ela, nem no lote de 29/09 nem no universo local.
- Ela substitui a redação da P3 (`../validacao_externa_etapa3_29-09/proposta_normativa_populacao.md`, preservada) nos
  pontos que o parecer apontou como ambíguos.
- As sugestões do parecer (`sugestoes_redacao_p3.md`) foram avaliadas uma a uma no §8. Nenhuma foi adotada
  automaticamente.

## 0. Transparência **[C]**

- Esta é uma emenda escrita depois de conhecidas as contagens e as causas de inelegibilidade do lote de 29/09 (§0 da
  P3).
- **[C]** marca cada mudança de alvo, unidade, cobertura, exclusão ou mínimo escrita com esse conhecimento. A marca
  informa conhecimento prévio; sozinha, não afirma calibração deliberada.
- Os limiares numéricos preexistentes continuam: E3 = 10, E4 = 90%, 3 cursos e 100 documentos pré-gold, 80 pós-gold.
- Um mínimo pós-gold por curso é **introduzido** (§5): é convenção operacional, sem garantia de precisão estatística.
- A regra v2 e o seu resultado vazio continuam registrados.
- Qualquer análise do lote já inspecionado sob esta emenda é **exploratória/descritiva**. Uma avaliação confirmatória
  exige aquisição prospectiva sob protocolo congelado antes de examinar a elegibilidade ou os resultados dessa nova
  aquisição.
- Aprovar este texto não autoriza aquisição, gold, build nem execução do motor.

## 1. Alvo e links **[C]**

**Alvo operacional:**

- arquivos publicados como conteúdos dos módulos Moodle `resource`, `folder` e `assign`;
- o HTML principal de cada módulo `page`.

Os itens são identificados pela listagem congelada da API e definidos pelo modo de publicação nessa listagem, antes de
considerar disponibilidade, resultado do download, extensão, conteúdo extraído ou predição.

**Fora do alvo e das suas conclusões:**

- módulos `url`;
- anexos de página;
- conteúdo acessado por referência externa.

Não se afirma que esse conteúdo seja inadjudicável ou impossível de congelar. A exclusão decorre do recorte de
aquisição: o protocolo não captura destinos externos sob a mesma cadeia de proveniência.

**Regras da fronteira:**

- vale para qualquer curso;
- não muda quando se conhece a identidade dos bytes ou a utilidade de um link;
- referências externas não são seguidas na aquisição nem na adjudicação;
- links e anexos são descritos à parte (quantidade e domínio, sem parâmetros) e não entram em E3/E4.

## 2. Ocorrências, cobertura e E4 **[C]**

1. Antes do download, congela-se a lista de **ocorrências de aquisição** do alvo. A identidade de cada uma é: curso,
   módulo, tipo de módulo, `filepath` como informado (ausente = ausente, nunca igualado a `/`), nome do arquivo e
   ordinal na lista congelada. Nenhuma ocorrência some por colisão de nome.
2. Cada `page` contribui com uma ocorrência esperada de HTML principal: o conteúdo com `filename == "index.html"`,
   `filepath == "/"` e `filesize == 0` (R-PAGE, redação revisada em 29/09).
   - Zero ou mais de um candidato gera ocorrência não coberta com a causa, sem escolha por conteúdo ou predição.
   - Os demais conteúdos da página são anexos, fora do alvo.
   - É **regra operacional provisória**, inferida das respostas disponíveis (38 páginas em 16 respostas reais
     congeladas da API, **inclusive as 8 do lote de 29/09**). Não é contrato confirmado do Moodle.
   - A confirmação da versão continua pendente, sem consulta externa nesta etapa (issue, adendo 2, A3).
   - Implementada no `adquire` e no gerador v5 (Gate 1 parcial).
3. Uma ocorrência é **coberta** só quando cumpre todas as condições:
   - bytes completos adquiridos;
   - registro da aquisição concluído (`status ok`, inventário `concluido`);
   - caminho e sha256 conferidos contra a fonte e contra o inventário cujo sha256 é o esperado;
   - vínculo pela **proveniência da aquisição**; a ligação por nome + tamanho nunca cobre;
   - aceita pela política de cegamento congelada.
4. Continuam **no denominador, como não cobertas**:
   - falha, parcial, recusa ou ausência de vínculo;
   - ambiguidade;
   - conteúdo vazio (`conteudo_vazio`);
   - formato fora da allowlist.

   O sucesso de outra ocorrência com os mesmos bytes não cobre uma ocorrência que falhou.
5. **E4:** `100 × ocorrências cobertas ≥ 90 × ocorrências do alvo`, com a mesma unidade dos dois lados. O denominador
   vem só da listagem congelada e não é reduzido por download, deduplicação, ilegibilidade, recusa ou gold.

## 3. Documentos, E3 e mínimos pré-gold **[C]**

1. Depois da aquisição verificada, **documento** é a classe de ocorrências cobertas com o mesmo par
   (curso, sha256). O número de documentos só é conhecido depois da aquisição e é congelado antes do gold e do build.
2. **E3:** ≥ 10 documentos cobertos distintos no curso.
3. **Pré-gold, total:** ≥ 3 cursos na população geral e ≥ 100 documentos cobertos distintos na soma. A unidade do
   "100" mudou de item estrutural para documento: marcada **[C]**.
4. O pacote de adjudicação é reconciliado com esse cadastro. Arquivo local sem ocorrência no alvo, anexo excluído e
   sobra não entram em E3, nos mínimos nem no gold. Recusas e falhas ficam no cadastro de cobertura, sem expor
   conteúdo ao adjudicador.

## 4. Duplicatas, eixos e bloco **[C]**

1. Uma linha de gold corresponde a um documento, com todas as suas ocorrências permitidas visíveis. O julgamento se
   baseia no conteúdo; nenhuma ocorrência é escolhida depois de ver predições.
2. **Conflito contextual (R-CC, proposta não aprovada; revisada em 29/09):** não existe regra de status aprovada para
   este caso. A redação anterior dizia "regra de status já congelada", mas o pré-registro §4.2 e o `gold-externo-1`
   estão registrados por hash e não foram aprovados, e nenhum dos dois trata de conflito.

   **Regra:**
   - O rótulo sai do conteúdo; as seções e ocorrências são pistas.
   - Se o conteúdo sustenta mais de uma unidade ou tópico, o documento fica `avaliado`, com vários ids (mecanismo do
     `gold-externo-1`), e conta normalmente nos eixos oficiais.
   - Se só a subunidade é ambígua (a unidade é determinável), o documento fica `avaliado` com a unidade e
     `sub_primaria = sub_aceita = ?` (marcador do `gold-externo-2`). Ele conta no eixo da unidade e sai dos
     denominadores de subunidade.
   - Se o conteúdo não decide a unidade e as ocorrências estão em seções de unidades diferentes, o documento fica
     `excluido`, com `observacao` iniciando por `conflito_contextual:`.

   **Efeitos do `excluido` por conflito:**
   - sai de todos os eixos do gold e dos mínimos pós-gold;
   - continua em E3 e nos mínimos pré-gold, em E4 e na estabilidade de bloco;
   - é contado e relatado por curso;
   - A_novo e C_novo são calculados também com cada exclusão por conflito contada como erro no eixo afetado. **O
     veredicto oficial só é "aprovado" se aprovar nas duas contas**; aprovado só no principal = "não aprovado
     (dependente das exclusões por conflito)". Sem mudar limiar;
   - B_novo não tem conta de sensibilidade (perda exige gold); o número de exclusões acompanha o veredicto;
   - a exclusão do gold não apaga a ocorrência da cobertura.

   **Momento:** durante a adjudicação, antes de qualquer build, replay ou captura. O gold fica congelado por sha256
   antes do build, e depois disso nenhum status muda.

   **Versão:** exige `gold-externo-2` e instruções v2, como arquivos novos e ainda só propostos. Detalhe na issue,
   adendo 2, A4. Nenhum gold foi produzido.
3. **Acerto por documento e por eixo:** todas as entries vinculadas pelos mesmos bytes têm de satisfazer a régua
   daquele eixo. Entry ausente conta como erro, e uma entry não representa as demais. Entries sem documento
   adjudicado são relatadas à parte e não pontuam.
4. **Estabilidade de bloco (o que se mede):**
   - compara-se CRU_NOVO com VOCAB_NOVO **por entry, pelo mesmo ID**;
   - todas as entries do documento têm de manter o bloco; entries diferentes podem ter blocos diferentes entre si;
   - o conjunto de IDs e a correspondência entre braços são conferidos na sanidade, **antes** de comparar;
   - ID ausente, duplicado ou vínculo não resolvido nessa sanidade deixa B_novo "não avaliado", e nada é resolvido
     depois de ver predições;
   - concordância entre braços não demonstra acurácia de bloco.
5. **Acurácia de bloco:** fora desta validação. Exige gold temporal independente e regra data/sessão → bloco
   congelada em protocolo próprio.

## 5. Mínimos pós-gold, E2 e não atingimento **[C]**

1. **E2 [C]:** plano local presente e aprovado pela política de cegamento congelada, com o par arquivo/texto
   verificável. Plano recusado impede o pacote e a elegibilidade. É condição de integridade, não justificada por
   contagens de cursos.
2. **Pós-gold, total (número inalterado, unidade = documento [C]):** ≥ 80 documentos na população da subunidade
   primária.
3. **Pós-gold, por curso (limiar introduzido [C]):**
   - curso com < 10 documentos na população da subunidade primária é descritivo quanto a C_novo;
   - ele continua nas métricas agregadas e no veto de perdas por documento/eixo;
   - o critério de 3 cursos é só pré-gold;
   - todo resultado informa quantos cursos atingiram o mínimo pós-gold.
4. **Não atingimento:** faltar qualquer mínimo agregado impede veredicto de generalização. Métricas descritivas, falhas
   de sanidade e vetos observados continuam relatados. Falta de amostra não vira aprovação e não autoriza mudar
   população ou limiar.

## 6. Alcance

As conclusões se restringem a:

- o alvo operacional;
- os formatos efetivamente admitidos;
- as fontes congeladas;
- o contexto institucional (PUCRS; conta do aluno).

E4 mede a cobertura das ocorrências desse alvo. Ele não representa a disciplina inteira, o conteúdo pedagógico,
destinos externos nem independência comprovada do desenvolvimento.

## 7. Exposição e vigência

1. "Sem ocorrência" só vale quando todas as fontes requisitadas estavam disponíveis e as suas saídas foram
   interpretadas integralmente.
2. Distinguem-se:
   - zero matches;
   - fonte ausente;
   - erro de execução;
   - erro de interpretação;
   - trecho omitido.
3. Todos os matches por linha são registrados, com termo, intervalo e vizinhança segura. A categoria do arquivo não
   determina uso nem nível.
4. **ES I:** na saída v2, os 221 matches (todos os de cada linha) continuam em "Engenharia de Software II", e o id e o
   código de ES I não aparecem. Isso não demonstra equivalência nem independência; a exclusão vigente continua até
   decisão própria.
5. Depois de resolvidas as ambiguidades, texto, políticas e scripts são congelados por hash. Uma emenda posterior não
   recebe status retrospectivo de pré-registro, e cada fase seguinte tem autorização própria.

## 8. Avaliação das sugestões do parecer (`sugestoes_redacao_p3.md`)

| § do parecer | decisão | justificativa |
|---|---|---|
| 1. Status e transparência | **aceita** | Separa conhecimento prévio de calibração; declara exploratória a análise do lote conhecido, que é a consequência correta de a emenda vir depois das contagens. Isso restringe o que P3.1 pode concluir sobre este lote. |
| 2. Alvo e links | **aceita** | A justificativa operacional (cadeia de proveniência) é independente do schema do gold e da capacidade do motor, que eram as fraquezas da P3. |
| 3. Identidade e ocorrências | **aceita** | Tira a mistura itens × bytes do denominador de E4. |
| 3. Cobertura | **modificada** | Acrescentado explicitamente: "vínculo pela proveniência da aquisição; nome + tamanho nunca cobre" e "inventário cujo sha256 é o esperado", ligando a regra ao pacote cego v4 (`proveniencia_confirmada`, `inventario_sha256`). |
| 3. HTML de página conferido contra o contrato da API antes da aprovação | **modificada (pendente)** | Revisado em 29/09: a regra (R-PAGE) vem da evidência local, com 38 páginas em 16 respostas reais congeladas e o teste do produto `tests/test_moodle_sync.py:219–223`. A confirmação no código do Moodle da instância fica como consulta externa descrita, não executada (issue, adendo 2, A3). |
| 3. Zero bytes | **aceita** | `conteudo_vazio` fica no denominador de E4. |
| 3. E3 e mínimos por documento | **aceita, com [C]** | A mudança de unidade do "100" e do "80" fica marcada [C], como o parecer apontou. |
| 3. Reconciliação do pacote | **aceita** | Com inventário, o v4 já não entrega arquivo fora dele. |
| 4. Uma linha por documento; conflito contextual antes do build | **aceita** | Fecha a escolha de ocorrência depois das predições. |
| 4. Acerto por documento e eixo (todas as entries) | **aceita** | Igual à P3 §4, agora por eixo. |
| 4. Estabilidade de bloco por entry/ID | **modificada** | O parecer deixava "invalida até resolução pelo protocolo de sanidade". P3.1 fixa a sanidade antes da comparação e, se ela falha, B_novo fica "não avaliado", sem resolução depois de ver predições. Isso fecha um grau de liberdade. |
| 4. Acurácia de bloco fora | **aceita** | Igual à P3 §10. |
| 5. E2 com política de cegamento | **aceita, com [C]** | Condição de integridade; plano recusado impede o pacote (v3 e v4). |
| 5. Mínimo por curso; 3 cursos só pré-gold | **aceita** | Não introduz mínimo pós-gold de cursos. Criá-lo agora seria um limiar novo escrito conhecendo as contagens. |
| 5. Não atingimento e alcance | **aceita** | Igual à P3 §§9 e 11, mais explícito. |
| 6. Exposição | **aceita / texto de ES I modificado** | A regra de "sem ocorrência" foi implementada no verificador v2. O texto sobre ES I foi atualizado para a saída v2 (todos os matches por linha), que o parecer não tinha. |
| 6. Vigência | **aceita** | Congelamento por hash; sem pré-registro retrospectivo. |

Nenhuma sugestão foi rejeitada por inteiro. Nenhuma inclui limiar novo além do mínimo por curso já presente na P3,
ajuste por curso, exceção de formato para atingir mínimo ou previsão de efeito no lote.
