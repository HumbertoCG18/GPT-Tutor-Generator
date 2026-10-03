# Validação externa do regime VOCAB, etapa 3: fechamento do alvo e correções de integridade (29/09/2026)

**Resultado:**

- as seis correções técnicas foram feitas e testadas (73/73);
- os 5 casos da revisão se reproduzem na v2 e não na v3;
- a conferência física local fecha sem divergência;
- há uma proposta normativa única de população, não aplicada;
- a verificação local de exposição não achou falhas de busca, e nenhum nível foi alterado.

Sem rede, gold, build, replay, LLM ou motor. Não é o Gate 1. **Parada para aprovação** das decisões metodológicas
(§5) e do pacote cego corrigido (§2).

## 1. Preservação

- O ZIP, o inventário, as fontes, os manifestos e os resultados da etapa 2 estão intactos: os 26 arquivos de
  `manifesto_etapa2.json` e os 61 de `manifesto_preparacao.json` (29/09) conferem por sha256. Os testes da etapa 2
  passam 45/45, sem alteração.
- Nenhum candidato reclassificado. A regra v2 e o seu resultado vazio não mudaram (`registro/nota_registro_29-09.md`).
- Os originais do catálogo e da triagem não foram tocados; as cópias redigidas são separadas (§6).
- Sem reset, clean, stash, `git add`, commit, push, PR ou merge. Os 4 stashes e os arquivos de outras sessões
  (`astra_revisao_regime2_17-09.md`, `diagnostico_subunidade_17-09.*`) estão intactos.
- Não alterados: `src/`, compilador, prompt, aliases, pontuação, 2ª passada, métricas históricas, exceção do gitleaks.

## 2. Correções técnicas (`correcoes/`)

Nas duas ferramentas, a v3 é uma cópia nova; a v2 da etapa 2 continua como foi executada.

| defeito demonstrado | correção | prova |
|---|---|---|
| plano com predição era copiado (auditoria vazia) | o arquivo e o texto do plano passam por `verifica_material`. Recusa = pacote não gerado (`PlanoRecusado`), destino não criado. A auditoria também verifica `plano/` | 4 testes |
| ZIP válido copiado sem examinar os membros | política explícita de membros (abaixo) | 21 testes |
| candidato único em outra seção era ligado | proveniência primeiro (abaixo) | 8 testes + 1 herdado reapontado |
| anexo de página fora da raiz: `ValueError`, inventário perdido | registro com `base` (`curso` ou `anexos_de_pagina`) + `caminho` relativo a ela; o congelamento cobre as duas árvores | 1 teste + congelamento |
| limite confiado ao `filesize` (7 bytes aceitos com limite 5) | leitura cortada em `min(limite por arquivo, orçamento restante) + 1` byte; `acima_do_limite_real` e `nao_baixado_orcamento_real`; a verificação pelo declarado continua | 2 testes |
| falha posterior apagava os registros já processados | exceção por arquivo vira `falha_local:<Tipo>` e o curso segue. Os registros vão para a lista do chamador na hora. O inventário é gravado a cada curso e no `finally` (`concluido: false` se interrompido), e `congelar` recusa inventário parcial | 3 testes |

**Política de membros de contêiner (pacote cego v3).**

- **ZIP simples:** cada membro passa pela mesma `verifica_material` do arquivo solto: allowlist, assinatura, varredura
  de texto e contêiner aninhado.
- **docx/pptx/xlsx/odt/odp/ods:**
  - XML e texto são varridos sem as tags, porque o texto vem quebrado em runs;
  - PDF, imagem e contêiner embutidos passam por `verifica_material`;
  - objeto OLE (`.bin`, salvo `printerSettings`), macro (`vbaProject.bin`, `*m`) e executável são recusados;
  - fontes, EMF/WMF e `mimetype` passam sem varredura.
- **Todos os contêineres:** o material é recusado quando tem caminho absoluto ou `..`, membro cifrado, nome de
  configuração ou credencial, mais de 5000 membros, mais de 500 MB descompactados, razão acima de 200× ou mais de
  2 níveis de aninhamento.
- **PDF:** `/EmbeddedFile` = recusa.
- Recusa é registrada com o motivo e o arquivo não é copiado. Nenhum material é liberado para atingir mínimo.

**Ligação Moodle → arquivo (pacote cego v3).**

- **Com `inventario` + `curso_id` na fonte:** cada item vem do registro da aquisição por (módulo, arquivo, `filepath`
  quando houver). O caminho é conferido na fonte e o sha256 contra o inventário. Divergência, registro ausente ou
  inventário parcial param a geração (`DivergenciaProveniencia`). Item não adquirido vira `arquivo_nao_adquirido`
  (visível, não adjudicável, com o status da aquisição).
- **Sem inventário:** nome + tamanho só ligam dentro da pasta da seção do módulo. Candidato só em outra seção vira
  `origem_nao_confirmada`, e o arquivo local continua como material sem módulo, na seção da sua pasta.
- **Em ambos:** o método de ligação de cada fonte fica no manifesto (`ligacao`), e anexos de página são registrados
  (`anexo_de_pagina`), não entregues.

**Reprodutor** (`correcoes/reproduz_casos_revisao.py` → `reprodutores_v2_v3.json`): os 5 casos da revisão contra a v2
e a v3, com fixtures sintéticas e rede falsa.

| caso | v2 | v3 |
|---|---|---|
| plano com predição | copiado, auditoria vazia | `PlanoRecusado` |
| ZIP com membro proibido | adjudicável, bytes copiados | `recusado`, bytes fora |
| único candidato em outra seção | ligado a `stash/Secao A/slides.pdf` | `(None, "origem_nao_confirmada")` |
| anexo de página fora da raiz | `ValueError`, sem inventário | registros com `base`/`caminho` válidos |
| limite pelo `filesize` | `ok`, 7 bytes contados | `acima_do_limite_real`, 0 bytes |

**Testes:** pacote cego 62 (arquivos herdados: 12 + 17, dos quais 1 novo; arquivo novo: 33); `adquire` 6; exposição 5. Total 73/73. Os logs estão em
`log_testes_etapa3.txt`.

**Diffs:**

- `diff_gerador_v2_v3.patch` (+230/−50);
- `diff_adquire_v2_v3.patch` (+134/−86);
- `diff_testes_herdados_v2_v3.patch` (+14/−2), com três mudanças nos testes herdados, todas por mudança pedida:
  1. o fixture passa a ter a cópia de `aula1.pdf` na pasta da própria seção, que é como os dois downloaders gravam.
     Sem isso, o módulo 405 era exatamente o caso "candidato em outra seção";
  2. o caso ambíguo passa a usar bytes diferentes na mesma pasta de seção, e o caso antigo (pastas que não são
     seções) virou teste de não ligação;
  3. um `docx` falso (`PK\x03\x04ok`) agora é recusado como ilegível.

O `adquire` v3 lê manifesto, enumerador e candidatos da etapa 2 só para ser importável. O `__main__` recusa rodar,
porque uma nova aquisição exige manifesto novo e Gate de rede. Não foi construída sandbox universal.

## 3. Conferência física local (`conferencia/`)

`conferencia_fontes.md`: os bytes das 275 fontes conferem com a árvore congelada e com o inventário, e os 461 itens da
API têm um registro com status cada. Há 5 páginas (`index.html` ok) e nenhum anexo. As 23 falhas estão num curso, e
não há duplicata entre cursos. Os números de falhas, duplicatas (9 pares), colisões (4) e formatos fora do recorte
(49 arquivos em 3 cursos) foram só listados, sem nenhuma alteração. Nenhum hash esperado foi recalculado.

## 4. Bloco e exposição (`exposicao/`)

- **Bloco:** a proposta (§10) separa **estabilidade de bloco entre braços** (o que esta validação mede) de
  **acurácia de bloco** (só com gold temporal independente, fora desta validação).
- **Exposição:** `verifica_exposicao.py` faz git grep/log no commit `bf46d51f` e lê os nomes das pastas de download.
  Registra padrão, termo, vizinhança de 3 caracteres, arquivo, linha, categoria do arquivo e trecho, omitindo o trecho
  de resultado do motor ou segredo. Não lê nem escreve níveis, e busca que falha dá INDETERMINADO. Em 21 candidatos,
  todos com busca ok:
  - 11 sem nenhuma ocorrência;
  - 10 com ocorrências descritas em `resumo_exposicao.md`: id dentro de sha256, título de livro, fixture de parser,
    prefixo de outro curso;
  - em Engenharia de Software I, todas as 221 ocorrências são "Engenharia de Software II".

  Nenhum N1 virou N0.

## 5. Proposta normativa única (`proposta_normativa_populacao.md`)

Ela resolve estes pontos:

- alvo documental;
- universo fixado pela listagem da API antes do download;
- unidade = bytes únicos por curso, fixada antes do build;
- duplicatas: uma linha por unidade na fonte e consistência no build;
- cobertura com falhas e recusas no denominador;
- links fora do alvo e das conclusões;
- mínimos totais inalterados e por curso = 10 pós-gold (abaixo, o curso fica descritivo);
- mínimos não atingidos: sem veredicto e nova aquisição sob Gate;
- alcance das conclusões.

**Mudanças informadas por contagens estão marcadas [C] e tabeladas no §13**, e a mais sensível é tirar os links do
alvo (os links reprovam E4 em 7 de 8 cursos). A proposta não foi aplicada e o efeito no lote não foi calculado. Nenhum
limiar mudou, o E4 continua em 90% e não se pesquisou nenhuma grade.

## 6. Registro (`registro/`)

`nota_registro_29-09.md` traz os quatro pontos pedidos:

- a correspondência parcial estendeu o manifesto;
- ES I não foi demonstrada equivalente a ES2;
- há texto excedente, inclusive nomes de professores, no campo de nome de 2 cursos;
- o resultado vazio pertence à regra v2.

As cópias redigidas `catalogo_divulgacao.json`, `triagem_divulgacao.json` e `../exposicao/exposicao_local_divulgacao.json`
saem de `redige_divulgacao.py`, que confere que os originais não mudam. O original `exposicao_local.json` fica só
local, fora do ZIP.

## 7. Limitações

- **PDF:** a busca de `/EmbeddedFile` é por bytes e um objeto em stream comprimido não é visto. O texto do PDF não é
  varrido, como já era na v2.
- **ZIP:** segue a allowlist do arquivo solto. Código `.go/.hs/.asm`, `Makefile`, `__MACOSX` e `Thumbs.db` recusam o
  ZIP inteiro. É recusa registrada, a favor da segurança, e reduz cobertura.
- **Documentos:** membros binários não listados (fontes, EMF/WMF) passam sem exame. A varredura procura só as
  assinaturas de motor e de segredo.
- **Inventário da aquisição:** é lido fora do `Leitor`, como documento do protocolo. A integridade dele depende do
  congelamento da etapa 2, e o sha256 fica em `fontes_lidas`.
- **Anexos de página:** são registrados e não entregues (0 no lote).
- **`adquire` v3:** exercitado só com cliente e `urlopen` falsos; nunca rodou contra o servidor.
- **Exposição:** só um commit e nomes de pastas (D9 aberto). A categoria é do arquivo, não da menção.
- **Proposta:** escrita por quem conhece as contagens (§0 da proposta).

## 8. Estado do worktree

Sem commit. A pasta `validacao_externa_etapa3_29-09/` é nova e não versionada. O tracker e o estado local são
atualizados depois do congelamento desta entrega. O `pendencias.md` já estava modificado antes desta etapa. Os 4
stashes e os arquivos de outras sessões estão intactos.

## 9. Próximo passo (depende de aprovação)

1. Aprovar ou recusar a proposta P3, sabendo das contagens.
2. Aprovar o pacote cego v3 e a política de contêineres.
3. Só então: aplicar P3 uma vez ao lote congelado (sem rede) e, se houver população, gerar os pacotes reais sob
   Gate próprio.
