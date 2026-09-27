# Adendo ao pré-registro do regime VOCAB — Fase 1 corrigida (25/09/2026)

Adendo único e datado a `docs/reports/2026-09-24-regime-vocab-desenho.md` (commit `2589ed5a`), depois da revisão
adversarial encaminhada pelo usuário em 25/09. Autorizado nesta etapa: corrigir protocolo e harness e rodar preflights
**sem gold**. **Não** autorizado: avaliar braços contra a régua, rede, Gemini, recompilação, mudança em `src`, commit.

## 1. Nome e escopo do resultado

A Fase 1 mede o **efeito do vocabulário sobre a cadeia de atribuição, condicionado à timeline histórica congelada**. Não é
reprodução integral do produto com vocabulário; essa exige reconstruir todos os derivados na ordem real do produto e fica
fora desta autorização.

## 2. Estado e artefatos da versão anterior (não reutilizáveis)

- HEAD `2589ed5a`, alinhado com o origin; mudanças locais alheias preservadas (4 arquivos de 17/09 sem commit).
- Protocolo anterior (24/09), **não reutilizável**:
  - script `c1-3/wad_regime_vocab_fase1_24-09.py` (sha256 `bbf234cc…`, sem commit), que refazia a unidade dos blocos pelo
    DP e usava taxonomia congelada + união aditiva de aliases;
  - palcos `.frzero/wad_sidecars_24-09/`, com controles "maior" e "aleatório" montados sobre o JSON bruto.
  - A execução foi interrompida no 4º braço, antes de qualquer captura gravada ou leitura de gold.
- O protocolo novo grava só em caminhos novos: `.frzero/wad2_25-09/` e `c1-3/wad2_*`.

## 3. Entradas congeladas e injeção

- **Pacotes:** os 7 congelados da régua v2 (MF, IA e CG em `.frzero/wv_importacao_22-09/`; SO, ES2, TCC e FR em
  `.frzero/pacote_fontes_15-09/`).
- **Oitavo pacote (LR):** tem sidecar LLM, mas não tem pacote congelado nem régua. Fica fora do placar e dos preflights;
  só sua proveniência é listada.
- **Timeline:** a mesma `course/.timeline_index.json` congelada em todos os braços, sem nenhum recálculo (unidade dos
  blocos, tópicos candidatos e demais campos). As saídas de bloco, unidade e subunidade rodam normalmente, e qualquer
  consequência é registrada.
- **Taxonomia do braço:** a própria reconstrução do produto (`engine._build_rich_content_taxonomy`), com o carregador do
  glossário (`repo.load_glossary_curation`) apontado para o palco do braço.
  - **Validade:** exige a equivalência A, reconstrução sem sidecar == taxonomia congelada (igualdade completa: unidades,
    ordem, títulos; tópicos com código, rótulo, slug, tipo, unidade e aliases, na ordem).
  - **Equivalência B** (congelada + união aditiva do delta == reconstrução com sidecar): é só diagnóstico. Se falhar, a
    união aditiva não serve, e a taxonomia do braço continua sendo a reconstrução do produto.
  - Falha em A em qualquer curso: a avaliação para, e o relatório mostra a diferença e a premissa quebrada.
  - O CRU usa a taxonomia congelada; A garante que ela é a mesma que o produto reconstrói.
- **Glossário do índice de unidade:** o palco do mesmo braço, inclusive nos controles, cujo sidecar é reescrito com o
  endereçamento do controle.
- **Motor de bloco:** recebe a taxonomia do braço. Ele só lê slug e título das unidades, e um assert confere que são iguais
  em todos os braços.
- **Identidade de tópico:** sempre (curso, slug da unidade, slug do tópico).

## 4. Braços e controles

| braço | sidecars carregados | papel |
|---|---|---|
| CRU | nenhum | referência; deve reproduzir por ID a captura de referência (bloco 223, unidade 249, sub 86) |
| VOCAB_ATUAL | LLM + manual | referência histórica de proveniência mista; não é evidência do regime limpo |
| VOCAB_LLM | só o LLM histórico | "sidecars LLM históricos, sem manual no carregamento desta execução" (não é "livre de ajuste": prompt e filtros foram desenvolvidos nos cursos conhecidos) |
| CTRL_MAIOR | LLM reendereçado | testa concentração na classe majoritária, não a distribuição por tópico |
| CTRL_ALEAT_1/2/3 | LLM reendereçado | embaralhamento condicionado dentro da unidade; sondagem exploratória |

**Relações efetivas do VOCAB_LLM** são as que existem depois do carregador, da normalização, dos filtros e da deduplicação:
por tópico (curso, unidade, tópico), os aliases presentes na reconstrução com o sidecar LLM e ausentes na reconstrução sem
sidecar, na ordem do produto. Os controles reendereçam só essas relações. Assim ficam preservadas as restrições de
elegibilidade que o braço original sofreu.

**CTRL_MAIOR:**
- em cada unidade, todas as relações efetivas vão para o tópico majoritário;
- tópico majoritário = o de maior contagem de decisões finais de subunidade do CRU desta execução, entre os materiais do
  curso naquela unidade, sem gold;
- empate: o primeiro na ordem da taxonomia; unidade sem nenhuma decisão: o primeiro tópico da unidade;
- termo repetido no mesmo destino é deduplicado, e isso é declarado;
- colisões com aliases já existentes no destino são registradas.

**CTRL_ALEAT_s (s = 1, 2, 3):** algoritmo fixado antes de rodar.
1. Para cada unidade u, R_u é a lista das relações efetivas (alias, tópico de origem), e c[t] é o número de aliases
   acrescentados ao tópico t.
2. Os destinos são as vagas: cada tópico t repetido c[t] vezes. Tópicos com c[t] = 0 continuam sem vagas.
3. Com `random.Random(f"{s}|{curso}|{u}")`, embaralham-se as vagas e casam-se as relações na ordem do produto. A tentativa
   é válida se (i) nenhum alias cai num tópico que já o tem na reconstrução sem sidecar, (ii) nenhum alias cai duas vezes
   no mesmo tópico e (iii) um alias com multiplicidade m termina em m tópicos distintos.
4. Até 2000 tentativas. Se nenhuma for válida, a unidade fica marcada "embaralhamento inviável sob as restrições" e usa a
   primeira tentativa, com as violações registradas; não é chamada de pareada.
5. Unidade com um tópico só com vagas, ou em que toda tentativa válida devolve cada relação à origem: "sem embaralhamento
   informativo". As relações ficam na origem, os materiais ficam no denominador, e a limitação é registrada.
6. O sidecar do controle contém, por chave de tópico `"<código> <rótulo>"`, os aliases atribuídos.

Verificação depois do carregador, na reconstrução do produto com o sidecar do controle:
- contagem por tópico igual a c[t];
- multiconjunto de termos igual;
- multiplicidade por termo igual;
- pares (alias, tópico) iguais aos sorteados.

O relatório traz colisões, termos descartados e a fração de relações que mudou de destino. As três sementes não serão
ampliadas depois dos resultados; o relatório poderá dizer "superou os controles examinados", nunca "provou superioridade
estatística".

**Sanidade do reendereçamento:** um sidecar reescrito com a atribuição identidade tem de reproduzir exatamente as relações
efetivas do VOCAB_LLM.

## 5. Isolamento e proveniência

- Cada braço roda em processo Python próprio, com estado independente: entries, taxonomia, glossário, caches, doadores e
  campos computados. A 2ª passada roda pela política do produto, sem herdar nada de outro braço.
- Instrumentação por processo:
  - arquivos de glossário e de taxonomia lidos;
  - presença do manual (esperado: só no VOCAB_ATUAL);
  - leituras de palco de outro braço (esperado 0);
  - chamadas ao compilador de vocabulário e tentativas de rede (esperado 0; `TUTOR_NO_VOCAB_COMPILE=1`, rede bloqueada);
  - leituras de arquivos de gold (esperado 0; uma trava aborta o processo).
- A captura e os preflights não importam módulos de avaliação (`compara_herancas`, `mede_3eixos`, `wz_*`, `wx_*`). A
  avaliação futura é um script separado.
- Proveniência por sidecar: sha256, origem, metadados internos (`_provenance`, `_modelo`, `_nota`, presença de `_raw`),
  entradas e unidades usadas na geração quando registradas. Onde faltar: "proveniência incompleta".

## 6. Captura por material (geração e seleção)

Por material no laço de subunidade, a captura grava:
- a unidade efetivamente fornecida à 1ª passada;
- as pontuações que o próprio seletor calculou para cada tópico daquela unidade (a função de pontuação é envolvida, sem
  reconstrução retrospectiva);
- vencedor, confiança, ambiguidade, abstenção e motivos da 1ª passada;
- o número de chamadas da 2ª passada;
- a decisão final e seus motivos.

Assert: a unidade da 1ª passada é igual à unidade final; as exceções são registradas.

**Avaliação futura (definições fixadas agora):**
- Escada por material:
  - (a) gold existe na taxonomia e é elegível na unidade usada;
  - (b) gold com pontuação > 0;
  - (c) gold com pontuação ≥ 0,05 (recorte diagnóstico fixo);
  - (d) gold escolhido na 1ª passada;
  - (e) decisão final correta.
- Candidato em ambos os braços, só no CRU, só no VOCAB, em nenhum. A seleção é comparada também no subconjunto em que o
  gold era candidato nos dois.
- Transições: correção, perda, erro → outro erro, abstenção → certa, abstenção → errada, decisão → vazio.
- Precisão das alterações com denominador de **todas** as saídas modificadas; a precisão das não vazias é adicional.
- Vazios e inconsistências de identidade continuam no denominador oficial. A subunidade aceita é auxiliar.

## 7. Três veredictos

- **A. Sinal exploratório:** VOCAB_LLM supera o CRU, o CTRL_MAIOR e cada CTRL_ALEAT na subunidade primária total. É
  evidência histórica limitada: não aprova integração, recompilação nem generalização. O relatório mostra o ganho por curso
  e todas as perdas.
- **B. Aceite de integração:** ganho positivo, zero perda de acertos atuais, nenhum curso regredindo, demais eixos
  preservados e replay integral pela cadeia completa do produto. Esta Fase 1 não fornece essa prova sozinha. Se houver sinal
  com perdas: "sinal exploratório observado; candidato reprovado para integração".
- **C. Meta:** mais de 90% por eixo e por curso **avaliado**; FR não tem bloco nem unidade avaliados.
- Nenhuma margem, limiar de precisão ou significância será criado depois do resultado; a Fase 1 é descritiva.
- Falha de fidelidade do harness compromete a atribuição do resultado. Candidato que perde com harness válido é resultado
  negativo válido.

## 8. Limites e fases

- Os 7 cursos são desenvolvimento contaminado, não holdout.
- 218/251 é limite diagnóstico das intervenções e fontes examinadas, sob as hipóteses usadas; não é impossibilidade
  universal do cru.
- 279/300 não comprova mais de 90% por curso nem generalização. O desenho futuro terá de tratar resultado por curso,
  dependência entre materiais e o compilador final congelado.
- As fases seguem separadas: (1) Fase 1 histórica offline, esta; (2) recompilação limpa, com autorização de rede própria;
  (3) compilador v2, com implementação e validação próprias; (4) validação em cursos novos, ainda não autorizada.

---

## Registro do preflight sem gold (25/09; fato, não altera as definições acima)

- **Artefatos:**
  - script `c1-3/wad2_regime_vocab_fase1_25-09.py` (sha256 `18e4155349736bf5…`);
  - relatório `c1-3/wad2_preflight_25-09.json` (`e6cd46d0f41a7180…`) e `.md`;
  - helpers usados sem alteração: `replay_bloco_21-09.py` (`86df7385…`) e `replay_unidade_21-09.py` (`a39e95af…`);
  - palcos em `.frzero/wad2_25-09/palcos/`; capturas em `.frzero/wad2_25-09/capturas/`, com a versão do script no nome.
- **Condições (13/13 cumpridas):**
  - `src/` e `tests/` sem diff;
  - equivalência A nos 7 cursos;
  - delta não vazio nos braços com sidecar;
  - CRU igual à referência por ID nos 350 materiais (sha canônico `2bf79173d213eda2`, igual ao da referência);
  - unidade da 1ª passada igual à final nos 341 materiais do laço;
  - reendereçamento identidade reproduz o VOCAB_LLM depois do carregador;
  - os 4 controles idênticos ao pretendido depois do carregador;
  - manual carregado só no VOCAB_ATUAL; nenhuma leitura de palco de outro braço;
  - 0 leitura de gold, 0 tentativa de rede e 0 chamada ao compilador em todos os processos;
  - unidades vistas pelo motor de bloco iguais em todos os braços;
  - taxonomia dos braços nos workers igual à do P2.
- **Equivalência B (diagnóstico) falha em MF, IA, TCC e CG:** o produto insere os aliases novos no meio da lista (sem
  remoções). A união aditiva não reproduz a ordem e fica descartada. Os braços usam a reconstrução do próprio produto,
  validada por A, e os braços VOCAB não leem a taxonomia congelada.
- **Controles:**
  - fração de relações que mudou de destino nos aleatórios: 0,56 a 0,89;
  - "sem embaralhamento informativo": IA u03 e CG u01 (um tópico com vagas cada), mantidos na origem e com os materiais no
    denominador;
  - nenhuma unidade inviável;
  - CTRL_MAIOR: 1 colisão (IA u05, "Aprendizado Supervisionado", que já é alias do tópico majoritário).
- **Proveniência:** todos os sidecars estão com **proveniência incompleta**.
  - LLM: `gemini-3.5-flash`, com `_raw`, sem versão de prompt; gravados em 11/09 (MF, SO, IA, ES2, TCC, CG) e 02/09 (FR,
    LR).
  - Manuais: sem modelo, de 07/09 a 12/09.
- **Pendências reais (nada a executar sem nova autorização):**
  1. capturar os 6 braços não-CRU (implementado; bloqueado no script);
  2. escrever e congelar por hash o script de avaliação separado, com as definições dos §§ 6–7, antes de avaliar;
  3. resultado sempre condicionado à timeline congelada; a reconstrução completa do produto fica fora;
  4. LR fora da Fase 1.
