from __future__ import annotations

from functools import partial


def build_repo_doc_aliases(
    *,
    repo_artifacts_module,
    student_state_render_fn,
    parse_bibliography_from_teaching_plan,
    clamp_navigation_artifact,
    code_review_profile_fn,
):
    student_state_md = partial(
        repo_artifacts_module.student_state_md,
        render_student_state_md_fn=student_state_render_fn,
    )
    progress_schema_md = repo_artifacts_module.progress_schema_md
    bibliography_md = partial(
        repo_artifacts_module.bibliography_md,
        parse_bibliography_from_teaching_plan_fn=parse_bibliography_from_teaching_plan,
        clamp_navigation_artifact=clamp_navigation_artifact,
    )
    exam_index_md = partial(
        repo_artifacts_module.exam_index_md,
        clamp_navigation_artifact=clamp_navigation_artifact,
    )
    assignment_index_md = partial(
        repo_artifacts_module.assignment_index_md,
        clamp_navigation_artifact=clamp_navigation_artifact,
    )
    code_index_md = partial(
        repo_artifacts_module.code_index_md,
        code_review_profile_fn=code_review_profile_fn,
        clamp_navigation_artifact=clamp_navigation_artifact,
    )
    whiteboard_index_md = partial(
        repo_artifacts_module.whiteboard_index_md,
        clamp_navigation_artifact=clamp_navigation_artifact,
    )
    return {
        "student_state_md": student_state_md,
        "progress_schema_md": progress_schema_md,
        "bibliography_md": bibliography_md,
        "exam_index_md": exam_index_md,
        "assignment_index_md": assignment_index_md,
        "code_index_md": code_index_md,
        "whiteboard_index_md": whiteboard_index_md,
    }

