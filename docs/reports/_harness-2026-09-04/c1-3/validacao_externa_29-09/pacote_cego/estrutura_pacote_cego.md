# Estrutura do pacote cego (`pacote-cego-1`) e allowlist

**Pacotes cegos REAIS: nenhum gerado.** A regra de seleção não propôs nenhum curso (`../populacao/regra_selecao.md`).
Ver `manifesto_pacotes_reais.json`. A estrutura abaixo vem do exemplo sintético `exemplo_sintetico/` (fonte com
armadilhas + pacote gerado + auditoria aprovada), montado pela mesma função que montaria os pacotes reais.

## Arquivos do pacote (allowlist positiva)

| arquivo | origem | conteúdo |
|---|---|---|
| `materiais/<material_id>__<nome>` | bruto (cópia byte a byte) | arquivo publicado no Moodle ou página HTML do Moodle |
| `plano/<nome original>` | bruto | plano de ensino original |
| `plano/plano_texto.<ext>` | bruto (conversão declarada na fonte) | texto do plano usado para os rótulos |
| `materiais.json` | derivado (`descobre`) | um registro por material: `material_id`, `tipo` (`arquivo`, `pagina`, `link_externo`, `arquivo_sem_fonte_local`), `adjudicavel`, `arquivo`, `nome_original`, `ocorrencias` (`secao`, `modulo`, `modname`), `sha256`, `tamanho`, `url` |
| `moodle_estrutura.json` | derivado do `contents.json` da API | `formato`, `secoes` (`numero`, `nome`, `resumo` em texto), `rotulos` (`secao`, `texto`), `modulos` (`secao`, `nome`, `modname`) |
| `rotulos.json` | derivado do texto do plano | `unidades` (`id`, `slug`, `titulo`), `topicos` (`id`, `unidade`, `slug`, `rotulo`, `codigo`); sem aliases |
| `gold_modelo.csv` | derivado | cabeçalho do schema + uma linha por material adjudicável |
| `INSTRUCOES.md` | documento do protocolo | cópia de `gold/instrucoes_adjudicador.md` |
| `declaracao_cegamento.md` | derivado das instruções | modelo da declaração |
| `pacote_manifesto.json` | derivado | sha256 e procedência de cada arquivo, sha256 do gerador e das instruções |

Qualquer outro arquivo, pasta ou chave JSON reprova a auditoria.

## O que nunca entra (leitor restrito + auditoria negativa)

- **Arquivos gerados pelo produto ou saídas do motor:** manifest, `.content_taxonomy.json`, `.timeline_index.json`,
  `.card_block_map.json`, `.lessons_index.json`, sidecars `.glossary_curation*.json`, `links.json`, `manual-review/`,
  `raw/moodle/labels.json` e `sections.json`, `raw/site/`, `stash/.moodle_nomes.json`, `_ARQUIVOS_DO_CARD.txt`,
  arquivos de `code/material/references_curation`, `FILE_MAP*`, `COURSE_MAP.md`, `GLOSSARY.md`, capturas, placares e
  avaliações.
- **Pastas:** `manual-review`, `.frzero`, `site`, `course`, `build`, `content`, `staging` e qualquer componente de
  caminho `*-Tutor` ou `GPT-Tutor-Generator*`.
- **Campos da API fora da allowlist:** autor, id de usuário, licença, datas de criação e afins.
- **Padrões de predição** em qualquer arquivo gerado: `computed_block/unit/subunit`, `temporal_block_id`,
  `unit_match`, `subunit_match`, `match_confidence`, `winner_score`, `assignment_run`, `auto_tags`,
  `glossary_curation`, `propagado-headings`, `secao-nomeia-subtopico`, `bloco-NN`. Nomes genéricos (score, confidence,
  reasons, captura, placar) são barrados como nome de campo pela allowlist de chaves; como texto do professor podem
  aparecer ("captura de pacotes").

## Por que só procurar nomes de campo não basta (e o que o auditor faz)

Uma predição pode ser copiada com outro nome ou dentro de um campo permitido. Por isso a auditoria regenera o pacote
inteiro a partir da MESMA fonte, numa pasta temporária, e exige bytes idênticos em todos os arquivos. Qualquer valor
que não venha da fonte bruta pela função declarada aparece como diferença. Os testes provam isso com uma "seção"
adulterada num campo permitido (`test_auditoria_pega_predicao_renomeada_em_campo_permitido`).

## Testes do cegamento (`test_pacote_cego.py`, 12)

Geração e auditoria limpas; conteúdo só de fonte permitida (nenhum campo do produto, autor ou usuário); rótulos só do
plano e sem alias; determinismo; leitor recusa saídas do motor, gerados do produto e caminhos fora das raízes; trava
de repositório por componente do caminho; auditoria pega chave proibida injetada, predição renomeada em campo
permitido, padrão de motor em valor, arquivo extra e bruto adulterado; plano sem unidades recusado; destino existente
recusado; formato de pastas sem API.
