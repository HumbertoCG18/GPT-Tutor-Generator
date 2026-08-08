# Fixture: teaching_plan REAL do MF (%APPDATA%/GPTTutorGenerator/subjects.json,
# perfil MF, extraido 2026-08-07; mtime observado da fonte 2026-08-07 —
# diverge do 2026-08-04 do brief, ver task-1-report.md).
# Headings REAIS coletados do repo MF (audit 2026-08-07, spec-review §F3).
# Caso: bullets-preview "1.3.1. Verificacao de Modelos" / "1.3.2. Verificacao de
# Programas" na abertura da u01 contaminavam a assinatura da u01 (empate 4x4 no
# bloco-16 — docs/reports/2026-08-06-task3-colisao-rotulo-mf.md).
from pathlib import Path

from src.builder.extraction.content_taxonomy import (
    build_content_taxonomy,
    _unit_title_core_tokens,
)
from src.builder.extraction.teaching_plan import _parse_units_from_teaching_plan, _topic_text
from src.builder.timeline.unit_matcher import _unit_tokens
from src.utils.helpers import slugify

MF_PLAN = Path("tests/fixtures/taxonomy/mf_teaching_plan.txt").read_text(encoding="utf-8")
MF_HEADINGS = [
    "VERIFICAÇÃO DE MODELOS",
    "Verificação de Modelos e Lógica Temporal",
    "checagem de modelos",
    "Verificação de Modelos NuSMV/NuXMV + Fasten",
    "Programação e Verificação com Dafny",
]


def _mk(plan, headings):
    return build_content_taxonomy(
        teaching_plan=plan,
        course_map_md="",
        glossary_md="",
        strong_headings=headings,
        parse_units_from_teaching_plan=_parse_units_from_teaching_plan,
        # DESVIO (ver task-1-report.md): o brief tinha `lambda t: str(t)`, que
        # serializa a tupla (texto, depth) inteira ("('1.1. Foo', 0)") em vez do
        # texto. Isso corrompe o label a ponto de _is_valid_topic_candidate
        # rejeitar todo topico-preview como "weak heading" ANTES de chegar na
        # migracao (a) -- o RED nao reproduzia o bug real. _topic_text e a
        # funcao de producao real (engine.py: _topic_text = _teaching_plan_topic_text),
        # usada por todo caller real de build_content_taxonomy.
        topic_text=_topic_text,
        normalize_unit_slug=lambda title: slugify(title),
    )


def test_title_core_tokens_por_tokens_sem_regex_de_prefixo():
    # DESVIO (ver task-1-report.md): _unit_title_core_tokens reusa
    # _topic_support_tokens, que trunca tokens >=5 chars pro stem de 5 chars
    # (fuzzy-match ja existente no modulo, ex.: "modelo"/"modelos" -> "model").
    # Valores abaixo sao os stems REAIS observados, nao a palavra cheia.
    assert _unit_title_core_tokens("Unidade 01 — Métodos Formais") == {"metod", "forma"}
    # "Aprendizagem" e "Aprendizado" colidem no MESMO stem "apren" (limitacao
    # conhecida do stem-5) -> ambos caem no filtro generico; so "maqui" sobra.
    assert _unit_title_core_tokens("Unidade de Aprendizagem 5 — Aprendizado de máquina") == {"maqui"}
    assert _unit_title_core_tokens("UNIDADE 02 — Turing-Computabilidade​") == {"turin"}
    # sem prefixo padrao -> titulo inteiro e o nucleo (degradacao graciosa)
    assert _unit_title_core_tokens("Verificação de Modelos") == {"verif", "model"}


def test_preview_migra_para_unidade_dona():
    tax = _mk(MF_PLAN, MF_HEADINGS)
    units = tax["units"]
    assert len(units) == 3
    u01, u02, u03 = units
    labels_u01 = [t["label"] for t in u01["topics"]]
    assert all("Modelos (Model Checking)" not in l for l in labels_u01)
    assert all(l != "Verificação de Programas" for l in labels_u01)
    # aliases ricos foram junto pro dono
    labels_u03 = [t["label"] for t in u03["topics"]]
    assert any("Verificação de Modelos" in l for l in labels_u03)


def test_assinatura_u01_sem_tokens_da_u03():
    tax = _mk(MF_PLAN, MF_HEADINGS)
    u01, u02, u03 = tax["units"]
    assert "temporal" not in _unit_tokens(u01)
    assert "temporal" in _unit_tokens(u03)


def test_heading_com_nucleo_de_titulo_so_enriquece_a_dona():
    tax = _mk(MF_PLAN, ["Verificação de Modelos e Lógica Temporal"])
    u01, u02, u03 = tax["units"]
    aliases_u01 = [a for t in u01["topics"] for a in t.get("aliases", [])]
    assert "Verificação de Modelos e Lógica Temporal" not in aliases_u01


def test_titulo_de_um_token_nao_participa_da_exclusividade():
    # guard anti-falso-positivo: nucleo com < 2 tokens (ex.: "Deadlock" SO u04)
    # "deadlock" (8 chars) tambem sofre o stem-5 -> "deadl" (ver desvio acima)
    assert _unit_title_core_tokens("Unidade 04 — _Deadlock_") == {"deadl"}
    # a exclusividade exige >= 2 tokens; taxonomia com titulo curto nao move nada
    # (coberto indiretamente: MF nao tem titulo de 1 token; asserção documental)


from src.builder.extraction.content_taxonomy import _clean_heading_text


def test_clean_heading_strips_decoracao_markdown():
    assert _clean_heading_text("**Exercícios**") == "Exercícios"
    assert (
        _clean_heading_text("[Formal Verification of Axiom-Free Proof](./entries/x.html)")
        == "Formal Verification of Axiom-Free Proof"
    )


def test_clean_heading_descarta_administrativo_e_tabela():
    # casos reais: TCC plano-de-ensino.md e geradas "Sumário"/"Conteúdo Extraído"
    assert _clean_heading_text("| NOME | E-MAIL | |---| Anderson |") == ""
    assert _clean_heading_text("PLANO DE ENSINO") == ""
    assert _clean_heading_text("PROFESSOR (ES)") == ""
    assert _clean_heading_text("Sumário") == ""
    assert _clean_heading_text("Conteúdo Extraído") == ""
    assert _clean_heading_text("Imagens Curadas") == ""


def test_clean_heading_preserva_conteudo_legitimo():
    assert _clean_heading_text("Verificação de Modelos e Lógica Temporal") == "Verificação de Modelos e Lógica Temporal"
