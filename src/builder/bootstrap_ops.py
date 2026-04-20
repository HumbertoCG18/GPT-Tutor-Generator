from __future__ import annotations

from datetime import datetime

from src.utils.helpers import ensure_dir, write_text


def create_structure(root_dir) -> None:
    dirs = [
        "system",
        "course",
        "content/units",
        "content/concepts",
        "content/summaries",
        "content/references",
        "content/curated",
        "content/images",
        "exercises/lists",
        "exercises/solved",
        "exercises/index",
        "exams/past-exams",
        "exams/answer-keys",
        "exams/exam-index",
        "student",
        "scripts",
        "raw/pdfs/material-de-aula",
        "raw/pdfs/provas",
        "raw/pdfs/listas",
        "raw/pdfs/gabaritos",
        "raw/pdfs/cronograma",
        "raw/pdfs/referencias",
        "raw/pdfs/bibliografia",
        "raw/pdfs/fotos-de-prova",
        "raw/pdfs/outros",
        "raw/images/fotos-de-prova",
        "raw/images/provas",
        "raw/images/material-de-aula",
        "raw/images/outros",
        "code/professor",
        "code/student",
        "raw/code/professor",
        "raw/code/student",
        "raw/zip",
        "raw/repos",
        "assignments/enunciados",
        "assignments/entregas",
        "raw/pdfs/trabalhos",
        "whiteboard/raw",
        "whiteboard/transcriptions",
        "raw/images/quadro-branco",
        "staging/markdown-auto/pymupdf4llm",
        "staging/markdown-auto/pymupdf",
        "staging/markdown-auto/docling",
        "staging/markdown-auto/marker",
        "staging/markdown-auto/scanned",
        "staging/markdown-auto/code",
        "staging/zip-extract",
        "manual-review/code",
        "manual-review/web",
        "staging/assets/images",
        "staging/assets/inline-images",
        "staging/assets/tables",
        "staging/assets/table-detections",
        "manual-review/pdfs",
        "manual-review/images",
        "build/claude-knowledge",
    ]
    for d in dirs:
        ensure_dir(root_dir / d)


def write_root_files(
    builder,
    *,
    tutor_policy_md_fn,
    pedagogy_md_fn,
    modes_md_fn,
    output_templates_md_fn,
    pdf_curation_guide_fn,
    backend_architecture_md_fn,
    backend_policy_yaml_fn,
    course_map_md_fn,
    glossary_md_fn,
    student_state_md_fn,
    progress_schema_md_fn,
    student_profile_md_fn,
    syllabus_md_fn,
    bibliography_md_fn,
    exam_index_md_fn,
    exercise_index_md_fn,
    assignment_index_md_fn,
    code_index_md_fn,
    whiteboard_index_md_fn,
    root_readme_fn,
    generated_repo_gitignore_text_fn,
    generate_claude_project_instructions_fn,
    generate_gpt_instructions_fn,
    generate_gemini_instructions_fn,
    exam_categories,
    exercise_categories,
    assignment_categories,
    code_categories,
    whiteboard_categories,
) -> None:
    course_slug = builder.course_meta["course_slug"]

    write_text(
        builder.root_dir / "course" / "COURSE_IDENTITY.md",
        f"""---
course_slug: {course_slug}
course_name: {builder.course_meta['course_name']}
semester: {builder.course_meta['semester']}
professor: {builder.course_meta['professor']}
institution: {builder.course_meta['institution']}
created_at: {datetime.now().isoformat(timespec='seconds')}
---

# COURSE_IDENTITY

## Disciplina
- Nome: {builder.course_meta['course_name']}
- Slug: {course_slug}
- Semestre: {builder.course_meta['semester']}
- Professor: {builder.course_meta['professor']}
- Instituição: {builder.course_meta['institution']}

## Objetivo
Este repositório organiza o conhecimento da disciplina em formato rastreável,
curado e reutilizável para um tutor acadêmico baseado no Claude.
""",
    )

    write_text(builder.root_dir / "system" / "TUTOR_POLICY.md", tutor_policy_md_fn(builder.course_meta, builder.subject_profile))
    write_text(builder.root_dir / "system" / "PEDAGOGY.md", pedagogy_md_fn())
    write_text(builder.root_dir / "system" / "MODES.md", modes_md_fn(builder.course_meta, builder.subject_profile))
    write_text(builder.root_dir / "system" / "OUTPUT_TEMPLATES.md", output_templates_md_fn(builder.course_meta, builder.subject_profile))

    write_text(builder.root_dir / "build" / "PDF_CURATION_GUIDE.md", pdf_curation_guide_fn())
    write_text(builder.root_dir / "build" / "BACKEND_ARCHITECTURE.md", backend_architecture_md_fn())
    write_text(builder.root_dir / "build" / "BACKEND_POLICY.yaml", backend_policy_yaml_fn(builder.options))

    write_text(builder.root_dir / "course" / "COURSE_MAP.md", course_map_md_fn(builder.course_meta, builder.subject_profile))
    write_text(
        builder.root_dir / "course" / "GLOSSARY.md",
        glossary_md_fn(
            builder.course_meta,
            builder.subject_profile,
            root_dir=builder.root_dir,
            manifest_entries=[e.to_dict() for e in builder.entries],
        ),
    )

    write_text(builder.root_dir / "student" / "STUDENT_STATE.md", student_state_md_fn(builder.course_meta, builder.student_profile))
    write_text(builder.root_dir / "build" / "PROGRESS_SCHEMA.md", progress_schema_md_fn())
    builder._ensure_unit_battery_directories()

    if builder.student_profile:
        write_text(builder.root_dir / "student" / "STUDENT_PROFILE.md", student_profile_md_fn(builder.student_profile))

    if builder.subject_profile and builder.subject_profile.syllabus:
        write_text(builder.root_dir / "course" / "SYLLABUS.md", syllabus_md_fn(builder.subject_profile))

    bib_entries = [e for e in builder.entries if e.category == "bibliografia"]
    write_text(builder.root_dir / "content" / "BIBLIOGRAPHY.md", bibliography_md_fn(builder.course_meta, bib_entries, builder.subject_profile))

    exam_entries = [e for e in builder.entries if e.category in exam_categories]
    if exam_entries:
        write_text(builder.root_dir / "exams" / "EXAM_INDEX.md", exam_index_md_fn(builder.course_meta, exam_entries))

    exercise_entries = [e for e in builder.entries if e.category in exercise_categories]
    if exercise_entries:
        write_text(builder.root_dir / "exercises" / "EXERCISE_INDEX.md", exercise_index_md_fn(builder.course_meta, exercise_entries))

    assignment_entries = [e for e in builder.entries if e.category in assignment_categories]
    if assignment_entries:
        write_text(builder.root_dir / "assignments" / "ASSIGNMENT_INDEX.md", assignment_index_md_fn(builder.course_meta, assignment_entries))

    code_entries = [e for e in builder.entries if e.category in code_categories]
    if code_entries:
        write_text(builder.root_dir / "code" / "CODE_INDEX.md", code_index_md_fn(builder.course_meta, code_entries, builder.subject_profile))

    wb_entries = [e for e in builder.entries if e.category in whiteboard_categories]
    if wb_entries:
        write_text(builder.root_dir / "whiteboard" / "WHITEBOARD_INDEX.md", whiteboard_index_md_fn(builder.course_meta, wb_entries))

    write_text(builder.root_dir / "README.md", root_readme_fn(builder.course_meta))
    write_text(builder.root_dir / ".gitignore", generated_repo_gitignore_text_fn())

    common_flags = dict(
        has_assignments=any(e.category in assignment_categories for e in builder.entries),
        has_code=any(e.category in code_categories for e in builder.entries),
        has_whiteboard=any(e.category in whiteboard_categories for e in builder.entries),
    )
    write_text(
        builder.root_dir / "setup" / "INSTRUCOES_CLAUDE_PROJETO.md",
        generate_claude_project_instructions_fn(
            builder.course_meta,
            builder.student_profile,
            builder.subject_profile,
            **common_flags,
        ),
    )
    write_text(
        builder.root_dir / "setup" / "INSTRUCOES_GPT_PROJETO.md",
        generate_gpt_instructions_fn(
            builder.course_meta,
            builder.student_profile,
            builder.subject_profile,
            **common_flags,
        ),
    )
    write_text(
        builder.root_dir / "setup" / "INSTRUCOES_GEMINI_PROJETO.md",
        generate_gemini_instructions_fn(
            builder.course_meta,
            builder.student_profile,
            builder.subject_profile,
            **common_flags,
        ),
    )
