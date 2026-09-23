# Medição de correção com ground-truth — Design

last_updated: 2026-06-05

## Contexto

A band (`computed_block_band`: alta/media/baixa) mede **confiança**, não
**correção verificada** — "alta" pode estar confiante e errado. O harness
existente (`scripts/eval_assignments.py`) roda o scorer real contra um gold set
**sintético** com `unit_guess` stubado e já reporta `confident_wrong`. Falta
medir correção **de fato** contra um repo real rotulado por verdade de domínio.

Item de backlog: "Medição de correção com ground-truth".

## Objetivo

Construir tooling que, dado um repo gerado real + rótulos de verdade fornecidos
pelo usuário, meça a correção real da atribuição file→bloco temporal (acurácia,
confusão, confiante-e-errado, calibração por band). Decisões aprovadas:
**tooling + usuário rotula**; eixo **bloco temporal**; rótulos em **CSV**.

A rotulação é assistida: após o usuário apontar um repo real, o agente lê o
conteúdo curado de cada material + os blocos da timeline e propõe `true_block_id`
(o usuário confirma/corrige). Por isso o CSV inclui `markdown_path`.

## Fontes de dados (sem re-rodar o scorer)

- **Predições:** `<repo_root>/manifest.json` → `entries[*]` com `id`,
  `computed_block_id`, `computed_block_band`, `computed_block_confidence`,
  `title`, `category`, e `markdown_path`/`base_markdown` (caminho do conteúdo
  curado). `FileEntry.to_dict()` **omite defaults** → ler sempre com `.get(k, "")`.
- **Bloco→período:** `<repo_root>/course/.timeline_index.json` →
  `{block["id"]: block["period_label"]}` sobre `blocks`.

Tudo legível de arquivos persistidos; nenhuma re-execução do pipeline.

## Componentes

### `scripts/eval_ground_truth.py` (lógica pura + CLI)

Funções puras (testáveis, mirror de `eval_assignments.py`):
- `load_predictions(repo_root: Path) -> dict[str, dict]`: `{entry_id: {block_id, band, confidence, title, category, markdown_path}}` a partir do manifest.
- `load_block_period_map(repo_root: Path) -> dict[str, str]`: `{block_id: period_label}` do `.timeline_index.json`.
- `load_labels_csv(path: Path) -> dict[str, str]`: `{entry_id: true_block_id}` (ignora linhas com `true_block_id` vazio).
- `evaluate_ground_truth(predictions, labels, block_map) -> dict`: relatório.
- `format_report(report, block_map) -> str` + `main(argv)` (`--json` para dump).

Relatório (`evaluate_ground_truth`):
- `total` (materiais rotulados — só os presentes em ambos predictions e labels),
- `correct`, `wrong`, `block_accuracy`,
- `orphans` (previu `""`), `missed` (verdade definida mas previu `""`),
- `confident_wrong` (band alta + bloco errado) — métrica-chave,
- `bands` (calibração correto/errado por band, incl. `""`),
- `confusion` (`"{true}->{pred|(orfao)}": count`),
- `cases` (linhas por material: id, true, predicted, band, correct).

### `scripts/make_ground_truth_template.py` (gera esqueleto)

- `build_template_rows(repo_root: Path) -> list[dict]`: uma linha por entry do
  manifest, reusando `load_predictions`/`load_block_period_map` de
  `eval_ground_truth` (DRY).
- `write_template_csv(rows, out_path)`: colunas
  `id, title, category, markdown_path, predicted_block_id, predicted_period, predicted_band, true_block_id`.
  `true_block_id` **pré-preenchido com `predicted_block_id`** (usuário confirma/corrige).
- `main(argv)`: `<repo_root> <out_csv>`; imprime no stdout a referência de blocos
  válidos (`id → period_label`) para facilitar a rotulação.

## Testes

`tests/test_eval_ground_truth.py` (mirror de `test_eval_assignments.py`):
- Fixture: cria repo temporário (`tmp_path/manifest.json` + `tmp_path/course/.timeline_index.json`) com 3-4 entries (1 correto, 1 confiante-e-errado, 1 órfão) + CSV de rótulos.
- `load_predictions` lê id/block/band com defaults ausentes (entry sem `computed_block_band`).
- `load_block_period_map` mapeia id→period.
- `evaluate_ground_truth`: acurácia, `confident_wrong`, `orphans`/`missed`, soma de bands == total, confusão.
- `build_template_rows`: `true_block_id` == `predicted_block_id`; uma linha por entry; colunas presentes.
- CLI smoke (`main`) opcional via `--json`.

## Fluxo de uso (após a entrega)

1. Usuário aponta um repo real (ex.: IA).
2. `python scripts/make_ground_truth_template.py <repo> labels.csv` → esqueleto.
3. Agente lê `markdown_path` de cada material + blocos da timeline, propõe
   `true_block_id`; usuário confirma/corrige.
4. `python scripts/eval_ground_truth.py <repo> labels.csv` → relatório.
5. Veredito: se `confident_wrong` e a acurácia real forem ruins, vale investir em
   precisão (reabrir #3 decay / #4 band); se já bons, encerrar a frente.

## Fora de escopo

- Os rótulos reais (verdade de domínio) — fornecidos pelo usuário, assistidos
  pelo agente, fora deste código.
- Eixo unidade e mudanças no scorer — só medição do estado atual file→bloco.
