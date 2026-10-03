# Correções pós-revisão da etapa 3: relatório (29/09/2026)

## Resultado

- Os defeitos P1 e P2 demonstrados pelo parecer foram corrigidos nas cópias v4 (pacote cego, aquisição) e v2
  (exposição, conferência).
- Ficam fora disso dois impedimentos detectados, as limitações aceitas e duas decisões pendentes (§3).
- Os 58 testes novos rodaram contra o código antigo: 49 falharam e 9 são controles. Depois das correções, os 58
  passam.
- As pastas inteiras passam 131/131. Regressões: suítes originais da etapa 3 com 73/73 e da etapa 2 com 45/45.
- Os 5 casos anteriores rodaram em processos separados: v2 com defeito, v3 e v4 corrigidos.

**Testes verdes não são aprovação metodológica nem avançam Gate.** Parado antes do Gate 2, sem commit e sem nova
chamada Astra.

**Decisões do Gate 1 aplicadas:**

- recusa conservadora de membros binários opacos, inclusive `printerSettings`, **exceto imagens embutidas** (§3.3);
- PDF com anexos (estrutura) separado da inspeção de texto;
- bytes reais transferidos contados, com três contadores;
- sha256 do inventário exigido;
- CONF01 incluído;
- nomes AQ canônicos.

## 1. Achados da revisão, por categoria

Categorias:

- **DC (defeito corrigido):** o comportamento errado foi reproduzido por teste vermelho e o teste passa depois da
  correção.
- **ID (impedimento detectado):** a correção depende de algo fora do escopo autorizado (alterar `src/`, ou rede). O
  item continua pendente; o teste só verifica que o impedimento fica registrado.
- **LA (limitação aceita):** limite conhecido, declarado e aceito numa decisão já tomada (Gate 1) ou que não pode ser
  eliminado por construção. É registrado e não é tratado como defeito.
- **DP (decisão pendente):** o código segue uma interpretação que diverge ou não é coberta pelas decisões do Gate 1.
  Precisa de decisão (§3.3).

Referências relativas a `correcoes/pacote_cego/gera_pacote_cego.py` (G), `correcoes/aquisicao/adquire.py` (A),
`exposicao/verifica_exposicao.py` (X) e `conferencia/confere_fontes.py` (F).

### Item 1: pacote cego

| achado | cat. | correção ou registro | teste |
|---|---|---|---|
| XML por regex (PC02–08, PC13, PC27–30) | DC | `_varre_xml` G:271: expat, codificação pela declaração/BOM, entidades resolvidas; DTD e `<!ENTITY>` recusados (G:280); texto, atributos, comentários e instruções varridos. Texto solto: BOM/UTF-16 (G:251) e entidades HTML (G:241) | `test_verifica_material_v4[PC06/07/08, PC13, PC27, PC28, PC29, PC30, docx-dtd-entidade, txt-utf16-motor, html-entidade-motor]`, `test_PC27_plano_docx...` |
| membro desconhecido aceito (PC09, PC10) | DC | classes explícitas em `verifica_conteiner` G:340; binário opaco ou desconhecido recusado (G:399), inclusive `printerSettings`, fontes, EMF/WMF, `.bin`, `.dat`; `doc/ppt/xls/mp4` recusados como membro | `[PC09, PC10, docx-fonte-embutida, docx-emf, zip-com-doc-ole]` |
| imagem embutida aceita só pela assinatura | **DP** | G:392 trata png/jpg/jpeg/gif embutidos como mídia da allowlist. Diverge da letra do Gate 1 (§3.3) | — (sem teste de recusa: comportamento a decidir) |
| negações do Leitor não valem no ZIP (PC11, PC12) | DC | `motivo_caminho` G:150, usado pelo Leitor e pelos membros | `[PC11, PC12]` |
| PDF: escape `#46` vence a busca literal (PC20) | DC | `verifica_pdf` G:299 com PyMuPDF: árvore de embutidos, objetos `/EmbeddedFile`/`/Filespec`+`/EF` (G:318), anotação de anexo (G:324); PDF que não abre = recusa | `[PC20, pdf-anexo-orfao, pdf-anexo-por-anotacao, pdf-invalido]` |
| texto extraível de PDF não varrido (PC21) | DC | texto das páginas, metadados do dicionário Info, anotações e links varridos, separados da estrutura | `[PC21]` |
| texto de PDF só em imagem | **DP** (corrigido depois: "sem OCR" não autorizou entregar pixels não examinados; ver issue, adendo 2, A1) | `paginas_sem_texto` por fonte no manifesto (G:332, G:699) | `test_pdf_sem_camada_de_texto_fica_registrado` |
| PDF recusado por comentário após EOF (PC31) | DC | a detecção estrutural não olha comentários | `[PC31]` |
| ligação sem inventário não confirma módulo (PC25) | LA | `proveniencia_confirmada: false` para toda ligação sem inventário (G:697). A P3.1 §2 não conta essa ligação como cobertura | `test_PC25...` |
| inventário trocado depois do congelamento (PC24, parte) | DC | `inventario_sha256` esperado é obrigatório; divergência aborta (G:483) | `test_inventario_exige_sha_esperado[sem-sha, sha-divergente]` |
| vínculo errado dentro do inventário congelado (PC24, parte) | LA | o sha256 verifica a identidade do inventário, não a verdade do vínculo; checagem barata de tamanho no §3.2 | `conferencia/confere_tamanhos.py` (read-only) |
| anexo de página reentra como sobra (PC26) | DC | um arquivo igual (nome, tamanho) a anexo da API não vira sobra (G:605, G:629); com inventário, nada fora dele é entregue (G:638) | `test_PC26...`, `test_com_inventario_arquivo_fora_do_inventario...` |
| recusa de material legítimo (PC17 e as novas: pptx com `printerSettings`, docx com fonte/EMF) | LA (Gate 1: sem exceção para cobertura) | mantida e documentada | `[pptx-padrao-printerSettings-recusado]` |
| controles (PC01, 14–16, 18, 19, 22, 23) | — | mantidos | testes herdados verdes |

### Item 2: aquisição. Nomes canônicos e correspondência

| nome canônico | ID JSON do revisor | ID do parecer | cat. | correção ou registro | teste |
|---|---|---|---|---|---|
| `partial_write` | AQ01 | AQ-01 | DC | registro antes da gravação; `.parcial` + `os.replace`; falha mantém `caminho_parcial` + `bytes_gravados` (A:273–285) | `test_partial_write` |
| `interrupt_after_write` | AQ02 | AQ-02 | DC | `status: gravando` com `caminho` e `caminho_parcial` antes de gravar (A:273) | `[escrita_do_parcial]`, `[publicacao_do_arquivo]` |
| `baixar_interrupt_after_write` | AQ07 | AQ-02 | DC | o `finally` publica o registro `gravando` | `test_baixar_interrupt_after_write` |
| `inventory_write_interruption` | AQ06 | AQ-03 | DC | `grava_json` atômico (A:91–97) | `[escrita_do_temporario]`, `[publicacao]` |
| `truncated_http_body_regression` | AQ08 | AQ-04 | DC | corpo < Content-Length = `falha_http:IncompleteRead` (A:199) | `http.client.HTTPResponse` real sobre BytesIO |
| `path_traversal` | AQ05 | AQ-06 | DC | alvo resolvido fora da base = `caminho_inseguro` (A:254) | `test_path_traversal` |
| `rejected_transfer_budget` | AQ04 | AQ-05 | DC | `bytes_transferidos` inclui recusados e sondagem (A:264) | `test_rejected_transfer_budget` |
| `probe_respects_remaining_budget` | novo | AQ-05 | DC | leitura ≤ `min(limite+1, restante)` (A:183) | `test_probe_respects_remaining_budget` |
| `metadata_outside_budget` | AQ03 | AQ-05 | **ID na v4 → DC na v5 (§6)** | o `MoodleClient` do produto lê e decodifica `core_course_get_contents` sem expor o tamanho recebido; medir exige alterar `src/`. O inventário grava `bytes_metadados: null` e o impedimento (A:175, A:343); o JSON reserializado não é contado | `test_metadata_outside_budget`: **verifica só o registro do impedimento**, não que o orçamento cubra metadados |
| `grava_json` sem fsync | — | — | LA | cobre interrupção do processo, não queda de energia | — |

### Itens 3 a 9

- **3. Reprodutor (DC).**
  - Regressão HTTP da v3 corrigida (AQ08).
  - Os 5 casos anteriores rodaram por versão em processo próprio (`roda_verificacao.py --versao`):
    - plano: v2 copia, v3/v4 `PlanoRecusado`;
    - ZIP: v2 entrega, v3/v4 recusam;
    - outra seção: v2 liga, v3/v4 `origem_nao_confirmada`;
    - anexo: v2 `ValueError`, v3/v4 com referência válida;
    - limite: v2 `ok`, v3 `acima_do_limite_real`, v4 `nao_baixado_orcamento_real` com 5 bytes transferidos.
  - Dependência estática: o gerador lê `validacao_externa_29-09/gold/instrucoes_adjudicador.md` do repositório. Ela
    não está neste ZIP e tem de acompanhar uma reprodução externa.
- **4. Diffs e testes herdados:** §4.
- **5. P3 → P3.1** (`proposta_normativa_populacao_p3_1.md`):
  - denominador por ocorrências; documento = (curso, sha256); cobertura com proveniência; mudanças de unidade e
    mínimo por curso marcados [C];
  - aplicação ao lote conhecido declarada exploratória;
  - 17 sugestões do parecer: 13 aceitas, 4 modificadas, nenhuma rejeitada;
  - **não aplicada**.
- **6. Bloco (DC na redação):**
  - estabilidade por entry, pelo mesmo ID, com a sanidade de IDs antes de comparar;
  - falha na sanidade deixa B_novo "não avaliado";
  - acurácia de bloco fora.
- **7. Exposição (DC):**

  | caso | correção |
  |---|---|
  | EXP-03, fonte ausente | vira INDETERMINADO (X:115, X:165) |
  | EXP-08, cor do Git | `-c color.*=never`, `--no-color` (X:48, X:117) |
  | EXP-06, saída não interpretada | vira INDETERMINADO (X:129) |
  | EXP-09, só o primeiro match | `finditer` com intervalo (X:134); linha do git sem match no Python vira INDETERMINADO (X:135) |
  | EXP-01, EXP-05, categorias | X:34, X:36; motivo de omissão específico (X:91) |

  - Busca rerodada só no commit `bf46d51f`: 21/21 `ok`. ES I tem 221 matches, todos em "Software II".
  - Afirmações corrigidas em `exposicao/resumo_exposicao_v2.md` e `registro/nota_registro_29-09_v2.md`.
  - Nenhum nível alterado.
  - REG-02 (a redação troca o nome inteiro, não fragmentos) é **LA**.
- **8. Registro (DC):** o ponto 2 da nota foi reescrito (v2). A cópia redigida da exposição v2 foi feita com a regra
  da etapa 3.
- **9. Conferência, CONF01 (DC):**
  - `integridade_global` = bytes conferem **E** inventário completo **E** selo do inventário (F:95);
  - rodada real, read-only: `true`.

## 2. Testes, comandos e contagens

Tudo foi reproduzido por um comando: `python -B roda_verificacao.py`, a partir desta pasta. Cada versão roda em
processo próprio; o vermelho usa uma cópia espelhada temporária em `c1-3/_replay_vermelho_tmp`, removida ao final.

| área | testes novos | vermelho (código antigo) | verde (v4/v2) | pasta inteira |
|---|---:|---|---|---|
| pacote cego | 39 | 30 falham, 9 passam (5 controles limpos, reabertura por bibliotecas, 3 PDFs com nome literal que a v3 já pegava) | 39/39 | 101/101 |
| aquisição | 11 | 11 falham | 11/11 | 17/17 |
| exposição | 6 | 6 falham | 6/6 | 11/11 |
| conferência | 2 | 2 falham | 2/2 | 2/2 |
| **total** | **58** | **49 falham** | **58/58** | **131/131** |

- **Regressão sem alteração:** etapa 3 (v3/v1) com 62 + 6 + 5 = 73; etapa 2 com 45.
- **Logs em `logs/`:**
  - `vermelho_inicial_*` (antes das correções);
  - `vermelho_final_*` (testes finais contra o código antigo);
  - `verde_novos_*`, `verde_pasta_*`, `regressao_*`;
  - JUnit XML de cada execução.
- **Resultados por teste, com a correspondência AQ:** `reprodutores_pos_correcao_etapa3.json`.

Comandos adicionais, todos read-only e sem rede:

- `python -B -m pytest <área> -q -p no:cacheprovider`;
- `python -B exposicao/verifica_exposicao.py exposicao/entrada_exposicao.json exposicao/exposicao_local_v2.json`;
- `python -B registro/redige_divulgacao_v2.py`;
- `python -B conferencia/confere_fontes.py`;
- `python -B conferencia/confere_tamanhos.py`.

**Dependências efetivamente usadas (Python 3.11):**

- **Reais no código:** `src.builder.extraction`, `src.builder.sources.moodle` e PyMuPDF 1.27.2.3 (declarado).
- **Só nos testes, instalados e não declarados:** pypdf 6.14.2, python-docx 1.2.0, openpyxl 3.1.5, python-pptx 1.0.2.
- **Stubs:** nenhum de `src/` localmente. A rede foi trocada por cliente e `urlopen` falsos e por
  `http.client.HTTPResponse` real sobre BytesIO.
- **Diferença para a revisão:** o parecer usou stubs de `src/`, então os resultados não são comparáveis linha a linha
  nos casos que dependem de rótulos.

## 3. O que impede a aprovação

### 3.1 Impedimentos detectados (pendentes)

1. ~~**`metadata_outside_budget`**~~ **resolvido na v5 (§6)**, com autorização para `src/`. Na v4, o teste verde
   verificava só o registro do impedimento.
2. **HTML principal de página contra o contrato da API** (P3.1 §2.2):
   - a regra R-PAGE foi implementada na v5 como regra operacional provisória, inferida das respostas locais,
     inclusive o lote;
   - a confirmação no Moodle da versão da instância continua pendente, sem consulta externa nesta etapa.

### 3.2 Limitações aceitas (registradas)

1. ~~Texto de PDF em imagem (sem OCR, Gate 1)~~. **Reclassificado como decisão pendente:** "sem OCR" proibiu acrescentar
   OCR, não autorizou entregar pixels não examinados. Ver §3.3 e a issue, adendo 2, A1. O registro
   `paginas_sem_texto` continua.
2. **Recusa de material legítimo** pela decisão conservadora: ZIP de código, pptx com `printerSettings`, docx com
   fonte ou EMF/WMF. É sem exceção para cobertura (Gate 1). O impacto no lote **não foi calculado**.
3. **PC24, vínculo errado já congelado no inventário:**
   - O sha256 esperado verifica a identidade do inventário, não a verdade de cada vínculo.
   - Checagem barata (`conferencia/confere_tamanhos.py`, read-only): o `filesize` declarado no `contents.json`
     congelado foi comparado com o tamanho real do arquivo ligado a cada registro `ok`. Resultado: 262 iguais,
     0 divergentes, 5 HTML de página sem declaração (a API informa 0).
   - Alcance: 260 arquivos têm tamanho único no curso, e uma troca entre eles seria detectada. 2 arquivos de bytes
     diferentes têm o mesmo tamanho, e uma troca entre eles passaria.
   - **Correção de uma afirmação anterior:** um novo download **não prova** o vínculo antigo. Ele estabelece uma nova
     proveniência: o que o servidor entrega *agora* para aquela `fileurl`.
     - Hash igual ao registrado, com `timemodified` e `filesize` iguais aos do `contents.json` congelado, é
       corroboração forte de que o registro antigo corresponde à publicação atual. Não é demonstração do download de
       29/09, que não pode ser refeito.
     - Hash diferente não prova vínculo errado: o arquivo pode ter sido atualizado no Moodle.
     - Um novo download também exigiria manifesto e Gate de rede próprios.
4. **Ligação sem inventário** (PC25): nome + tamanho não confirma módulo; ela fica marcada e não conta como cobertura.
5. **REG-02:** a redação cobre o nome inteiro, não fragmentos em saídas futuras.
6. **`grava_json` sem fsync.**

### 3.3 Binários ainda aceitos sem inspeção suficiente (decisão pendente)

O Gate 1 decidiu: "recusar quando não houver inspeção suficiente, inclusive `printerSettings`. Assinatura e busca
textual nos bytes não demonstram ausência de segredo ou predição". A v4 continua aceitando o seguinte **só pela
assinatura (magic bytes)**, sem examinar o conteúdo:

| o quê | onde entra | o que não é examinado | relação com o Gate 1 |
|---|---|---|---|
| **imagens embutidas** png/jpg/jpeg/gif em docx/pptx/xlsx/odt/odp/ods/zip (inclui `docProps/thumbnail.jpeg` e `Thumbnails/thumbnail.png`) | G:392 (documento) e `verifica_material` para membros de ZIP | pixels e metadados (PNG `tEXt/zTXt/iTXt`, JPEG EXIF/XMP/COM, comentários GIF) | **diverge**: são membros binários sem inspeção suficiente, e o Gate 1 mandava recusar. Foram tratados como mídia da allowlist, por analogia com a imagem solta |
| imagens soltas png/jpg/jpeg/gif | `verifica_material` G:405 | pixels e metadados | não coberto pelo Gate 1 (que tratou de membros); o princípio da decisão se aplica igual |
| `doc/ppt/xls` soltos (OLE legado) | G:405, só `MAGIC` | todo o conteúdo: texto, macros VBA, objetos embutidos | não coberto pelo Gate 1; é **binário opaco**, o caso mais próximo do `printerSettings` |
| `mp4` solto | G:405, só `ftyp` | vídeo, áudio, metadados e legendas (texto) | não coberto pelo Gate 1 |
| imagens dentro de PDF; metadados XMP do PDF | `verifica_pdf` G:299 | pixels (sem OCR); XMP não é lido (só o dicionário Info) | o texto em imagem é **DP** (reclassificado; ver adendo 2, A1); o **XMP é lacuna pequena não decidida** |
| saídas embutidas em `ipynb` (imagens em base64) | varredura de texto G:241 | a base64 não é decodificada; a imagem não é examinada | não coberto |

**Decisão necessária (proposta, não aplicada):** uma regra única para mídia e binários soltos.

1. **Proposta:**
   - **(a) OLE legado soltos (`doc/ppt/xls`): recusar.** São contêineres opacos que podem trazer macros e objetos
     embutidos, e não há parser na biblioteca padrão nem em dependência declarada. É a mesma lógica do
     `printerSettings`.
   - **(b) Imagens, soltas e embutidas:** decidir entre
     - **b1)** recusar, que é a coerência estrita com o Gate 1 e derruba quase todos os slides e documentos com
       figura; ou
     - **b2)** aceitar como conteúdo visual, com duas condições: implementar a leitura estruturada dos metadados
       textuais (PNG tEXt/zTXt/iTXt, JPEG COM/XMP, comentário GIF), e aceitar explicitamente os pixels não
       examinados como limitação (LA), como já foi aceito para o texto de PDF em imagem.
   - **(c) `mp4` solto: recusar** até existir inspeção de trilhas de texto e metadados.
   - **(d) XMP do PDF e base64 de `ipynb`:** incluir na varredura (pequeno) ou aceitar como LA.
2. **Recomendação:** (a) recusar, (b2), (c) recusar, (d) incluir na varredura.
   - A b2 é a única que mantém adjudicável material visual comum sem fingir que ele foi inspecionado.
   - A b1 é a opção conservadora literal.
3. **Impacto no lote:** não calculado para nenhuma opção. Calcular exigiria aplicar a política aos arquivos reais,
   o que precisa de autorização. As contagens de formato do lote (`conferencia_fontes.json`) já são conhecidas por
   quem decide.

## 4. Arquivos e hashes das versões testadas

| arquivo | v3/v1 (etapa 3) sha256 | v4/v2 testado sha256 | diff |
|---|---|---|---|
| gera_pacote_cego.py | `66a8bdab…` | `ca045615…` | `diffs/diff_gerador_v3_v4.patch` (+183/−38) |
| adquire.py | `139509ec…` | `ceca5f52…` | `diffs/diff_adquire_v3_v4.patch` (+86/−34) |
| verifica_exposicao.py | `d668bfac…` | `fc36c8a7…` | `diffs/diff_verifica_exposicao_v1_v2.patch` (+57/−27) |
| confere_fontes.py | `be35381e…` | `554d1bac…` | `diffs/diff_confere_fontes_v1_v2.patch` (+5/−1) |

Os hashes completos estão em `reprodutores_pos_correcao_etapa3.json` (`execucao`) e em
`manifesto_correcoes_etapa3.json` (todos os arquivos desta pasta).

**Testes herdados alterados** (`diffs/diff_testes_herdados_v3_v4.patch`), todos por mudança pedida:

- **PDF válido nas fixtures:** o v4 recusa PDF que não abre. Mudou em `test_pacote_cego.py` (+24/−2), `_v2`
  (+5/−5) e `_v3` (+14/−12).
- **Em `_v3`:**
  - `DOCX_OK` sem fonte embutida;
  - `oleObject` com a mensagem "opaco";
  - XML de runs bem formado;
  - PDF falso com `/EmbeddedFile` esperando "ilegível";
  - testes de inventário declarando `inventario_sha256`.
- **`test_adquire_v3.py` (+12/−9):**
  - contadores `transferidos`/`aceitos`;
  - o caso 5/5 espera `nao_baixado_orcamento_real`;
  - gravação em `.parcial`;
  - esquema 3.

**Enfraquecimento:** dois casos herdados deixaram de exercitar o próprio mecanismo: o PDF falso não testa mais anexo,
e o caso 5/5 não testa mais o limite por arquivo. Os dois mecanismos têm teste novo com entrada válida.

**ZIP da entrega:** `Desktop/para-gpt/validacao_externa_etapa3_correcoes_29-09.zip`. Fora dele ficam:

- `exposicao/exposicao_local_v2.json`, o original com texto excedente;
- fontes acadêmicas (`.frzero/`), credenciais e o documento de instruções de 29/09.

## 5. Preservação e não aplicação

- A etapa 3 continua intacta: os 28 arquivos de `manifesto_etapa3.json` conferem, e as 5 entradas preservadas também.
- A etapa 2 continua intacta (26/26), e a preparação de 29/09 também (61/61). O ZIP da etapa 3 tem sha `8a41658a…`.
- As evidências do GPT estão sem alteração.
- As fontes `.frzero/` só foram lidas (conferências de bytes e de tamanhos).
- **Nem a P3 nem a P3.1 foram aplicadas**, e nenhuma elegibilidade foi calculada.
- Não houve rede, gold, adjudicação, motor, build, replay, recompilação, escolha de população nem instalação de
  dependência.
- Sem commit. Os 4 stashes estão intactos. `.codex/hooks.json`, de outra sessão, não foi tocado.
- Gitleaks: 1 falso positivo `sumologic-access-token` em `manifesto_correcoes_etapa3.json` (nome
  `resumo_exposicao_v2.md` seguido de sha256). É a mesma classe da etapa 3. Não foi criada allowlist nova.

## 6. Rodada v5: Gate 1 parcial (R-META e R-PAGE)

**Escopo autorizado:** R-META (inclusive `MoodleClient` e seus testes) e a correção técnica de R-PAGE. Ficaram de fora:

- **R-VIS:** não aprovada e não implementada. **O pacote não está liberado para uso real.**
- **R-CC:** só proposta documental (issue, adendo 2, A4; P3.1 §4.2).

O código está em `../validacao_externa_etapa3_correcoes_v5_29-09/`. As versões v4 ficaram intactas.

**Definição do orçamento:** bytes dos **corpos HTTP lidos pela aplicação**: respostas do webservice, medidas pelo
`MoodleClient`, e downloads de arquivos. **Não é todo o tráfego de rede:** cabeçalhos, TLS, retransmissões e outros
acessos ficam fora. O tamanho do JSON reserializado não é medida de transferência.

**Alteração em `src/builder/sources/moodle.py`** (`diffs/diff_src_moodle.patch`, +56/−1; sha256 depois `24430123…`):

- `MoodleClient` ganhou `bytes_recebidos`, `limite_bytes` (`None` = comportamento anterior) e `ultimo_corpo`.
- O corpo passa a ser lido em blocos, e cada bloco é contado ao chegar.
- O orçamento esgotado é verificado **antes de abrir a requisição**, em `_call`.
- Um Content-Length acima do orçamento restante não é lido.
- Corpo truncado levanta `http.client.IncompleteRead`, com o parcial.
- Corpo sem Content-Length que enche o orçamento levanta `OrcamentoExcedido`, com o parcial e sem sondar além do
  limite.
- Os bytes são contados também quando o JSON é inválido, a API devolve erro, a resposta vem incompleta ou há
  interrupção entre blocos.
- `site_info`, `get_users_courses` e `get_course_contents` passam por `_call`. `login` e `download_course` não mudaram.

**`adquire` v5** (`diffs/diff_adquire_v4_v5.patch`, +70/−18; sha256 `c06a63f5…`):

- **Catálogo:** entra no orçamento comum. Os bytes vão para `metadados_catalogo.json` (acumulados, gravados também na
  falha) e para `triagem.bytes_metadados_catalogo`.
- **Metadados de curso:** antes de cada `get_course_contents`, `limite_bytes` recebe o restante do orçamento comum.
  O delta entra em `bytes_metadados`/`bytes_transferidos` num `finally`, também quando a chamada falha.
- `OrcamentoExcedido` vira o erro do curso `nao_baixado_orcamento_real:metadados`.
- Triagem anterior à v5 (sem contagem do catálogo) gera um impedimento registrado.
- O inventário ganha `definicao_orcamento`.
- **R-PAGE:** o HTML principal é `index.html` com `filepath "/"` e `filesize 0`, exatamente um. Zero ou vários geram o
  registro `html_principal_ausente|ambiguo` (não coberto, no denominador). Os demais conteúdos são anexos, inclusive
  `.html`.

**Gerador v5** (`diffs/diff_gerador_v4_v5.patch`, +44/−22; sha256 `a88336eb…`):

- A mesma regra R-PAGE: `pagina_sem_html_principal` e `pagina_sem_fonte_local`, não adjudicáveis e visíveis. Antes,
  uma página sem arquivo sumia em silêncio.
- A ligação com inventário filtra pelo `papel`, o que resolve a colisão com um anexo `index.html`.
- Arquivo da pasta de páginas não vinculado não vira sobra.

**R-PAGE é regra operacional provisória:** foi inferida das 16 respostas locais disponíveis, **inclusive as 8 do lote**,
e não é contrato confirmado do Moodle. A confirmação continua pendente, sem consulta externa.

**Testes** (`python -B roda_verificacao_v5.py`, cada versão em processo próprio; resultado em
`reprodutores_v5_etapa3.json` e `logs/`):

| alvo | vermelho antes | verde depois |
|---|---|---|
| `tests/test_moodle.py` (10 novos) | 10 falham, 44 existentes passam (gravado antes de alterar o `src/`) | 54/54 |
| `adquire` v5 (13 novos: metadados pelo corpo real, orçamento com e sem Content-Length, falha de JSON e API, catálogo, triagem sem contagem, anexo `.html`, colisão com `index.html`, 0/2 candidatos, campos ausentes) | 13 falham na v4 | 13/13; pasta 30/30 |
| gerador v5 (8 novos, inclusive colisão) | 8 falham na v4 | 8/8; pasta 109/109 |

- **Validação do produto:** suíte `tests` completa com 2458 passando, 1 falha e 4 pulados. A linha de base antes da
  alteração tinha 2448 passando, a **mesma** falha e 4 pulados. A falha é o teste
  `test_divisao_de_blocos_atual[Fundamentos-de-Redes-Tutor]`, no arquivo `tests/test_caracterizacao_blocos_atual.py`
  (corrigido em 29/09: o texto anterior trocava o nome do arquivo pelo nome do teste). É alheia a esta tarefa e não
  foi corrigida.
- **Regressões sem alteração:** pastas v4 (101, 17, 11, 2), etapa 3 (62, 6, 5) e etapa 2 (45).
- **5 casos anteriores:** continuam corrigidos na v5.
- **Testes herdados alterados** (`diffs/diff_testes_herdados_v4_v5.patch`):
  - fake `Cliente` com `bytes_recebidos`/`limite_bytes`;
  - `index.html` de página com `filesize 0`;
  - asserções de orçamento pelo par (transferidos, aceitos);
  - `test_metadata_outside_budget` da v4 agora espera o impedimento da triagem pré-v5;
  - fixtures de página com o `index.html` real (`501-index.html`).
- **Dependências:** reais (`src`, PyMuPDF). O transporte é falso: `http.client.HTTPResponse` sobre BytesIO e `urlopen`
  substituído. Não houve stub de `src/`.

**Pendências:**

- **R-VIS:** decisão, inclusive a aceitação expressa do risco residual dos pixels, se for o caso.
- **R-CC:** aprovação, com o `gold-externo-2` proposto.
- **R-PAGE:** confirmação do contrato.
- **Grafo local:** atualizar antes do commit (invariante do projeto: código de `src/` mudou; o grafo não é versionado).
- **Gate 2:** revisão e commit, com `src/builder/sources/moodle.py` e `tests/test_moodle.py` modificados e não
  commitados.
- **Aprovação metodológica.**

### 6.1 Catálogo entre execuções e interrupção (continuação do R-META)

Os dois caminhos foram achados pelo revisor **por inspeção de `catalogo()`, sem execução por ele**. Foram reproduzidos
aqui primeiro, com testes vermelhos contra a v5 anterior à correção (`logs/vermelho_catalogo_v5_antes.txt`), e só
depois corrigidos.

**1. Orçamento acumulado não limitava a execução seguinte.**

- **Reprodutor (antes):** o segundo `catalogo()` recebia o teto inteiro e voltava a ler.
  `test_catalogo_repetido_desconta_o_consumo_anterior` falhou com "DID NOT RAISE OrcamentoExcedido".
- **Correção:**
  - `le_consumo_catalogo()` lê o registro persistido **antes de qualquer requisição**, e o `catalogo()` usa como
    limite só o que resta do orçamento comum;
  - `baixar()` passa a usar o registro persistido, e não a triagem, que pode ser anterior a tentativas posteriores;
  - triagem com mais consumo que o registro é inconsistência;
  - registro ausente vira impedimento registrado, com a triagem como limite inferior;
  - registro ilegível ou inconsistente (total diferente da soma, bytes negativos ou não inteiros) levanta
    `RegistroIlegivel` antes de qualquer requisição. **Nunca vira consumo zero.**
- **Testes:**
  - duas execuções, a segunda recusada sem ler além do restante;
  - primeira execução parcialmente consumida e interrompida, e a segunda limitada pelo que sobrou;
  - registro ilegível, com total inconsistente ou com bytes negativos;
  - `baixar()` usando o registro em vez da triagem antiga;
  - `baixar()` com registro ilegível ou menor que a triagem, sem requisição.

**2. Interrupção podia apagar o registro.**

- **Reprodutor (antes):** o `KeyboardInterrupt` durante `site_info` e durante `get_users_courses` virava
  `UnboundLocalError` no `finally` (`erro` não inicializado), e nada era gravado.
- **Correção:** `erro = "interrompido"` antes das chamadas. O `finally` grava os bytes já contados, e a interrupção
  original propaga.
- **Testes:** interrupção em cada uma das duas chamadas, conferindo o registro persistido.

**Resultados:**

| alvo | resultado |
|---|---|
| reprodutores novos (10), antes da correção | 10 falham |
| reprodutores novos (10), depois | 10/10 |
| pasta de aquisição v5 | 40/40 |

- **Produto:** `src/builder/sources/moodle.py` e `tests/test_moodle.py` estão **inalterados** desde a execução registrada
  (sha256 `24430123…` e `99951fdb…`). Por isso a suíte completa não foi repetida.
- **Pacote cego v5:** não mudou.
- **Diffs:** `diffs/diff_adquire_v5_catalogo.patch` (v5 antes → depois), `diffs/diff_test_adquire_v5_catalogo.patch` e
  `diffs/diff_adquire_v4_v5.patch`, regenerado.
- **Resultados:** `reprodutores_v5_catalogo_etapa3.json`.
- **Hashes:** `adquire` v5 depois da correção `f7549835…` (antes `c06a63f5…`); `test_adquire_v5.py` `af6eb563…`.
  A correção isolada tem +37/−9 (numstat). O diff v4→v5 regenerado passa a +98/−18; o §6 registrava +70/−18 antes desta
  correção.

**Grafo local:** atualizado com `graphify update .` (Python de `graphify-out/.graphify_python`), extração de código sem
LLM nem rede: 18138 nós, 39079 arestas, 852 comunidades. Não foram executados:

- o renome de comunidades por LLM (`graphify label`), proibido nesta etapa;
- a extração semântica de documentos.

### 6.2 Pacote para a revisão do delta e proposta de commit (Gate 2 pendente)

**Pacote congelado:**

- `Desktop/para-gpt/revisao_delta_rmeta_rpage_29-09.zip`, montado por
  `c1-3/revisao_delta_rmeta_rpage_29-09/monta_pacote.py` a partir de uma lista explícita.
- O manifesto `manifesto_pacote_revisao_delta.json` tem o sha256 de cada arquivo incluído e identifica por caminho e
  hash:
  - os baselines: v4, o HEAD `bf46d51f` dos dois arquivos do produto e o executor v4;
  - as dependências: manifesto de aquisição, enumerador, candidatos, instruções do adjudicador e extração de rótulos
    do `src`;
  - os ZIPs anteriores, preservados.
- Documentos: só versões sem texto excedente. A conferência dos excedentes é feita pelo script, que os lê do catálogo
  sem gravá-los. O JUnit fica fora.
- O sha256 do próprio ZIP não cabe dentro dele. Está registrado no tracker, no estado local e no fechamento.

**Escopo da revisão** (`ESCOPO_REVISAO.md`):

- contagem e limite dos corpos HTTP e compatibilidade sem limite;
- persistência do consumo entre chamadas e execuções, com falha e interrupção;
- R-PAGE provisória e os casos não cobertos;
- correspondência entre código, testes e evidências.

A auditoria anterior está encerrada.

**Commit técnico proposto:** somente estes dois arquivos (Gate 2 não autorizado; nada em staging):

| arquivo | sha256 | blob git |
|---|---|---|
| `src/builder/sources/moodle.py` | `244301234d671b4ebb990499c96d4f2a6257348d614abcc15ee3e987c12b319b` | `e930b640` |
| `tests/test_moodle.py` | `99951fdbdc2a2618c3a164ada26e70111a5486e02e00d14e0731f4fcc4be5716` | `40146bb7` |

Os baselines no HEAD são os blobs `67cf1302` e `f5f479d5`.

`docs/reports/pendencias.md` também está modificado: havia alteração anterior a esta tarefa, e esta tarefa acrescentou
entradas. Ele fica **fora** do commit proposto. Incluí-lo exige justificativa própria antes do Gate 2.

**Grafo local:** atualizado depois da última mudança de código (`graphify update .`, sem LLM): `graph.json` de 29/09
18:48, 18138 nós. Ele continua atual, porque o `src/` não mudou desde então. Não é versionado.

**Revisão independente pendente (workflow, `references/review.md`):**

- O delta altera código do produto, e "código relevante exige revisão independente". Pelo contrato, essa revisão é
  do Astra: somente leitura, com brief autocontido, diff fixado e timeout de 10 minutos.
- A tentativa automática desta tarefa já foi consumida: foi o parecer independente da etapa 3, com
  `escaladas_automaticas = 1`, preservado.
- Pelo contrato, nova revisão LLM **exige autorização explícita**. A conferência local deste relatório **não é
  revisão independente**.
- Pendentes: essa revisão do delta, a decisão do Gate 2 sobre o commit dos dois arquivos e, separada, a aprovação
  metodológica. R-VIS não foi aprovada, e o pacote não está liberado para uso real. R-CC/`gold-externo-2` e R-PAGE
  continuam proposta e provisória.
