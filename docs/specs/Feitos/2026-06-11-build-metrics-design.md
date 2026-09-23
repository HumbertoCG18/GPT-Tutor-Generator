# Métricas de build no BUILD_REPORT — Design

date: 2026-06-11
roadmap: #5 (agregar custos / qualidade no BUILD_REPORT)
status: aprovado para plano

## Objetivo

Dar visibilidade por build de **custo** (via proxy real), **carga de OCR** e
**qualidade de extração**, gravando uma seção nova no `BUILD_REPORT.md`. O
desenho prioriza modularidade: adicionar métrica nova depois não deve exigir
refatorar o gerador do relatório nem os collectors existentes.

## Decisão de escopo (e o que foi descartado de propósito)

Análise da evidência durante o brainstorm:

- **`cost_breakdown` da API Datalab é vapor hoje.** Sidecar real de teste traz
  `"cost_breakdown": {}`. O único valor não-vazio nos testes (`{"total_cents": 2}`)
  é uma chave inventada pelo autor do teste. No código, `cost_breakdown` só é
  repassado cego de `last_payload.get("cost_breakdown")`. **Não somamos o dict
  agora** — renderizaria sempre vazio.
- **Datalab cobra por página.** Logo o proxy de custo real é
  **páginas processadas via Datalab**, disponível no sidecar
  (`selected_pages_count` / `page_count`). É essa a métrica de custo de hoje.
- **Contagem de imagens rejeitadas por ruído não é rastreada** e exigiria
  instrumentar o pipeline de extração para uma métrica de baixo valor. **Fora
  do escopo desta entrega** — vira slot futuro que o desenho já comporta.

Métricas populadas hoje (todas com dado real):
1. Páginas processadas via Datalab (proxy de custo) + nº de entries via Datalab.
2. `parse_quality` médio do Datalab.
3. % de PDFs escaneados (por contagem e por páginas).

## Arquitetura

Módulo puro novo: `src/builder/artifacts/build_metrics.py`. Sem I/O de
escrita; só lê manifest (em memória) e sidecars Datalab (somente leitura). O
gerador `write_build_report` (`src/builder/artifacts/repo.py:441`) chama
`collect_build_metrics` + `render_build_metrics_md` e anexa as linhas ao
relatório — `write_build_report` continua fino.

```
src/builder/artifacts/build_metrics.py
  collect_scan_stats(entries)          -> ScanStats          # manifest-only, 0 I/O
  collect_datalab_metrics(entries, root_dir) -> DatalabMetrics  # lê cada sidecar 1x
  collect_build_metrics(manifest, root_dir)  -> BuildMetrics     # orquestra
  render_build_metrics_md(metrics)     -> list[str]          # markdown
```

### Princípio de extensão

- Métrica nova = novo `collect_*` + nova entrada em `collect_build_metrics` +
  um bloco em `render_build_metrics_md`. **Não toca collectors existentes nem
  `write_build_report`.**
- Quando/se Datalab passar a devolver custo real: `collect_datalab_metrics` já
  abre o sidecar — adiciona-se a leitura de `cost_breakdown` (somando com
  `merge_numeric_dicts`, já existente em `text/markdown_utils`) dentro do mesmo
  collector. Sem mudança estrutural.
- Imagens rejeitadas: instrumenta o pipeline depois e adiciona
  `collect_image_stats(entries)` como plugin.

## Estruturas de dados

Dataclasses simples (frozen) em `build_metrics.py`:

```python
@dataclass(frozen=True)
class ScanStats:
    pdf_total: int           # entries com file_type == "pdf"
    scanned_count: int       # subset com document_report.suspected_scan True
    total_pages: int         # soma de document_report.page_count dos pdfs
    scanned_pages: int       # idem, só dos escaneados

@dataclass(frozen=True)
class DatalabMetrics:
    entry_count: int             # entries processados via Datalab
    processed_pages: int         # soma de páginas processadas (proxy de custo)
    avg_parse_quality: Optional[float]   # média dos parse_quality_score (None se nenhum)

@dataclass(frozen=True)
class BuildMetrics:
    scan: ScanStats
    datalab: DatalabMetrics
```

## Fontes de dado (caminhos exatos verificados)

- PDF entry: `entry["file_type"] == "pdf"`.
- Escaneado: `entry["document_report"]["suspected_scan"]` (bool).
- Páginas do PDF: `entry["document_report"]["page_count"]` (int).
- Entry via Datalab: `entry.get("advanced_backend") == "datalab"` **e**
  `entry.get("advanced_metadata_path")` presente.
- Sidecar Datalab: `root_dir / entry["advanced_metadata_path"]` → JSON com
  `selected_pages_count` (fallback `page_count`) e `parse_quality_score`
  (pode ser `None`).

`document_report` pode faltar (entries não-PDF, ou PDF que falhou profiling):
collectors usam `.get(...)` com default e ignoram entries sem o campo.

## Fluxo

1. `write_build_report` monta o relatório como hoje (metadados + regras).
2. Chama `metrics = collect_build_metrics(manifest, root_dir)`.
3. `collect_build_metrics` chama `collect_scan_stats(entries)` e
   `collect_datalab_metrics(entries, root_dir)`.
4. `report.extend(render_build_metrics_md(metrics))`.
5. Grava o arquivo (inalterado).

## Tratamento de erro

- Sidecar ausente, JSON inválido, ou chave faltando → `collect_datalab_metrics`
  pula **aquele** entry (try/except por arquivo) e segue. Build nunca quebra
  por métrica.
- Sem entries Datalab → `DatalabMetrics(0, 0, None)`; render mostra "—".
- Sem PDFs → `ScanStats` zerado; render mostra "0 PDFs".
- Divisão por zero em % → guarda `if total else 0`.

## Saída no BUILD_REPORT.md

Seção anexada após "## Regras práticas de curadoria":

```
## Custos e qualidade do build
- páginas processadas via Datalab: 42 (em 3 arquivo(s)) — proxy de custo (Datalab bilha por página)
- parse_quality médio (Datalab): 0.91
- PDFs escaneados: 2 de 7 (29%) · 80 de 350 páginas
```

Quando não há dado: "páginas processadas via Datalab: — (nenhum arquivo via Datalab)".
Sem tabela por arquivo nesta entrega (a versão por-entry foi reavaliada como
desnecessária frente ao proxy agregado; slot futuro se preciso).

## Testes

`tests/test_build_metrics.py`:
- `collect_scan_stats`: manifest fake com pdfs escaneados/não, e não-PDFs
  ignorados; checa contagens e páginas.
- `collect_datalab_metrics`: cria sidecars JSON em tmp_path; checa soma de
  páginas, contagem de entries, média de parse_quality (e None quando ausente).
- erro: sidecar com JSON inválido / arquivo ausente → entry pulado, sem exceção.
- `render_build_metrics_md`: render com dados e render vazio (placeholders "—").

Teste de integração em `write_build_report` (no test existente de repo
artifacts, se houver): a seção "## Custos e qualidade do build" aparece no
texto gerado.

## Não-objetivos

- Somar `cost_breakdown` (vazio hoje).
- Instrumentar/contar imagens rejeitadas por ruído.
- Tabela de custo por arquivo.
- Configurar taxa $/página (usuário multiplica externamente; YAGNI).
