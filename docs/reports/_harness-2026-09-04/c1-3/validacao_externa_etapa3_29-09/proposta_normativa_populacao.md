# Proposta normativa única: população da validação externa (P3, 29/09/2026)

**Status: proposta. Nada aqui foi aplicado.** Não foi calculada nenhuma contagem com esta regra, nem no lote de 29/09
nem no universo local. A seleção vigente continua vazia (regra v2, `registro/nota_registro_29-09.md`, item 4). Resolve
D1, D2, D3, D7 e D8 de `../validacao_externa_etapa2_29-09/decisoes_pendentes.md`; D4, D5, D6 e D9 ficam fora (§12).

## 0. Contagens já conhecidas por quem propõe

Quem escreveu esta proposta já conhece:

- o universo local de 29/09: 16 candidatos (N3 7, N2 1, N1 5, N0 3), nenhum elegível;
- o lote da etapa 2: 8 cursos N0 e 461 itens da API (267 ok, 171 links, 23 `tipo_inesperado` num curso), com E2/E3/E4
  por curso (7 reprovam em E4, 1 em E3);
- a conferência desta etapa: 9 pares de duplicatas em 3 cursos; formatos fora da allowlist em 3 cursos (`.go` 33, `.asm` 9,
  `.jar` 1, `.mod` 1, sem extensão 5); nenhum anexo de página;
- a verificação de exposição desta etapa.

As regras marcadas **[C]** mudam o que a regra v2 dizia e foram escritas conhecendo essas contagens (tabela no §13).
Nenhuma foi escolhida para fazer um curso específico entrar ou sair. Nenhum limiar numérico foi alterado.

## 1. Alvo do estudo **[C]**

O alvo é o **subconjunto documental publicado no Moodle** da disciplina, não a disciplina inteira. Ele contém os
arquivos dos módulos `resource`, `folder` e `assign` e o HTML principal dos módulos `page`. Ficam fora: módulos `url`
(links), rótulos, fóruns, questionários, outros tipos de módulo, anexos embutidos em páginas e qualquer conteúdo
acessado por link.

Justificativa independente das contagens: o gold (`gold-externo-1`) nunca rotula links, e o regime VOCAB atua sobre o
texto dos materiais. Um estudo não pode concluir sobre o que não consegue adjudicar. O custo está no §11: as
conclusões não valem para conteúdo acessado por link.

## 2. Universo por curso, fixado antes do download **[C]**

O universo de um curso é a lista de itens do alvo (§1) na resposta `core_course_get_contents`, congelada
(`raw/moodle/contents.json`). Ela fica fixada antes de baixar qualquer byte. O download não acrescenta nem retira itens
do universo; só decide quais itens ficam cobertos (§5).

## 3. Unidade amostral, fixada antes do build **[C]**

A unidade é o **documento**, identificado dentro de cada curso pelo sha256 dos bytes adquiridos. Um item sem bytes
(falha ou recusa na aquisição) é uma unidade própria, identificada por (módulo, `filepath`, arquivo). Isso é
conservador: se duas cópias falharem, contam como duas unidades não cobertas.

A lista de unidades adjudicáveis é a de `materiais.json` do pacote cego v3, com o hash congelado antes de qualquer build.
Em cada curso, a unidade é (curso, sha256): os mesmos bytes em dois cursos dão duas unidades, porque o espaço de
rótulos (plano) é outro.

## 4. Duplicatas **[C]**

- **Duplicatas na fonte:** os mesmos bytes em vários itens ou seções formam **uma** unidade, com todas as ocorrências
  (seção, módulo) visíveis ao adjudicador. Isso dá uma linha de gold e resolve a pergunta em aberto de D3.
- **Duplicatas no build** (D3-B, consistência): uma unidade só conta como acerto se **todas** as entradas do build com
  os mesmos bytes acertam. Se ela não tem entrada no build, conta como erro. Entradas do build sem unidade no pacote
  são relatadas e não pontuam. Não se escolhe uma entrada representante e não se replica a linha do gold.

## 5. Cobertura da aquisição, com falhas no denominador **[C]**

Uma unidade fica **coberta** quando cumpre três condições:

1. foi adquirida com status `ok`;
2. foi ligada ao item pela proveniência da aquisição (registro do inventário com caminho e sha256 conferidos);
3. foi aceita pela política de cegamento v3, inclusive a política de membros de contêiner.

As demais unidades do universo ficam **não cobertas** e continuam no denominador:

- falha de aquisição (`tipo_inesperado`, `assinatura_invalida`, `falha_http:*`, `falha_local:*`);
- recusa por tamanho ou orçamento, declarado ou real;
- recusa de segurança;
- formato fora da allowlist;
- `origem_nao_confirmada`.

Nenhuma recusa é revertida para cumprir o critério, e nenhum arquivo é liberado para atingir mínimo.

## 6. Links **[C]**

Links ficam fora do alvo e do universo e não entram em E3 nem em E4. Eles são relatados só de forma descritiva, por
curso: quantidade e domínio, sem parâmetros. Nenhum link é adjudicado, e as conclusões os excluem explicitamente (§11).

## 7. Elegibilidade do curso

- **E2 (inalterado no limiar):** plano local disponível **e** aceito pela política de cegamento v3 (o pacote não é
  gerado com plano recusado).
- **E3 [C]:** ≥ 10 unidades **cobertas** (antes: itens estruturais, com links).
- **E4 [C]:** `cobertas × 100 ≥ 90 × universo`, só com inteiros. O limiar de 90% não muda; muda o denominador, que
  passa a ser o universo do §2, com falhas e recusas e sem links.
- Os níveis N0–N3, as classes de população (geral = N0, piloto = N1), `K_MAX` = 6 e a ordem por
  `sha256("vocab-validacao-externa-2026-09-29|moodle:<id>")` ficam **inalterados**.

## 8. Mínimos

- **Pré-gold (inalterados nos números):** 3 cursos na população geral e 100 unidades cobertas na soma.
- **Pós-gold, total (inalterado):** ≥ 80 unidades com status `avaliado` na população da subunidade primária, somando os
  cursos.
- **Pós-gold, por curso [C] (D1-B):** um curso com < 10 unidades na população da subunidade primária é **descritivo**.
  Ele não recebe veredicto próprio (C_novo, "curso regredindo"), mas continua no total e no veto de perdas do B_novo:
  qualquer perda, em qualquer curso, reprova. O número 10 é o mesmo de E3, não calibrado em contagens.

## 9. Mínimos não atingidos

Sem veredicto de generalização: A_novo, B_novo e C_novo ficam "não avaliados", nunca aprovados nem reprovados. Os
números do piloto são só descritivos. Nenhum limiar muda, nenhum curso excluído (os sete de desenvolvimento, LR,
LSO, UX) entra, e nenhuma recusa é revertida. O próximo passo é uma nova aquisição, sob manifesto novo e Gate de rede
próprio (outra conta, outros semestres), com o `adquire` v3.

## 10. Bloco: estabilidade não é acurácia (D2)

- **Estabilidade de bloco entre braços** é o que esta validação mede: para cada unidade, o bloco previsto por CRU_NOVO
  tem de ser igual ao previsto por VOCAB_NOVO (`B_rodada`). Faz parte do B_novo como hoje (§11.2 do pré-registro de
  29/09). Mostra que o vocabulário não mexe no bloco; **não** mostra que o bloco está certo. Os relatórios dizem
  "estabilidade de bloco", nunca "acerto" nem "acurácia" de bloco.
- **Acurácia de bloco** só com um gold temporal independente, fora desta validação. Nele, o adjudicador marcaria
  data e sessão a partir do cronograma bruto, e a regra data → bloco seria fixada antes do build. Isso exige
  pré-registro e Gate próprios. Nenhuma afirmação de acurácia de bloco será feita com os dados desta validação.

## 11. Alcance das conclusões

Um veredicto, se houver, vale só dentro destes limites:

- disciplinas da PUCRS em que a conta do aluno está inscrita no Moodle, nos semestres do catálogo;
- o subconjunto documental do §1, como adquirido e congelado;
- formatos da allowlist do pacote cego v3;
- planos no formato institucional.

Ele não vale para conteúdo acessado por link, anexos de página, formatos fora da allowlist, material privado do
professor nem outras instituições.

O adjudicador é o próprio aluno: cursou as disciplinas, é cego às predições e não à hipótese. N0 significa "nenhuma
evidência nas fontes pesquisadas" (limite de D9), não independência comprovada. Nada disto é significância
estatística.

## 12. Fora desta proposta

- **D4** (`model_version`): segue aberto.
- **D5** (âncora da exceção do gitleaks): segue aberto; sem allowlist nova.
- **D6**: substituído pelo §14.
- **D9** (alcance da busca de exposição): segue aberto; a verificação local desta etapa não o amplia.
- **Allowlist de formatos:** incluir extensões de código (`.go`, `.hs`, `.asm` etc.) exigiria mudar a política de
  cegamento e seus testes, o que não está autorizado. Até lá, esses arquivos contam como não cobertos (§5).

## 13. Mudanças de regra informadas por contagens

| # | regra v2 (29/09) | P3 | contagens conhecidas ao escrever | efeito líquido no lote |
|---|---|---|---|---|
| 1 | alvo = curso; links no denominador de E4 | alvo documental; links fora (§1, §6) | links reprovam E4 em 7 de 8 cursos (D7) | **não calculado**; tende a tirar a principal barreira do E4 |
| 2 | E3/E4 sobre itens estruturais | sobre unidades de bytes únicos (§3) | 9 pares de duplicatas em 3 cursos | não calculado |
| 3 | falhas só no inventário (D8) | falhas e recusas no denominador (§5) | 23 falhas num curso | não calculado; mais severo |
| 4 | fora da allowlist sem regra | não coberta, no denominador (§5) | `.go` 33, `.asm` 9, sem extensão 5, `.jar` 1, `.mod` 1 | não calculado; mais severo |
| 5 | sem mínimo por curso | < 10 → descritivo (§8) | tamanhos do lote | não aplicável antes do gold |
| 6 | duplicata do build replicada | consistência (§4) | nenhuma (sem build) | — |
| 7 | anexos de página sem regra | fora do alvo, relatados (§1) | 0 anexos | nenhum no lote |

"Não calculado" é deliberado: calcular seria aplicar a proposta ao lote. Se a mudança 1 for recusada por ser informada
por contagens, vale a regra v2 e a seleção continua vazia. Esta proposta não traz uma versão alternativa.

## 14. Entrada em vigor

1. Aprovação explícita desta proposta, que será congelada por sha256.
2. Aplicação **uma única vez** ao lote já adquirido e a qualquer aquisição futura, com o resultado relatado seja qual
   for. Uma revisão feita depois de ver o resultado vira P4 e não pode ser aplicada a este lote.
3. A aplicação exige o pacote cego v3 aprovado e roda sem rede sobre as fontes congeladas. O resultado de P3 nunca
   substitui o resultado vazio da regra v2; os dois ficam registrados, cada um com sua regra.
