# Issue (rascunho local): validação externa VOCAB, etapa 3 — correções pós-revisão independente

**Estado:** aguardando Gate 1. Nada implementado. Rascunho local; publicar no GitHub só se autorizado.

## Contexto

A revisão independente da etapa 3 (`Codex/2026-09-29/revis-o-independente-valida-o-externa/outputs/Do_Gpt/`:
`revisao_etapa3.md`, `reprodutores_etapa3.json`, `evidencias_etapa3.zip`, `sugestoes_redacao_p3.md`) **não aprova**:

- o pacote cego v3 (P1): bypasses entregam conteúdo proibido com auditoria vazia;
- a aquisição v3 (P1): parcial órfão, janela entre escrita e registro, checkpoint destrutivo e regressão HTTP;
- a P3 no texto atual (P2);
- a exposição (P2): falsos zeros e conclusão excessiva sobre ES I.

Confirmados pela revisão: os 5 casos anteriores corrigidos, os diffs delimitados, a conferência física, as redações
e a distinção de bloco. A revisão está consumida: sem nova chamada Astra automática.

Prefixos dos casos: **PC** pacote cego, **AQ** aquisição, **EXP** exposição, **REG** registro, **CONF** conferência.
A numeração AQ do JSON difere da tabela do parecer. Aqui os casos são citados pelo nome.

## Classificação (routing.md)

- **Nível T3:** segurança do cegamento (vazamento de predição ou segredo ao adjudicador) e perda de registro na
  aquisição.
- **Confiança:** alta nos defeitos, porque todos têm reprodutor executado; média na redação da P3.
- **Executor pela tabela:** claude-fable-5-1/high. A sessão atual é opus-5-5; a escolha é do usuário.
- **Alcance:** 4 ferramentas da validação externa (cópias novas), 2 documentos corrigidos em versão nova e 1 proposta
  normativa. Nenhum arquivo em `src/`. Tarefa de mais de 20 chamadas.

## Escopo

### 1. Pacote cego (v3 → v4)

| achado | casos | correção proposta |
|---|---|---|
| XML examinado por regex: atributos, entidades e UTF-16 escapam | PC02–08, PC13, PC27–30 | parse por `xml.etree` (stdlib) com recusa de DTD/`<!ENTITY>` (OOXML e ODF não usam); varrer texto concatenado **e** todo valor de atributo; codificação pela declaração/BOM; `_decodifica` passa a reconhecer BOM UTF-8/16/32 também em texto solto |
| membro desconhecido aceito implicitamente | PC09, PC10 | allowlist explícita de membros por classe de documento; extensão desconhecida = recusa. Binário estrutural permitido (imagem, fonte, EMF/WMF, `printerSettings`) passa por assinatura e varredura léxica dos bytes (UTF-8 e UTF-16), com limite declarado |
| negações de caminho do `Leitor` não valem dentro de ZIP | PC11, PC12 | uma função pura de caminho (NOME_NEGADO, PARTE_NEGADA, RAIZ_NEGADA, `raw/` fora do permitido, segredo) usada pelo `Leitor` e pelos membros |
| PDF: `/EmbeddedFile` literal é vencido por escape `#46` | PC20; PC21 e PC31 relacionados | detecção estrutural com PyMuPDF (dependência declarada em `pyproject.toml`): arquivos embutidos, anotação de anexo, texto das páginas varrido; PDF ilegível = recusa. Menção em comentário deixa de recusar (PC31) |
| anexo de página reentra como sobra adjudicável | PC26 | arquivo local que corresponde a anexo de página da API fica em `fontes_nao_usadas` e nunca vira sobra |
| ligação sem inventário não confirma módulo | PC25 | limite explícito: `nome_tamanho_secao` = "não confirmada por proveniência" no manifesto e no relatório; a P3.1 não conta essa ligação como cobertura |
| inventário coerente, porém errado | PC24 | a fonte passa a declarar `inventario_sha256` esperado (o do congelamento); divergência aborta. Isso reduz o limite, sem eliminá-lo |

Recusas amplas (PC17) ficam como limite declarado, sem liberar formatos.

### 2. Aquisição (`adquire` v3 → v4; sem rede, só cliente falso)

| achado | caso | correção proposta |
|---|---|---|
| gravação parcial perde a referência | `partial_write` | escrita em `<alvo>.parcial` e depois `os.replace`; falha registra `caminho_parcial` e bytes gravados, sem apagar |
| interrupção entre escrita e registro | `interrupt_after_write`, `baixar_interrupt_after_write` | registro anexado **antes** da escrita (`status: gravando`) e atualizado depois; o `finally` publica o que houver |
| checkpoint destrutivo | `inventory_write_interruption` | `grava_json` atômico (temporário no mesmo diretório + `os.replace`) para inventário e `contents.json` |
| regressão de corpo HTTP truncado | `truncated_http_body_regression` | corpo menor que `Content-Length` (ou leitura sem EOF) = `falha_http:IncompleteRead`, como na v2 |
| caminho escapa da raiz | `path_traversal` | alvo resolvido tem de ficar dentro da base; senão `caminho_inseguro`, sem baixar |
| contrato de orçamento ambíguo | `metadata_outside_budget`, `rejected_transfer_budget` | três contadores: `bytes_transferidos` (tudo que veio da rede, inclusive recusados e metadados), `bytes_aceitos` (corpos gravados) e `bytes_metadados`. O limite total vale para os **transferidos** |

### 3. Exposição (`verifica_exposicao` v1 → v2)

| achado | caso | correção proposta |
|---|---|---|
| fonte ausente vira zero/ok | EXP-03 | pasta requisitada ausente = INDETERMINADO |
| cor do Git descarta a linha | EXP-08 | `git --no-pager -c color.ui=never -c core.quotePath=false grep --no-color -z` |
| saída não interpretada vira zero | EXP-06 | qualquer linha não interpretada = INDETERMINADO |
| só o primeiro match por linha | EXP-09 | `finditer`: um registro por match, com intervalo, termo, vizinhança e motivo específico de omissão |
| categoria enganosa | EXP-01, EXP-05 | `tests/` antes de código; "resultado do motor" só por nome e extensão de artefato; ressalva junto das contagens |

Depois, rerodar a verificação local no commit `bf46d51f` (read-only). `resumo_exposicao.md` e
`nota_registro_29-09.md` ganham **versões corrigidas novas**: nada de ES I sem id/código até a busca nova mostrar isso.
Níveis não mudam.

### 4. P3 → P3.1 (redação, não aplicada)

Redação inequívoca para os seguintes pontos:

- denominador de E4 por ocorrências da listagem congelada;
- documento = (curso, sha256) para E3, mínimos e gold;
- cobertura por ocorrência;
- regra das duplicatas por eixo;
- mínimo por curso marcado como limiar introduzido [C];
- mínimos 100/80 com a mudança de unidade marcada [C];
- estabilidade de bloco por entry/ID;
- aplicação ao lote conhecido = exploratória.

Cada sugestão de `sugestoes_redacao_p3.md` vai para uma tabela como aceita, modificada ou rejeitada, com motivo. Nada
é adotado automaticamente, e a P3.1 não é aplicada nem contada.

### 5. Verificação

1. **Vermelho primeiro:** portar os contraexemplos pertinentes para pytest nas cópias v4, rodar contra a v3 e
   registrar a falha.
2. **Correção** e depois verde.
3. **Regressões:** 73 testes da etapa 3, 45 da etapa 2 e os 5 casos anteriores pelo reprodutor v2×v3×v4.
4. **Dependências:** fixtures com python-docx, openpyxl, python-pptx e pypdf (instalados, **não declarados** no
   `pyproject`; só teste) e verificação independente do gerador (pypdf × PyMuPDF). As dependências do produto
   (`src.builder...`) são reais, sem stubs. O relatório distingue cada uma.

Opcional (fora dos 5 pontos pedidos): **CONF01**, resultado global de integridade em `confere_fontes` incluindo o selo
do inventário. Sem autorização, fica "pendente".

## Fora de escopo

Rede, gold real, adjudicação, motor, build, replay, recompilação de vocabulário, escolha de população, cálculo de
elegibilidade pela P3/P3.1, `src/`, exceção do gitleaks, commit até o Gate 2.

## Preservação

Etapas de 29/09, 2 e 3 intactas: ZIPs, `.frzero/`, manifestos (`manifesto_etapa3.json` continua válido, pois nada
dentro de `validacao_externa_etapa3_29-09/` é editado) e as evidências do GPT.

## Aceite

- Cada contraexemplo portado falha na v3 e passa na v4.
- 73 + 45 testes anteriores e os 5 casos anteriores verdes.
- Busca de exposição sem falso zero nos casos EXP.
- P3.1 com a tabela de sugestões.

Entregas:

- `relatorio_correcoes_etapa3.md`, com cada achado corrigido, pendente ou contestado, arquivo:linha, teste
  antes/depois, comandos, contagens, logs, limites dos stubs, arquivos e hashes, e pendências;
- `reprodutores_pos_correcao_etapa3.json`, arquivo novo;
- diffs v3→v4.

Testes verdes não são aprovação metodológica nem avançam Gate.

---

# Adendo 2 (29/09, depois da complementação): decisões restantes. AGUARDANDO DECISÃO

Estado conferido:

- branch `feat/motor-atribuicao`, HEAD `bf46d51f`, 4 stashes;
- correções v4/v2 e ZIP `44a63910…` preservados; o ZIP é o retrato aceito da organização das evidências;
- nada implementado neste adendo e nenhuma suíte reexecutada.

As regras abaixo são propostas. Nenhuma foi aplicada ao lote, e nenhuma usa impacto estimado em elegibilidade como
justificativa.

## A1. Cegamento e binários: R-VIS. NÃO APROVADA (Gate 1 parcial de 29/09); nada implementado

**Classificação:** "sem OCR" (Gate 1) proibiu acrescentar OCR. Não autorizou entregar pixels não examinados. Estão
**pendentes**, sem aceitação:

- texto de PDF em imagem;
- imagens soltas e embutidas;
- OLE legado;
- MP4;
- XMP;
- saídas de notebook.

**Retificação da versão anterior deste adendo.** Retiro duas alegações sem sustentação:

1. que a origem institucional impediria conteúdo proibido: a proveniência não diz nada sobre o conteúdo que o
   professor publicou;
2. que a política conservadora recusaria necessariamente qualquer PDF: isso depende de como se define inspeção e não
   é consequência lógica.

**Três dimensões distintas, que uma não substitui a outra:**

| dimensão | o que garante | o que não garante |
|---|---|---|
| integridade dos bytes (sha256 conferido contra o inventário congelado) | que o arquivo entregue é o mesmo registrado na aquisição | nada sobre o que o arquivo contém |
| confiança na aquisição (`proveniencia_confirmada`, vínculo pelo inventário) | que o arquivo veio da `fileurl` daquele módulo, pelo processo registrado | ausência de conteúdo proibido: o servidor entrega o que foi publicado |
| inspeção do conteúdo (texto, XML, metadados) | ausência das assinaturas conhecidas **nas estruturas examinadas** | nada sobre pixels, vetores ou estruturas não examinadas |

**Consequência:**

- Entregar pixels e vetores não examinados exige **aceitar expressamente esse risco residual**, como decisão própria.
  `proveniencia_confirmada = true` não substitui essa aceitação.
- Até lá, **nenhuma liberação visual** foi implementada, e o pacote **não está liberado para uso real**.
- As opções continuam:
  - a) recusar o que não é examinável, com a recusa de material legítimo documentada;
  - b) aceitar expressamente o risco residual dos pixels, examinando todas as estruturas textuais: metadados de
    imagem, XMP, JSON decodificado de notebooks;
  - c) outra política.
- Em qualquer caso, OLE legado solto e MP4 continuam recusáveis por conteúdo textual e ativo não examinado. Isso não
  foi aplicado.

## A2. Orçamento de metadados: R-META. AUTORIZADO e IMPLEMENTADO (Gate 1 parcial de 29/09; resultados no relatório, §6)

**Estado do cliente atual.** Em `src/builder/sources/moodle.py`, `MoodleClient._call` (linhas 414–423) faz
`urlopen(...)` e `json.loads(r.read().decode())`. Toda chamada de webservice passa por ele: `site_info` (425),
`get_users_courses` (428) e `get_course_contents` (431). A resposta bruta nunca é exposta; por isso a v4 registrou o
impedimento.

**Menor alteração proposta** (só `MoodleClient`; downloads, `login` e `download_course` ficam como estão):

1. `__init__`: acrescentar `self.bytes_recebidos = 0` e `self.limite_bytes = None`. `None` preserva o comportamento
   atual.
2. `_call`: trocar `r.read()` por `bruto = self._le_resposta(r)` e decodificar depois. A contagem é dos bytes do corpo
   efetivamente lidos, antes de decodificar; nunca do JSON reserializado.
3. Novo `_le_resposta(r)`:
   - **sem limite:** `r.read()` (o http.client já levanta `IncompleteRead` com Content-Length) e soma a
     `bytes_recebidos`;
   - **com limite:** `teto = limite_bytes - bytes_recebidos` e `r.read(teto)`, somando o que foi lido **antes** de
     qualquer exceção;
   - **corpo menor que o Content-Length:** com `len < teto`, levanta `http.client.IncompleteRead` (transferência
     incompleta); com `len == teto`, levanta `OrcamentoExcedido`;
   - **sem Content-Length e `len == teto`:** levanta `OrcamentoExcedido`, porque confirmar o fim exigiria ler além do
     orçamento (conservador);
   - `teto <= 0` levanta `OrcamentoExcedido` sem fazer a requisição.
4. Nova exceção `OrcamentoExcedido(RuntimeError)` no módulo, com `bytes_lidos`.
5. Os cabeçalhos HTTP não são contados. A limitação fica declarada.

**Testes com transporte falso** (`tests/test_moodle.py`; `urlopen` do módulo substituído por
`http.client.HTTPResponse` sobre BytesIO):

- conta exatamente o tamanho do corpo;
- é cumulativo entre chamadas;
- limite estourado levanta `OrcamentoExcedido` e conta o que foi lido;
- corpo truncado com Content-Length levanta `IncompleteRead`;
- `limite_bytes = None` mantém o resultado atual (os testes existentes do módulo continuam verdes);
- `teto <= 0` não faz a requisição.

**No `adquire` (v5):**

- antes de cada chamada de metadados, `cli.limite_bytes = cli.bytes_recebidos + restante`, com
  `restante = bytes_totais_max − bytes_transferidos`. Os downloads continuam lidos pelo `baixa_arquivo`, fora do
  cliente, e o limite do cliente passa a respeitar o orçamento comum;
- o delta de `cli.bytes_recebidos` em cada chamada de metadados vai para `bytes_metadados` e `bytes_transferidos`;
- `OrcamentoExcedido` em `get_course_contents` vira erro do curso `nao_baixado_orcamento_real (metadados)`;
- o impedimento sai do inventário;
- `test_metadata_outside_budget` passa a exigir a contagem real (com `MoodleClient` verdadeiro e transporte falso).

**Arquivos:** `src/builder/sources/moodle.py`, `tests/test_moodle.py`,
`correcoes/aquisicao/adquire.py` (v5) e `test_adquire_v5.py`.

## A3. Contrato das páginas: R-PAGE. IMPLEMENTADA como regra operacional provisória (Gate 1 parcial de 29/09)

A regra foi **inferida das respostas disponíveis, inclusive as do lote** (8 das 16 respostas vêm da aquisição de
29/09). **Não é contrato confirmado do Moodle.** A confirmação da versão continua pendente, sem consulta externa
nesta etapa.

**Evidência local:**

- 16 respostas reais de `core_course_get_contents` congeladas:
  - 8 em `docs/reports/_harness-2026-09-02/moodle_contents/`;
  - 8 em `.frzero/validacao_externa_aquisicao_29-09/*/raw/moodle/`.
- Juntas somam 38 módulos `page`.
- Em **todos os 38**, há exatamente um conteúdo `index.html` com `filepath "/"`, `filesize 0`, `sortorder 1` e sem
  `mimetype`.
- Um deles tem também um anexo (`.cpp`) listado **antes**, com `sortorder 0`, tamanho real e `mimetype`.
- O teste do produto `tests/test_moodle_sync.py:219–223` reproduz esse caso (anexo antes do `index.html`).

**Regra proposta R-PAGE:** o HTML principal é o conteúdo com `filename == "index.html"`, `filepath == "/"` e
`filesize == 0`.

- Exatamente um candidato: ocorrência do alvo.
- Zero ou mais de um: ocorrência não coberta, com a causa registrada.
- Os demais conteúdos da página são anexos (fora do alvo).
- `index.htm` sai da redação: não há evidência local.
- **Mudança de código necessária:** a v4 do `adquire` e do gerador trata **qualquer** `.html/.htm` de página como
  HTML principal. Um anexo `notas.html` seria confundido com ele.

**Lacuna:** a evidência é empírica, de uma instância (PUCRS). Não há cópia local do contrato do Moodle.

**Consulta externa necessária (não executada):**

1. obter `release` de `core_webservice_get_site_info` da instância (rede autenticada);
2. ler, no código-fonte do Moodle dessa versão, `mod/page/lib.php`, função `page_export_contents()`, e confirmar que
   ela sempre emite um único `index.html` gerado (`filepath "/"`, `filesize 0`, `sortorder 1`) além dos arquivos da
   área `content`, e se um arquivo da área pode se chamar `index.html`.

## A4. P3.1 §4.2: "regra de status já congelada"

**Não existe regra aprovada.** O mais próximo:

- o pré-registro `2026-09-29-regime-vocab-validacao-externa-preregistro.md` §4.2 (sha256 `c9b1cbdd…`, **não
  assinado**);
- o `gold/gold_schema.md`, versão `gold-externo-1` (sha256 `bbacd543…`): coluna `status`, regras de consistência 3 e 5
  e tradução, linhas 38–39;
- as `gold/instrucoes_adjudicador.md` (sha256 `16612dfb…`), item 1: "o nome do arquivo e a seção do Moodle são pistas".

Os três estão registrados por hash em `manifesto_preparacao.json`, mas não aprovados. Nenhum trata de conflito
contextual. A expressão "já congelada" da P3.1 era imprecisa.

**Regra proposta R-CC (não aprovada):**

1. **Rótulo pelo conteúdo.** O adjudicador rotula o documento pelo conteúdo; ocorrências e seções são pistas.
2. **Conteúdo sustenta mais de uma unidade ou tópico:** `status = avaliado` com vários ids (`U01|U03`; tópicos em
   `sub_primaria`/`sub_aceita`). É o mecanismo que o `gold-externo-1` já prevê. Conta normalmente nos eixos oficiais
   (um documento, uma linha).
3. **Só a subunidade é ambígua** (a unidade é determinável pelo conteúdo, e o tópico depende do contexto da
   ocorrência):
   - `status = avaliado`, `unidade` = os ids determinados, `sub_primaria = ?` e `sub_aceita = ?`;
   - `?` é um marcador novo do `gold-externo-2`: "subunidade não determinável por conflito contextual";
   - o documento conta no eixo da unidade e sai dos denominadores das subunidades primária e aceita;
   - é contado e relatado.

   Se o conteúdo sustenta mais de um tópico, usam-se vários ids, não `?`. O caso inverso (subunidade determinável e
   unidade ambígua) não existe, porque todo tópico pertence a uma unidade (regra 1 do `gold-externo-1`).
4. **Conteúdo não decide a unidade e as ocorrências estão em seções de unidades diferentes:** `status = excluido`, com
   `observacao` iniciando por `conflito_contextual:` e listando os contextos.

   | onde | efeito do documento em conflito |
   |---|---|
   | eixos do gold (unidade, subunidade primária, subunidade aceita) | fora |
   | mínimos pós-gold (80 total, 10 por curso) | fora |
   | E3 e mínimos pré-gold | continua (é cadastro de cobertura, anterior ao gold) |
   | E4 (cobertura) | continua |
   | estabilidade de bloco | continua (comparação entre braços, não usa gold) |

   Em qualquer caso, é contado e relatado por curso.
5. **Sensibilidade, com consequência fixada antes dos resultados:**
   - A_novo e C_novo são calculados duas vezes: no principal e com cada exclusão por conflito contada como erro no eixo
     afetado (documento `excluido` em todos os eixos; `?` nos eixos de subunidade);
   - **o veredicto oficial é "aprovado" só se aprovar nas duas contas**; aprovado só no principal = "não aprovado
     (dependente das exclusões por conflito)";
   - o limiar não muda;
   - B_novo exige gold para medir perda e, por isso, não tem conta de sensibilidade. O número de documentos e eixos
     excluídos por conflito acompanha o veredicto de B.
6. **Momento:** o adjudicador decide durante a adjudicação, numa passada, antes de qualquer build, replay ou captura
   dos cursos novos. O gold é congelado por sha256 antes do build (`gold-externo-1`, regra 5), e depois disso nenhum
   status muda. O executor não reclassifica.
7. **Versão:** exige `gold-externo-2` (convenção `conflito_contextual:`, marcador `?` e sensibilidade) e instruções
   v2, ambos arquivos novos e ainda só propostos. O `gold-externo-1` não é editado. Nenhum gold foi produzido.

## A5. Arquivos que uma nova implementação alteraria

| decisão | arquivos |
|---|---|
| R-VIS | `correcoes/pacote_cego/gera_pacote_cego.py` (v5): metadados de imagem, XMP, notebooks, condição de proveniência para conteúdo visual, OLE/MP4 soltos; testes v5 |
| R-META | `src/builder/sources/moodle.py`, `tests/test_moodle.py` (**precisa de autorização para `src/`**); `correcoes/aquisicao/adquire.py` (v5) e testes |
| R-PAGE | `adquire.py` (v5) e `gera_pacote_cego.py` (v5): seleção do HTML principal; testes com o caso real do anexo antes do `index.html`; P3.1 §2.2 |
| R-CC | documentos só: P3.1 §4.2 e, se aprovada, `gold-externo-2` e instruções v2 como arquivos novos |

## A6. Critérios de aceite da próxima implementação

- **R-VIS:** um teste vermelho → verde por caso.
  - Casos recusados:
    - PNG com `tEXt` contendo saída do motor;
    - JPEG com XMP e com EXIF contendo token;
    - PDF com XMP contendo saída do motor;
    - notebook com `_` escondendo a assinatura;
    - saída `image/png` com metadado proibido;
    - `doc` e `mp4` soltos;
    - PDF ou imagem sem proveniência confirmada;
    - chunk PNG desconhecido.
  - Controles aceitos: os mesmos arquivos limpos com proveniência confirmada.
- **R-META:**
  - os testes do cliente listados em A2;
  - no `adquire`, `bytes_metadados` igual ao tamanho do corpo recebido (não o reserializado) e metadados que estouram
    o orçamento recusados;
  - sem mudança de resultado com `limite_bytes = None`: a suíte do produto de `test_moodle.py` e a regressão completa
    `python -m pytest tests -q` verdes.
- **R-PAGE:**
  - anexo `.html` não vira HTML principal;
  - página com zero ou dois candidatos gera ocorrência não coberta com a causa.
- **Regressão:** as suítes v4 (131) e as da etapa 3 (73) e etapa 2 (45), rodadas em processos separados; os 5 casos
  anteriores; o vermelho final registrado.

## A7. Três aprovações distintas

1. **Autorização para implementar:** decidir R-VIS (inclusive a alteração do contrato do Gate 1), R-META (inclusive a
   permissão para alterar `src/`) e R-PAGE. Nada disso vale sem decisão explícita.
2. **Gate 2 para commit:** depois da implementação, dos testes e da revisão definida no workflow, e antes de qualquer
   commit. Hoje nada está commitado.
3. **Aprovação metodológica:** P3.1 (com R-CC e R-PAGE na redação), R-VIS como mudança de contrato e o pré-registro.
   Independe dos testes verdes e não autoriza gold, aquisição ou aplicação ao lote.

---

# Adendo 3 (29/09): execução do Gate 1 parcial

- **R-META (implementado):** alteração em `src/builder/sources/moodle.py` (`MoodleClient`) e `tests/test_moodle.py`;
  `adquire` v5 em `../validacao_externa_etapa3_correcoes_v5_29-09/`.
- **R-PAGE (implementado, provisório):** `adquire` v5 e gerador v5, na mesma pasta.
- **R-VIS:** não aprovada e não implementada (A1). O pacote não está liberado para uso real.
- **R-CC:** só proposta documental (A4, P3.1 §4.2). Sem gold nem adjudicação.
- **Evidência:** diferenças, resultados, hashes e pendências estão no `relatorio_correcoes_etapa3.md`, §6, e em
  `../validacao_externa_etapa3_correcoes_v5_29-09/reprodutores_v5_etapa3.json`.
- **Aprovações pendentes e separadas:** Gate 2 para commit e aprovação metodológica.
- **Continuação do R-META (catálogo):** os dois caminhos achados pelo revisor por inspeção foram reproduzidos (10
  testes vermelhos) e corrigidos (10 verdes; aquisição v5 40/40):
  - o consumo persistido é lido antes da requisição, e um registro ilegível não vira zero;
  - uma interrupção grava os bytes e propaga.

  Grafo local atualizado (`graphify update .`, sem LLM). Detalhe no relatório, §6.1.
