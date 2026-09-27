# Adendo v2 ao pré-registro do regime VOCAB — Fase 1, harness corrigido (25/09/2026)

Substitui, para a medição, o adendo v1 (`2026-09-25-regime-vocab-adendo-fase1.md`, sha256 `bc12ab37…`, preservado sem
alteração). Motivo: a revisão adversarial encaminhada pelo usuário em 25/09 encontrou falhas no harness v2
(`wad2_regime_vocab_fase1_25-09.py`, `18e41553…`). Autorizado nesta etapa (Gate 1 restrito):
- corrigir o harness;
- escrever o avaliador separado e testes sintéticos;
- reexecutar os preflights sem gold.

**Não** autorizado: capturar os seis braços restantes, avaliar contra a régua real, mudar `src/`, rede, recompilação ou
commit.

Só o bloco entre os marcadores NORMATIVO entra no hash do congelamento (`protocolo_sha`). O registro de resultados fica
fora dele.

<!-- NORMATIVO:INICIO -->
## N1. Resultado e fases

- **Nome:** "efeito do vocabulário sobre a cadeia de atribuição, condicionado à timeline histórica congelada". Não é
  reprodução integral do produto com vocabulário.
- **Fases separadas:**
  1. Fase 1 histórica offline;
  2. recompilação limpa, com autorização de rede própria;
  3. compilador v2;
  4. validação em cursos novos, não autorizada.
- Os 7 cursos são desenvolvimento contaminado. 218/251 é limite diagnóstico das fontes examinadas, não impossibilidade
  universal. 279/300 não comprova generalização.

## N2. Entradas, injeção e equivalências

- **Pacotes:** os 7 congelados (MF, IA e CG em `.frzero/wv_importacao_22-09/`; SO, ES2, TCC e FR em
  `.frzero/pacote_fontes_15-09/`). LR fora (sem pacote congelado nem régua).
- **Timeline:** histórica e congelada, idêntica em todos os braços, sem nenhum recálculo; as saídas de bloco, unidade e
  subunidade rodam normalmente.
- **Taxonomia:** nos braços com sidecar, a reconstrução do produto (`engine._build_rich_content_taxonomy`) com o
  carregador do glossário no palco do braço. No CRU, a congelada. O glossário do índice de unidade é o do mesmo braço.
- **A:** reconstrução sem sidecar == taxonomia congelada, igualdade completa, ordem de listas preservada. Falha em A
  interrompe antes de qualquer captura.
- **B (diagnóstico):** a inspeção integral classifica cada diferença entre a união aditiva e a reconstrução como "só ordem
  de aliases" ou "outra". A contagem é total; os exemplos exibidos podem ser limitados. B não precisa passar.
- **C:** o sidecar `_IDENTIDADE` (relações efetivas reendereçadas para a própria origem) tem de reproduzir o VOCAB_LLM na
  taxonomia completa, com ordem, e no índice de unidade. Se C falhar, o mecanismo de reendereçamento não é alterado antes de
  apresentar a diferença concreta.
- **D (verificação dos controles):**
  - campos não-alias e identidades de tópico idênticos à reconstrução sem sidecar;
  - aliases preexistentes preservados na ordem (sem remoção);
  - adições do tópico iguais ao pretendido, como multiconjunto; canonização declarada: a ordem em que o produto insere os
    aliases não é promessa do controle.
- **Identidade:** tópico = (curso, unidade, tópico); nunca `topic_slug` isolado.
- **Entradas externas:** os arquivos de origem apontados por `source_path` nos manifests (fora dos pacotes, por exemplo
  `.zip` de código em `Desktop/Moodle`) são lidos pela cadeia. Ficam congelados um a um (hash) e são permitidos só
  pelo caminho exato, em modo somente leitura; conferidos no acesso e antes/depois. Qualquer outro arquivo das mesmas
  pastas continua proibido. Arquivo externo ausente interrompe.

## N3. Congelamento, captura e reúso

- **Congelamento comum** (`id_comum` = sha256 da parte normativa):
  - hash deste bloco normativo;
  - hashes completos de `captura.py`, `comum.py`, `avaliador.py`, `test_wad3.py` e dos helpers `replay_bloco_21-09.py` e
    `replay_unidade_21-09.py`;
  - base pretendida `2589ed5a…` e hash da árvore `src/`;
  - Python, plataforma, hash da lista de distribuições instaladas e variáveis de ambiente registradas (lista fechada, sem
    segredos);
  - hash por arquivo de toda a árvore dos 7 pacotes (manifest, `profile_input`, Markdown, curadorias etc.);
  - hash da captura de referência;
  - inventário de IDs;
  - expectativas: mapa de manuais, braços liberados para captura, denominadores.
- **Insumos por braço:** arquivos do palco, snapshots de taxonomia e de índice de unidade (arquivo e conteúdo). O hash entra
  no congelamento separado dos resultados.
- **Captura:** esquema `wad3-captura-1`, `id_comum`, insumos do braço, braço, modo, status, inventário, verificações,
  violações, acessos e `conteudo_sha`.
  - Reúso só depois de validar tudo isso. Braço, modo, insumos, conteúdo, esquema ou status errados = rejeição.
  - Nome de arquivo nunca basta; captura inválida no caminho esperado interrompe, sem sobrescrever.
- **Gravação:** atômica; falhas vão para `falhas/` e nunca ocupam o lugar de uma captura.
- **Conferência antes e depois:** cada leitura de entrada comum é conferida contra o hash congelado no acesso e de novo ao
  final; o processo principal compara a árvore inteira antes e depois.
- **Captura completa:** só do CRU nesta etapa (`CAPTURA_LIBERADA`), inclusive pelo ponto de entrada interno.

## N4. Violações e travas

- **Violação:** leitura de gold (padrões de nome), palco ou snapshot de outro braço, tutor vivo depois do preparo, arquivo
  fora da lista permitida, escrita em entrada, insumo divergente ou não congelado, rede, subprocesso não autorizado,
  compilador de vocabulário.
- Toda violação fica no registro do processo, mesmo quando uma camada engole a exceção. Resultado: status de falha, nenhuma
  captura gravada, diagnóstico em arquivo separado (sem conteúdo de gold nem segredo) e saída ≠ 0. O processo principal
  também sai ≠ 0 quando reprova. As condições essenciais não usam `assert`.
- **Alcance real:** `builtins.open`/`io.open`, API de socket (`connect`, `connect_ex`, `create_connection`,
  `getaddrinfo`), `subprocess.Popen` e o compilador. **Não** cobre `os.open`, `mmap`, extensões C nem rede fora da API de
  socket; não é sandbox. As travas são instaladas antes de qualquer import de `src/`.
- **Manual esperado:** no VOCAB_ATUAL, só CG, ES2, IA, SO e TCC; nos demais braços, nenhum. Divergência do inventário real
  = mudança de insumo e parada.
- Os workers nunca leem tutores vivos; a leitura para preparo e proveniência é do processo principal, antes dos palcos.
- **Negado por declaração (não é violação):**
  - `.env` da raiz do repositório (segredos): o carregador do produto tenta lê-lo no import; a trava impede a leitura
    sem ler o conteúdo e registra o acesso em `negados`. O produto segue sem ele (sem rede, as chaves são
    irrelevantes). Se isso mudar alguma decisão, a reprodução do CRU por ID aponta a diferença.
- **Determinismo:** `PYTHONHASHSEED=0` em todos os processos; o processo principal se relança antes das travas.
  O cache do módulo `platform` é aquecido antes das travas (no Windows, a 1ª consulta executa `ver`).

## N5. Captura por material

Registrados por material:
- curso e ID; se a rota automática de subunidade foi chamada; motivo quando não foi (`manual_subunit`, `nao_material`,
  `sem_bloco`, `nao_identificado`);
- na 1ª chamada: unidade fornecida, pontuações exatas calculadas pelo próprio pontuador do seletor, com identidade (unidade,
  tópico) e sem arredondamento, vencedor com a unidade retornada (`m.unit_slug`), confiança, ambiguidade e motivos
  completos;
- chamadas posteriores, cada uma registrada;
- decisão final completa;
- hash da taxonomia usada.

A instrumentação não altera a decisão. Premissa: a unidade da 1ª passada é igual à final, em todos os braços. Divergência
invalida a captura; nada é sobrescrito.

## N6. Controles

- **CTRL_MAIOR:** em cada unidade, as relações efetivas do VOCAB_LLM vão para o tópico com mais decisões finais do CRU
  desta execução (empate: ordem da taxonomia; sem decisões: o primeiro tópico). Termo repetido é deduplicado e colisões são
  registradas. Testa concentração na classe majoritária, não distribuição.
- **CTRL_ALEAT_1/2/3** (sementes 1, 2, 3; `random.Random(f"{semente}|{curso}|{unidade}")`; 2000 tentativas):
  - as vagas são os destinos originais, e o controle usa a primeira permutação válida (sem colisão com alias preexistente do
    destino e sem duplicata);
  - estados: `estruturalmente_nao_informativa` (menos de 2 tópicos com vagas; fica na origem),
    `identidade_sorteada` (a primeira válida é a identidade; não se sorteia de novo), `pareado`, e
    `sem_permutacao_valida_no_orcamento`, que bloqueia o controle, que então não é aprovado nem avaliado;
  - propriedades exigidas na verificação: pares pretendidos, contagem por tópico, multiconjunto, multiplicidade por termo,
    sem duplicata e sem remoção.
- Os aleatórios testam o endereçamento condicionado à distribuição de vagas, não todo o efeito da compilação LLM.
- Materiais de unidades não informativas ficam no denominador. Sem novas sementes, novos braços ou significância.

## N7. Avaliador (script separado e congelado antes da captura)

- **Ordem:** validar capturas, congelamento, braços, cursos, IDs, esquema, ausência de violações e de mistura de versões;
  só então ler a régua, por uma porta única com autorização explícita.
- **Denominadores oficiais:** 237 (bloco), 284 (unidade), 251 (subunidade primária). Inventário de captura: 350. FR sem
  bloco nem unidade. LR fora.
- **Material ausente:** `eid` nulo é erro. Registro ausente para `eid` presente é captura corrompida e invalida a
  avaliação. Predição ausente nunca vira abstenção correta.
- **Régua histórica exata:** bloco por igualdade; unidade, primária e aceita por pertinência; `{""}` = vazio correto.
  Nenhuma correção de gold nesta avaliação.
- **Geração:**
  - escada: (a) existe na taxonomia e é elegível na unidade usada; (b) score > 0; (c) score ≥ 0,05; (d) escolhido na 1ª
    passada; (e) final correto;
  - grupos ambos / só CRU / só braço / nenhum nos dois cortes (0,05 é recorte fixo);
  - seleção comparada no subconjunto comum de candidatos, com numeradores e denominadores.
- **Transições:** partição por (certo antes, certo depois, vazio antes, vazio depois, mudou). Categorias derivadas dela:
  correção, perda, erro → outro erro, correta → outra correta, abstenção → certa, abstenção → errada, decisão → vazio.
- **Precisão das alterações:** saídas alteradas que terminam corretas sobre **todas** as alteradas; com zero alterações,
  "não aplicável". A precisão das alterações não vazias é adicional.
- **Meta:** contagem exata (acertos × 10 > 9 × n), nunca percentual arredondado.
- **Veredictos:**
  - A: VOCAB_LLM > CRU, CTRL_MAIOR e cada aleatório na primária total; VOCAB_ATUAL não decide.
  - B: sem perdas e sem regressão por curso; mesmo assim, não comprova integração completa. Se A for verdadeiro com perdas:
    "sinal exploratório observado; candidato reprovado para integração".
  - C: mais de 90% por eixo e curso avaliado.
- Nenhuma margem, limiar ou teste de significância depois dos resultados.
<!-- NORMATIVO:FIM -->

## Registro (fora do bloco normativo)

- **Testes sintéticos:** 37/37 (`wad3_25-09/testes_v3.txt`).
- **Preflight v3, tentativa 5:** 20/20 condições, saída 0, 187 s.
- **Congelamento comum:** `05dc9cf1e3f35c09c79104fb1cfc953c8ee49660e56c045679ca4200366ad8f7`. Hashes completos em
  `wad3_25-09/manifesto_congelamento_v3.json`.
- **As 4 tentativas anteriores reprovaram e pararam antes de capturar.** Estão preservadas, e as correções entraram no
  protocolo acima:
  1. raiz do repositório errada, que deixou o check de `src/` vazio;
  2. `sys.path` sem a raiz;
  3. `.env`, `ver` e índice;
  4. fonte externa não congelada.
- **CRU recapturado** com a instrumentação nova: igual à referência por ID (350 materiais, 0 divergências); 341 chamados;
  unidade da 1ª passada igual à final em todos. Os braços não-CRU tiveram só carga (taxonomia, índice e artefatos
  temporais), sem classificação final.
- Matriz de achados, artefatos reutilizados/descartados e limitações: `wad3_25-09/matriz_achados_v3.md`.
- Captura dos 6 braços e avaliação: **não executadas**, aguardam autorização própria.
