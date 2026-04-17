from __future__ import annotations

import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from src.utils.helpers import json_str


def student_state_md(
    course_meta: dict,
    student_profile=None,
    *,
    render_student_state_md_fn: Callable[..., str],
) -> str:
    course_name = course_meta.get("course_name", "Curso")
    nick = "Aluno"
    if student_profile and getattr(student_profile, "full_name", ""):
        nick = getattr(student_profile, "nickname", "") or getattr(student_profile, "full_name", "")

    today = datetime.now().strftime("%Y-%m-%d")

    return render_student_state_md_fn(
        course_name=course_name,
        student_nickname=nick,
        today=today,
        active=None,
        active_unit_progress=[],
        recent=[],
        closed_units=[],
        next_topic="",
    )


def progress_schema_md() -> str:
    return """# PROGRESS_SCHEMA

## Schema do estado do aluno

Define a estrutura esperada de `STUDENT_STATE.md`.
Use este arquivo como referência ao atualizar o estado manualmente
ou ao pedir ao Claude para gerar uma atualização.

## Campos obrigatórios

```yaml
---
course: string          # Nome da disciplina
student: string         # Nome/apelido do aluno
last_updated: YYYY-MM-DD
---
```

## Status válidos para tópicos

| Status | Significado |
|---|---|
| `não iniciado` | Ainda não foi estudado |
| `em progresso` | Estudado mas não consolidado |
| `com dúvidas` | Estudado com pontos em aberto |
| `concluído` | Compreensão sólida demonstrada |
| `revisão` | Concluído mas precisa reforçar para prova |

## Ciclo de atualização recomendado

```
Sessão de estudo
    → Claude sugere bloco de atualização
    → Aluno revisa e ajusta
    → Aluno faz commit no GitHub
    → Na próxima sessão: Claude lê o estado atualizado
```

## Template de atualização (gerado pelo Claude ao final da sessão)

```markdown
## Atualização sugerida — [DATA]

**Tópico estudado:** [nome]
**Status:** [status válido acima]
**Dúvidas identificadas:** [lista ou "nenhuma"]
**Erros observados:** [lista ou "nenhum"]
**Próximo passo:** [próximo tópico sugerido]
```
"""


def bibliography_md(
    course_meta: dict,
    entries=None,
    subject_profile=None,
    *,
    parse_bibliography_from_teaching_plan_fn: Callable[[str], dict],
    clamp_navigation_artifact: Callable[..., str],
) -> str:
    course_name = course_meta.get("course_name", "Curso")
    entries = entries or []

    lines = [
        f"# BIBLIOGRAPHY — {course_name}",
        "",
        "> **Como usar:** Links e referências da disciplina.",
        "> O tutor consulta este arquivo quando o aluno pede fontes",
        "> ou quando uma explicação pode ser aprofundada com leitura adicional.",
        "",
    ]

    teaching_plan = getattr(subject_profile, "teaching_plan", "") if subject_profile else ""
    parsed = parse_bibliography_from_teaching_plan_fn(teaching_plan) if teaching_plan else {}
    basica = parsed.get("basica", [])
    complementar = parsed.get("complementar", [])

    if basica or complementar:
        lines.append("## Bibliografia do plano de ensino")
        lines.append("")
        if basica:
            lines.append("### Básica")
            lines.append("")
            for ref in basica:
                lines.append(f"- {ref}")
            lines.append("")
        if complementar:
            lines.append("### Complementar")
            lines.append("")
            for ref in complementar:
                lines.append(f"- {ref}")
            lines.append("")

    if entries:
        lines.append("## Referências importadas")
        lines.append("")
        for entry in entries:
            lines.append(f"### {entry.title}")
            lines.append(f"- **URL:** {entry.source_path}")
            if entry.tags:
                lines.append(f"- **Tags:** {entry.tags}")
            if entry.notes:
                lines.append(f"- **Nota:** {entry.notes}")
            if entry.professor_signal:
                lines.append(f"- **Indicação do professor:** {entry.professor_signal}")
            lines.append(f"- **Incluir no bundle:** {'sim' if entry.include_in_bundle else 'não'}")
            lines.append("")

    if not basica and not complementar and not entries:
        lines += [
            "## Referências",
            "",
            "<!-- Adicione referências aqui, importe links pelo app,",
            "     ou preencha o Plano de Ensino no Gerenciador de Matérias. -->",
            "",
        ]

    lines += [
        "## Mapa de relevância por tópico",
        "",
        "<!-- Preencha após organizar as referências -->",
        "",
        "| Tópico | Referência principal | Acessível | Incidência em prova |",
        "|---|---|---|---|",
        "| [a preencher] | | | |",
        "",
    ]

    return clamp_navigation_artifact(
        "\n".join(lines),
        max_chars=14000,
        label="course/COURSE_MAP.md",
    )


def exam_index_md(course_meta: dict, entries=None, *, clamp_navigation_artifact: Callable[..., str]) -> str:
    course_name = course_meta.get("course_name", "Curso")
    entries = entries or []

    lines = [
        f"# EXAM_INDEX — {course_name}",
        "",
        "> **Como usar:** Índice de provas anteriores por tópico.",
        "> O tutor consulta este arquivo no modo `exam_prep` para identificar",
        "> quais tópicos têm maior incidência e quais padrões de questão se repetem.",
        "",
        "## Provas disponíveis",
        "",
    ]

    lines.append("| Arquivo | Tipo | Prova | Observação | Padrão do professor |")
    lines.append("|---|---|---|---|---|")
    for entry in entries:
        tipo = "foto" if entry.category == "fotos-de-prova" else "original"
        lines.append(
            f"| {Path(entry.source_path).name} | {tipo} | {entry.title} "
            f"| {entry.notes or ''} | {entry.professor_signal or ''} |"
        )

    lines += [
        "",
        "## Incidência de tópicos por prova",
        "",
        "> Preencha após revisar cada prova. O tutor usa esta tabela no modo `exam_prep`.",
        "",
        "| Tópico | P1 | P2 | P3 | Total | Peso estimado |",
        "|---|---|---|---|---|---|",
        "| [a preencher] | | | | | |",
        "",
        "## Padrões de questão observados",
        "",
        "<!-- Liste padrões recorrentes: tipos de enunciado, estrutura, pegadinhas comuns -->",
        "",
    ]

    return clamp_navigation_artifact(
        "\n".join(lines),
        max_chars=12000,
        label="course/FILE_MAP.md",
    )


def assignment_index_md(course_meta: dict, entries=None, *, clamp_navigation_artifact: Callable[..., str]) -> str:
    course_name = course_meta.get("course_name", "Curso")
    entries = entries or []
    lines = [
        f"# ASSIGNMENT_INDEX — {course_name}",
        "",
        "> **Como usar:** Índice de trabalhos e projetos.",
        "> Consulte antes de guiar o aluno — não entregue a solução.",
        "",
        "## Trabalhos",
        "",
    ]
    if entries:
        lines += ["| Arquivo | Título | Unidade | Status |", "|---|---|---|---|"]
        for e in entries:
            lines.append(f"| {Path(e.source_path).name} | {e.title} | {e.tags or ''} | pendente |")
    else:
        lines += ["| Arquivo | Título | Unidade | Status |", "|---|---|---|---|", "| [a preencher] | | | |"]
    lines += ["", "## Padrões do professor", "", "- [a preencher]", ""]
    result = "\n".join(lines)
    return clamp_navigation_artifact(result, max_chars=12000, label="course/FILE_MAP.md")


def code_index_md(
    course_meta: dict,
    entries=None,
    subject_profile=None,
    *,
    code_review_profile_fn: Callable[[Optional[dict], object], dict],
    clamp_navigation_artifact: Callable[..., str],
) -> str:
    course_name = course_meta.get("course_name", "Curso")
    entries = entries or []
    prof_entries = [e for e in entries if e.category == "codigo-professor"]
    profile = code_review_profile_fn(course_meta, subject_profile)
    lines = [
        f"# CODE_INDEX — {course_name}",
        "",
        profile["code_index_intro"],
        profile["code_index_review_line"],
        "",
    ]
    if prof_entries:
        lines += [
            profile["code_index_section"],
            "",
            "| Arquivo | Linguagem | Unidade | Conceito demonstrado | Notas |",
            "|---|---|---|---|---|",
        ]
        for e in prof_entries:
            conceito = e.professor_signal or "[a preencher]"
            unit_str = ""
            if e.notes and "Unidade:" in e.notes:
                try:
                    unit_str = e.notes.split("Unidade:")[1].strip()
                except (IndexError, AttributeError):
                    pass
            lines.append(
                f"| {Path(e.source_path).name} | {e.tags or ''} | {unit_str} | {conceito} | |"
            )
        lines.append("")
    else:
        lines += [profile["code_index_empty"], ""]
    lines += [
        profile["code_index_patterns"],
        "",
        "<!-- Preencha conforme analisar o código -->",
        "- [a preencher]",
        "",
    ]
    result = "\n".join(lines)
    return clamp_navigation_artifact(result, max_chars=14000, label="course/COURSE_MAP.md")


def whiteboard_index_md(course_meta: dict, entries=None, *, clamp_navigation_artifact: Callable[..., str]) -> str:
    course_name = course_meta.get("course_name", "Curso")
    entries = entries or []
    lines = [f"# WHITEBOARD_INDEX — {course_name}", "", "> Fotos de quadro branco com explicações do professor.", ""]
    if entries:
        lines += ["| Arquivo | Título | Unidade | Padrão identificado |", "|---|---|---|---|"]
        for e in entries:
            lines.append(f"| {Path(e.source_path).name} | {e.title} | {e.tags or ''} | {e.professor_signal or ''} |")
    else:
        lines += ["| Arquivo | Título | Unidade | Padrão identificado |", "|---|---|---|---|", "| [a preencher] | | | |"]
    lines += ["", "## Padrões pedagógicos", "", "- [a preencher]", ""]
    result = "\n".join(lines)
    return clamp_navigation_artifact(result, max_chars=12000, label="course/FILE_MAP.md")


def root_readme(course_meta: dict) -> str:
    return f"""# {course_meta.get('course_name', 'Curso')}

Repositório gerado pelo **Academic Tutor Repo Builder V3**.
Plataforma alvo: **Claude Projects** (claude.ai)

## Como usar com Claude

1. Crie um **Projeto** no Claude.ai com o nome desta disciplina
2. Cole o conteúdo de `setup/INSTRUCOES_CLAUDE_PROJETO.md` no campo **Instructions** do Projeto
3. Conecte este repositório GitHub ao Projeto (aba Settings → GitHub)
4. Inicie uma conversa — o Claude lerá os arquivos automaticamente

## Estrutura
- `system/` — política do tutor, pedagogia, modos, templates
- `course/` — identidade, mapa, cronograma, glossário, bibliografia
- `student/` — estado atual, perfil, schema de progresso
- `content/` — material de aula curado
- `exercises/` — listas de exercícios
- `exams/` — provas anteriores e gabaritos
- `raw/` — materiais originais (PDFs, imagens)
- `staging/` — extração automática (para revisão)
- `manual-review/` — revisão humana guiada
- `build/claude-knowledge/` — bundle para upload manual se necessário

## Arquivos-chave para o tutor

| Arquivo | Função |
|---|---|
| `setup/INSTRUCOES_CLAUDE_PROJETO.md` | System prompt do Projeto (não indexado pelo tutor) |
| `student/STUDENT_STATE.md` | Estado atual do aluno — atualizar após cada sessão |
| `course/COURSE_MAP.md` | Preencher com os tópicos em ordem |
| `course/GLOSSARY.md` | Preencher com terminologia da disciplina |
| `content/BIBLIOGRAPHY.md` | Referências bibliográficas |

## Fluxo recomendado

1. Rodar extração automática no app
2. Revisar `manual-review/`
3. Promover conteúdo curado para `content/`, `exercises/`, `exams/`
4. Preencher `COURSE_MAP.md` e `GLOSSARY.md`
5. Conectar ao Projeto no Claude.ai
6. Após cada sessão de estudo: atualizar `student/STUDENT_STATE.md` e fazer push
"""


def wrap_frontmatter(meta: dict, body: str, *, json_str_fn: Optional[Callable[[Any], str]] = None) -> str:
    json_str_fn = json_str_fn or json_str
    header = ["---"]
    for k, v in meta.items():
        header.append(f"{k}: {json_str_fn(v)}")
    header.append("---")
    header.append("")
    return "\n".join(header) + body.strip() + "\n"


def rows_to_markdown_table(rows: list) -> str:
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    fixed = [r + [""] * (width - len(r)) for r in rows]
    header = fixed[0]
    sep = ["---"] * width
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(sep) + " |",
    ]
    for row in fixed[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines) + "\n"


def manual_pdf_review_template(entry, item: Dict[str, object], *, json_str_fn: Callable[[Any], str]) -> str:
    report = item.get("document_report") or {}
    decision = item.get("pipeline_decision") or {}
    return f"""---
id: {entry.id()}
title: {json_str_fn(entry.title)}
type: manual_pdf_review
category: {entry.category}
source_pdf: {json_str_fn(item.get('raw_target'))}
processing_mode: {json_str_fn(entry.processing_mode)}
document_profile: {json_str_fn(entry.document_profile)}
page_range: {json_str_fn(entry.page_range)}
effective_profile: {json_str_fn(item.get('effective_profile'))}
base_backend: {json_str_fn(item.get('base_backend'))}
advanced_backend: {json_str_fn(item.get('advanced_backend'))}
base_markdown: {json_str_fn(item.get('base_markdown'))}
advanced_markdown: {json_str_fn(item.get('advanced_markdown'))}
---

# Revisão Manual — {entry.title}

## Perfil detectado
- Perfil efetivo: `{item.get('effective_profile')}`
- Páginas: `{report.get('page_count')}`
- Texto: `{report.get('text_chars')}` chars
- Imagens: `{report.get('images_count')}`
- Tabelas: `{report.get('table_candidates')}`
- Scan: `{report.get('suspected_scan')}`

## Pipeline
- Modo: `{decision.get('processing_mode')}`
- Base: `{decision.get('base_backend')}`
- Avançado: `{decision.get('advanced_backend')}`

## Checklist
- [ ] Conferir títulos e subtítulos
- [ ] Corrigir ordem de leitura
- [ ] Revisar fórmulas e converter para LaTeX
- [ ] Revisar tabelas exportadas
- [ ] Verificar imagens/figuras importantes
- [ ] Registrar pistas sobre o professor

## Markdown corrigido
<!-- Cole aqui a versão corrigida -->

## Destino curado sugerido
- [ ] `content/curated/`
- [ ] `exercises/lists/`
- [ ] `exams/past-exams/`
"""


def manual_image_review_template(entry, raw_target: Path, root_dir: Path, *, safe_rel_fn: Callable[[Path, Path], str]) -> str:
    image_path = safe_rel_fn(raw_target, root_dir)
    return f"""---
id: {entry.id()}
title: {json.dumps(entry.title, ensure_ascii=False)}
type: manual_image_review
category: {entry.category}
source_image: {json.dumps(image_path, ensure_ascii=False)}
---

# Revisão Manual — Imagem

## Metadados
- Tags: `{entry.tags}`
- Relevante para prova: `{entry.relevant_for_exam}`
- Sinal do professor: `{entry.professor_signal}`

## Transcrição fiel
<!-- Escreva o texto da imagem aqui -->

## Destino curado sugerido
- [ ] `exams/past-exams/`
- [ ] `content/curated/`
"""


def manual_url_review_template(entry, item: Dict[str, object], *, json_str_fn: Callable[[Any], str]) -> str:
    source_url = entry.source_path
    return f"""---
id: {entry.id()}
title: {json_str_fn(entry.title)}
type: manual_url_review
category: {entry.category}
source_url: {json_str_fn(source_url)}
processing_mode: {json_str_fn(entry.processing_mode)}
base_backend: {json_str_fn(item.get('base_backend'))}
base_markdown: {json_str_fn(item.get('base_markdown'))}
---

# Revisão Manual — Página Web

## Origem
- URL: <{source_url}>
- Backend base: `{item.get('base_backend')}`

## Checklist
- [ ] Conferir se o conteúdo baixado corresponde à página correta
- [ ] Remover navegação, rodapé, anúncios e texto irrelevante
- [ ] Corrigir títulos e hierarquia de seções
- [ ] Verificar se links importantes foram preservados
- [ ] Destacar trechos úteis para o tutor

## Markdown corrigido
<!-- Cole aqui a versão corrigida -->

## Destino curado sugerido
- [ ] `content/curated/`
- [ ] `course/references/`
"""


def migrate_legacy_url_manual_reviews(
    root_dir: Path,
    *,
    ensure_dir_fn: Callable[[Path], None],
    safe_rel_fn: Callable[[Path, Path], str],
    write_text_fn: Callable[[Path, str], None],
    logger,
) -> int:
    manual_pdfs_dir = root_dir / "manual-review" / "pdfs"
    manual_web_dir = root_dir / "manual-review" / "web"
    if not manual_pdfs_dir.exists():
        return 0

    ensure_dir_fn(manual_web_dir)
    manifest_path = root_dir / "manifest.json"
    manifest = None
    manifest_changed = False
    moved = 0

    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Could not read manifest.json during URL review migration: %s", exc)
            manifest = None

    for review_path in manual_pdfs_dir.rglob("*.md"):
        try:
            content = review_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        fm = {}
        match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if match:
            for line in match.group(1).strip().split("\n"):
                if ":" not in line:
                    continue
                key, _, value = line.partition(":")
                fm[key.strip()] = value.strip().strip('"').strip("'")

        if fm.get("type") != "manual_url_review" and fm.get("base_backend") != "url_fetcher":
            continue

        destination = manual_web_dir / review_path.name
        if destination.exists():
            try:
                review_path.unlink()
            except Exception as exc:
                logger.warning("Could not remove duplicate legacy URL review %s: %s", review_path, exc)
            else:
                moved += 1
            continue

        ensure_dir_fn(destination.parent)
        try:
            shutil.move(str(review_path), str(destination))
        except Exception as exc:
            logger.warning("Could not migrate legacy URL review %s: %s", review_path, exc)
            continue

        moved += 1
        entry_id = fm.get("id") or destination.stem
        if manifest:
            for entry in manifest.get("entries", []):
                if entry.get("id") == entry_id and entry.get("manual_review"):
                    old_rel = safe_rel_fn(review_path, root_dir)
                    if entry.get("manual_review") == old_rel:
                        entry["manual_review"] = safe_rel_fn(destination, root_dir)
                        manifest_changed = True
                    break

    if manifest and manifest_changed:
        manifest["updated_at"] = datetime.now().isoformat(timespec="seconds")
        write_text_fn(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))

    return moved


def pdf_curation_guide() -> str:
    return """# PDF_CURATION_GUIDE

## Regra central
PDF bruto não é conhecimento final.
Ele é insumo para:
1. extração automática
2. revisão manual
3. curadoria por função pedagógica

## Quando usar cada camada
- Base: PDFs simples, texto corrido, listas e cronogramas.
- Avançada: fórmulas, tabelas difíceis, layout complexo, scans, provas.
- Manual assisted: qualquer material que influencie a lógica de prova.

## Artefatos gerados
- `raw/`: arquivo original
- `staging/`: extração automática
- `manual-review/`: revisão humana guiada
- `content/` e `exams/`: conhecimento curado

## Destino final no Claude Project
Todo arquivo curado deve estar em formato Markdown limpo
para ser lido eficientemente pelo Claude via integração GitHub.
"""


def backend_architecture_md() -> str:
    return """# BACKEND_ARCHITECTURE

## Visão geral
A V3 usa arquitetura de backends em camadas.

```text
PDF bruto
 -> camada base
 -> camada avançada (quando necessário)
 -> extração de artefatos
 -> revisão manual guiada
 -> conteúdo curado
 -> Claude Project (via GitHub sync)
```

## Camada base
- `pymupdf4llm`: Markdown rápido para PDFs digitais.
- `pymupdf`: fallback bruto.

## Camada avançada
- `docling`: OCR, fórmulas, tabelas e imagens referenciadas.
- `marker`: equações, inline math, tabelas e imagens.

## Modos de processamento
- `quick`: só camada base.
- `high_fidelity`: base + avançada.
- `manual_assisted`: base + artefatos + revisão humana.
- `auto`: decide pelo perfil do documento.

## Regra de ouro
O tutor não deve consumir o PDF bruto como fonte final.
A fonte final deve ser o Markdown curado derivado da revisão manual,
sincronizado com o Claude Project via GitHub.
"""


def backend_policy_yaml(options: Dict[str, object], *, json_str_fn: Callable[[Any], str]) -> str:
    return f"""version: 3
target_platform: claude-projects
policy:
  default_processing_mode: {options.get('default_processing_mode', 'auto')}
  default_ocr_language: {json_str_fn(options.get('default_ocr_language', 'por,eng'))}
  require_manual_review_for:
    - math_heavy
    - scanned
    - diagram_heavy
  base_layer_priority:
    - pymupdf4llm
    - pymupdf
  advanced_layer_priority:
    - docling
    - marker
  asset_pipeline:
    extract_images: true
    extract_tables: true
  promotion_rule: |
    Nenhum arquivo de staging é conhecimento final.
    O conhecimento final deve sair de manual-review/ e depois ser promovido
    para content/, exercises/ ou exams/, e então sincronizado com o Claude Project.
"""


def exercise_index_md(
    course_meta: dict,
    entries=None,
    *,
    collapse_ws_fn: Callable[[str], str],
    merge_manual_and_auto_tags_fn: Callable[..., str],
    clamp_navigation_artifact: Callable[..., str],
) -> str:
    course_name = course_meta.get("course_name", "Curso")
    entries = entries or []
    lines = [
        f"# EXERCISE_INDEX — {course_name}",
        "",
        "> **Como usar:** Índice operacional de prática da disciplina.",
        "> O tutor consulta este arquivo para localizar listas, provas antigas",
        "> e recursos de exercícios por unidade, prioridade e finalidade.",
        "",
        "| Recurso | Tipo | Unidade | Solução | Prioridade | Quando usar |",
        "|---|---|---|---|---|---|",
    ]
    if entries:
        for entry in entries:
            notes = collapse_ws_fn(entry.notes or "")
            tags = collapse_ws_fn(
                merge_manual_and_auto_tags_fn(
                    list(entry.manual_tags or []),
                    list(entry.auto_tags or []),
                    fallback_tags=entry.tags or "",
                    limit=3,
                )
            )
            category = collapse_ws_fn(entry.category or "")
            category_lower = category.lower()
            kind = "prova" if "prova" in category_lower else "lista" if "lista" in category_lower else "exercício"
            has_solution = "sim" if any(token in notes.lower() for token in ["gabarito", "resolu", "soluç"]) else "não"
            priority = "alta" if "prova" in category_lower or has_solution == "sim" else "média"
            usage = "revisão de prova" if "prova" in category_lower else "fixação por unidade"
            lines.append(
                f"| {entry.title} | {kind} | {tags or 'não mapeado'} | {has_solution} | {priority} | {usage} |"
            )
    else:
        lines.append("| [a preencher] | | | | | |")
        lines += [
            "",
            "> Adicione listas ou provas antigas para o tutor conseguir sugerir prática com baixo custo de contexto.",
        ]
    lines.append("")
    result = "\n".join(lines)
    return clamp_navigation_artifact(result, max_chars=14000, label="exercises/EXERCISE_INDEX.md")
