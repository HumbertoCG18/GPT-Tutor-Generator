# Sistema do gabarito: cards-pasta como fonte autoritativa de file→bloco

> Design doc. Aprovado em 2026-06-07.

## Goal

Resolver na raiz a atribuição file→bloco (hoje ~62,5% via matching lexical) usando
a **estrutura de cards do Moodle** que o professor já criou, materializada como
**pastas** no stash da cadeira. O card de cada arquivo é o sinal **autoritativo**:
torna a atribuição **determinística**, gera o **gabarito automático** (zero
rotulação manual, em qualquer cadeira) e **escala incrementalmente** (arquivo novo
no card → herda o destino).

## Contexto / decisões

- **Stash folder por cadeira** já existe (`SubjectProfile.stash_folder`, definido no
  Gerenciador de Matérias).
- **Convenção de pastas:** `<stash>/<nome do card>/<arquivos>`. O **código (.zip)
  fica DENTRO do card** a que pertence (ex.: `stash/Verificação de Programas/hoare.zip`)
  — resolve de raiz o "código-sem-unidade".
- **card → bloco:** **auto por nome/data** (nome do card casa com unidade/tópico do
  plano; "Semana N"/datas → bloco por data) **+ confirmação única por cadeira** numa
  telinha pros cards não-casados (poucos itens), persistida.
- Investigação confirmou: o gabarito **deve** vir de fonte fora da lógica de
  atribuição (senão é circular). O card (feito pelo professor) é essa fonte. Sinais
  alternativos ("Aula N", datas no nome) existem em alguns cursos mas variam por
  professor; o card é o universal.
- **Parado pra depois (anotado):** dessincronização timeline-index × manifest
  (rebuild do índice não re-roda file→bloco) — corrigir num esforço próprio.

## Arquitetura

```
stash/<card>/arquivos  ──(import ciente de pasta)──>  entry.source_section = <card>
                                                            │
teaching_plan/timeline ──(resolve_card_to_block: nome/data)──> card→bloco(s) (auto)
                                                            │  não-casados
                                                            ▼  ──> confirmação única (UI) ──> .card_block_map.json
entry.source_section + card_block_map ──> atribuição DETERMINÍSTICA (override do lexical)
                                       └─> gabarito automático = card_block_map (mede sem rótulo)
```

Princípio: `source_section` (o card) é autoritativo. Quando presente e mapeado,
**vence o scorer lexical**. Override manual de bloco/unidade continua acima de tudo.

---

## Componentes

### 1. `FileEntry.source_section: str = ""`
Novo campo: o card/seção de origem do arquivo. Serializado (to_dict/from_dict
retrocompatível, como os demais). Espelha o padrão dos campos existentes.

### 2. Import ciente de pasta-card (do stash)
- Nova ação "📥 Importar do stash" (no fluxo de importação).
- Lê `subject.stash_folder`; para cada **subpasta imediata** (= card), importa seus
  arquivos com `source_section = <nome da subpasta>`.
- **Categoria** inferida por arquivo (heurística atual estendida): `.zip` →
  `codigo-professor`; nome com "exerc"/"lista" → `listas`; "respostas"/"gabarito" →
  `gabaritos`; "trabalho"/"t1"/"t2" → `trabalhos`; senão `material-de-aula`. (O card
  dá a SEÇÃO/tópico; a categoria dá o TIPO — independentes.)
- Arquivos soltos na raiz do stash (sem subpasta) → `source_section=""` (caem no
  caminho lexical atual; sem regressão).
- Idempotente: re-importar atualiza `source_section` por `source_path` (não duplica).

### 3. `resolve_card_to_block(card_name, subject, timeline) -> (block_ids, confidence, reason)`
Função pura. Resolve um card a um ou mais blocos:
1. **Nome → unidade/tópico:** normaliza e casa o nome do card com os títulos de
   unidade/tópico do `content_taxonomy`/plano (overlap de tokens, reuso de
   `norm_ascii_lower`). Match forte → os blocos daquela unidade.
2. **Semana/data:** se o nome contém "Semana N" ou uma data (DD/MM) → mapeia ao(s)
   bloco(s) cujo período cobre essa semana/data.
3. Sem match confiável → `([], 0.0, "needs-confirmation")`.

### 4. Mapa card→bloco por cadeira (persistido) + confirmação única
- Arquivo `course/.card_block_map.json`: `{card_name: {block_ids: [...], source: "auto"|"manual"}}`.
- Telinha (UI) "Mapear cards" por cadeira: lista os cards (de `source_section` dos
  entries), mostra a sugestão `auto`, e deixa confirmar/corrigir os `needs-confirmation`.
  Persiste no `.card_block_map.json`. Manual vence auto.
- Poucos cards por cadeira → 1 passo rápido, uma vez (re-confirma só quando surge
  card novo).

### 5. Atribuição determinística (em `resolve_unit_block_tags`)
- Ordem: `manual_timeline_block_id` (override) > **card→bloco** (`source_section` +
  card_block_map) > scorer lexical atual (fallback).
- Quando o card mapeia a **vários blocos** (card largo, ex.: "Verificação de
  Programas" = b10–b15): usar o scorer atual **restrito a esses blocos** pra escolher
  o sub-bloco (date/sequência/lexical dentro do card) — o card barra o cross-card.
- `computed_unit_slug` derivado do bloco escolhido (consistente).
- `source_section` persistido no entry; band reflete a fonte (card → alta).

### 6. Gabarito automático + medição
- O `card_block_map` + `source_section` = a verdade. Script de medição
  (estende `eval_ground_truth` ou novo) compara `computed_block_id` ao(s) bloco(s)
  do card de cada arquivo → acurácia **sem rótulo manual**, em qualquer cadeira.
- Métrica: % de arquivos no bloco do seu card (e cross-card = erro).

---

## Decomposição (2 planos)

- **Plano 1 — captura do card:** `FileEntry.source_section` + import ciente de
  pasta-card (walk do stash, inferência de categoria, persistência). Entrega: cada
  arquivo carrega seu card. Testável sozinho (importa árvore → entries com section).
- **Plano 2 — uso + medição:** `resolve_card_to_block` + `.card_block_map.json` +
  telinha de confirmação + wiring na atribuição (card vence lexical, sub-bloco
  restrito) + medição automática. Re-medir contra a baseline 62,5%/11-confident-wrong
  do Métodos.

## Testing

- `source_section` round-trip no FileEntry; import de uma árvore-fixture
  (`card/a.pdf`, `card/b.zip`) → entries com `source_section` + categoria correta.
- `resolve_card_to_block`: nome casa unidade; "Semana 3" → bloco por data; sem match
  → needs-confirmation.
- Atribuição: entry com card mapeado a 1 bloco → esse bloco (override do lexical);
  card a vários → sub-bloco via scorer restrito; sem card → lexical (sem regressão).
- Medição: rodar no Métodos (após organizar o stash em cards) e exigir
  acurácia **> 62,5%** e confident-wrong **< 11** vs a baseline.

## Fora de escopo

- Scraper Moodle (preencher as pastas automaticamente) — futuro; o card-pasta é
  manual/semi-auto por ora.
- Correção do desync timeline×manifest (anotado, esforço próprio).
- Refator visual do tab Cronograma (vem depois, com a atribuição já confiável).

## Riscos

- Cards muito largos (ex.: "Verificação de Programas") ainda precisam do scorer
  intra-card pro sub-bloco — mas restrito ao card (cross-card eliminado).
- Nome do card que não casa com o plano → cai na confirmação manual (poucos).
- Stash desorganizado (arquivos soltos) → fallback lexical (sem regressão, sinalizado).
