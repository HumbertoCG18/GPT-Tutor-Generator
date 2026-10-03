# Decisões pendentes para fechar o pré-registro da validação externa (29/09/2026)

**Nada aqui foi aplicado.** O pré-registro de 29/09 continua NÃO assinado e não será assinado enquanto qualquer item
abaixo estiver aberto. Nos pontos D1, D2 e D3 o texto de 29/09 afirmava uma regra; essas afirmações ficam suspensas.

**Aviso de contaminação por contagens:** as contagens do universo local de 29/09 e do lote adquirido nesta etapa já
são conhecidas por quem decide. Qualquer escolha abaixo deve registrar isso e não pode ser justificada por fazer um
curso específico entrar ou sair.

## D1. Mínimo pós-gold e mínimo por curso

Hoje (proposto em 29/09, não aprovado): pré-gold 3 cursos N0 e 100 adjudicáveis; pós-gold 80 materiais na população
da subunidade primária; nenhum mínimo por curso.

| opção | efeito | risco |
|---|---|---|
| A. manter só os mínimos totais | curso pequeno entra e pesa pouco no total | um curso de 5 materiais vira "curso avaliado" em C_novo |
| B. somar mínimo por curso (ex.: ≥ 10 na subunidade primária pós-gold; abaixo disso o curso só é descritivo) | C_novo e "nenhum curso regride" só valem para cursos com n mínimo | o número exato é arbitrário; decidir antes do gold |
| C. mínimo derivado de precisão desejada (largura de intervalo) | justificável estatisticamente | exige fixar a métrica e o método agora; não há cálculo feito |

## D2. Bloco: medir com gold ou limitar a dois eixos

Hoje (proposto, não aprovado): bloco não rotulado; B exige invariância de bloco por ID entre CRU e candidato.

| opção | o que o adjudicador recebe | efeito em B e C | risco |
|---|---|---|---|
| A. dois eixos (unidade, subunidade primária) + estabilidade de bloco | nada de bloco | B = sem perda nos dois eixos + nenhum bloco muda; C sem bloco | não mede acerto de bloco; só que o vocabulário não o mexe |
| B. bloco com gold por data/sessão da aula (o adjudicador marca a data; o bloco sai do cronograma depois do build por regra fixa) | cronograma bruto (SARC ou plano) | B e C com os três eixos | mapeamento data → bloco feito depois do gold; a regra tem de ser fixada antes |
| C. bloco com gold sobre a lista de blocos do motor de timeline | lista de blocos computada | três eixos | quebra o cegamento (espaço de rótulos produzido pelo motor) |

## D3. Unidade amostral e política para duplicatas

Hoje (código de 29/09): unidade = material (bytes únicos); no avaliador, a linha do gold é replicada para cada entry
com os mesmos bytes (`material@eid`), o que infla o denominador quando o build duplica entries (demonstrado pela
revisão).

| opção | unidade | duplicatas no build | risco |
|---|---|---|---|
| A. material (bytes) | 1 linha por material | avalia só a entry de menor id (regra fixa); as outras relatadas | a escolhida pode divergir das demais sem aparecer no placar |
| B. material, exigindo consistência | 1 linha por material | acerto só se TODAS as entries do material acertam | mais severo; um erro de duplicata vira erro do material |
| C. entry | 1 linha por entry | replicação (código atual) | infla o n; o mesmo julgamento conta várias vezes |
| D. excluir materiais duplicados | 1 linha por material único | fora do denominador, relatados | perde materiais legítimos |

Também em aberto: o mesmo arquivo publicado em duas seções do Moodle já é um material com duas ocorrências
(gerador v2); confirmar que isso vale como uma linha.

## Outros pontos abertos encontrados pela revisão (fora da lista de correções desta etapa)

- **D4. `model_version`:** a política diz que valores mistos invalidam a geração, mas o código de 29/09 não aborta
  com `model_version` misto nem ausente (demonstrado). Decidir: implementar a verificação na sanidade pós-geração
  (sem nova geração) ou retirar a regra.
- **D5. Exceção do gitleaks:** a regex aceita 64 hex seguidos de espaço e sufixo (sem âncora final). Decidir se fecha
  a âncora; não foi alterada nesta etapa porque não estava na lista autorizada.
- **D6. Regra do lote adquirido:** esta etapa aplica ao lote a mesma regra da v2 (N0–N3, E2–E4, mesmos limiares).
  Qualquer ajuste de limiar para o lote exige decisão explícita, sabendo das contagens.

## Pontos abertos pelo lote adquirido em 29/09 (contagens já conhecidas)

- **D7. E4 em cursos com links do Moodle.** No lote, os 8 cursos N0 falham ou em E3 (1) ou em E4 (7). E4 é o único
  critério que barra os 4 cursos que passam em E2 e E3. A regra conta cada módulo `url` como item adjudicável sem
  fonte local congelável. Decidir, sabendo destas contagens: manter E4 como está; tirar links do denominador de E4
  (links nunca entram no gold, pelo schema); ou outro limiar. Qualquer opção muda a população e tem de ser
  justificada sem referência a cursos específicos.
- **D8. Downloads que falharam e a contagem estrutural.** Arquivos listados pela API que não chegaram (ex.: 23 com
  `tipo_inesperado` em um curso) não entram em "adjudicáveis" nem em "com fonte local"; estão só no inventário.
  Decidir se entram no denominador de E3/E4.
- **D9. Alcance da busca de exposição.** A busca olha só o commit `bf46d51f` desta branch e as pastas de download
  anteriores; não olha outras branches, worktrees, a memória de sessões nem conversas. "N0" significa "nenhuma
  evidência nessas fontes", não independência comprovada. Decidir se a busca deve cobrir outras fontes antes do
  Gate 1.
