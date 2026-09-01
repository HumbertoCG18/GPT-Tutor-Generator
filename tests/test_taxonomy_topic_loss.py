"""Perda de topicos do PLANO DE ENSINO ate a taxonomia (auditoria 2026-08-18).

Fixtures: linhas LITERAIS dos teaching_plan reais em
%APPDATA%/GPTTutorGenerator/subjects.json (perfis "Sistemas Operacionais",
"Teoria da Computabilidade e Complexidade", "Engenharia de Software II" e
"Inteligencia Artificial", lidos 2026-08-18) — formatos PUCRS distintos entre si.
Casos vindos de scripts/audit_taxonomy_losses.py: 15 topicos do plano ausentes da
taxonomia (TCC 11, SO 3, ES2 1).
"""
from src.builder.extraction.content_taxonomy import (
    _extract_topic_code,
    _looks_like_tool_candidate,
)
from src.builder.extraction.teaching_plan import _parse_units_from_teaching_plan, _topic_text

# SO: numeracao em negrito, item 5.1 SEM bullet (os irmaos 5.2-5.4 tem).
SO_U04 = "\n".join([
    "## **N\u00ba. DA UNIDADE:** 04 **CONTE\u00daDO:** _Deadlock_ ",
    "",
    "**5.1.** Conceitos b\u00e1sicos ",
    "",
    "- **5.2.** Caracteriza\u00e7\u00e3o ",
    "",
    "- Aulas expositivas nas quais se buscar\u00e1 a participa\u00e7\u00e3o dos alunos em um processo de discuss\u00e3o. ",
    "- Uso de projetor multim\u00eddia. ",
])

# ES2: numeracao SEM ponto final, item 1.1 sem bullet.
ES2_U01 = "\n".join([
    "## N\u00b0 DA UNIDADE: 01 ",
    "",
    "CONTE\u00daDO: Arquitetura de Software ",
    "",
    "1.1 Conceito de arquitetura de software ",
    "",
    "- 1.2 Vis\u00f5es arquiteturais: estrutural e din\u00e2mica ",
])

# TCC: 4 itens colados numa linha so pela extracao do PDF + zero-width space no titulo.
TCC_U04 = "\n".join([
    "## **UNIDADE 04: Hierarquia de Classes de Complexidade de Problemas Computacionais** ",
    "",
    "4.6.1 Defini\u00e7\u00e3o da Classe 4.6.2 Exemplos de Problemas em PSPACE 4.6.3 Provas de "
    "PSPACE-Completude 4.7 Intratabilidade ",
])
TCC_U02 = "\n".join([
    "## **UNIDADE 02: Turing-Computabilidade\u200b** ",
    "",
    "- 2.1. M\u00e1quinas de Turing ",
])

# IA: unidade de aprendizagem com topicos em linhas soltas, SEM numeracao e SEM bullet.
IA_U01 = "\n".join([
    "Unidade de Aprendizagem 1: Vis\u00e3o Geral (5%)",
    "Conceitua\u00e7\u00e3o",
    "",
    "Breve Hist\u00f3rico de IA",
])


def _codes(plan):
    return {_extract_topic_code(_topic_text(t))
            for _title, topics in _parse_units_from_teaching_plan(plan) for t in topics}


def _labels(plan):
    return [_topic_text(t) for _title, topics in _parse_units_from_teaching_plan(plan) for t in topics]


def test_topico_numerado_em_negrito_sem_bullet_e_capturado():
    assert "5.1" in _codes(SO_U04)


def test_numeracao_sem_ponto_final_e_capturada():
    assert "1.1" in _codes(ES2_U01)


def test_itens_colados_na_mesma_linha_viram_topicos_separados():
    assert {"4.6.1", "4.6.2", "4.6.3", "4.7"} <= _codes(TCC_U04)


def test_codigo_numerico_sobrevive_para_o_filtro_da_taxonomia():
    """build_content_taxonomy so pula o filtro de known_tools quando ha codigo:
    `if not topic_code and not _is_valid_topic_candidate(...)`."""
    assert "" not in _codes(SO_U04)
    assert "" not in _codes(ES2_U01)


def test_metodologia_nao_vira_topico_quando_a_unidade_tem_numerados():
    assert not any("projetor" in label for label in _labels(SO_U04))
    assert not any("expositivas" in label for label in _labels(SO_U04))


def test_unidade_sem_numeracao_mantem_topicos_em_linha_solta():
    """Formato IA: sem esse ramo a unidade inteira fica vazia."""
    labels = _labels(IA_U01)
    assert "Conceitua\u00e7\u00e3o" in labels
    assert "Breve Hist\u00f3rico de IA" in labels


def test_zero_width_space_nao_vaza_do_titulo_da_unidade():
    titles = [title for title, _ in _parse_units_from_teaching_plan(TCC_U02)]
    assert titles and "\u200b" not in titles[0]


def test_tool_so_casa_em_fronteira_de_palavra():
    """`ementa` derrubava "ImplEMENTAcao"; `threads` derrubava "mulTITHREADS"."""
    perfil = {"known_tools": ["ementa", "threads", "np-completude"]}
    assert not _looks_like_tool_candidate("Implementa\u00e7\u00e3o de sistemas de arquivos", semantic_profile=perfil)
    assert not _looks_like_tool_candidate("Programas multithreads", semantic_profile=perfil)
    assert _looks_like_tool_candidate("Uso de threads", semantic_profile=perfil)
    assert _looks_like_tool_candidate("Provas de NP-Completude", semantic_profile=perfil)


def test_heading_institucional_nao_vira_alias_de_topico():
    """"ENGENHARIA DE SOFTWARE II" encabeca TODO slide do curso; como alias ele
    transformava o topico dono em ima (ES2: Kubernetes e o T1 migraram para a
    unidade de arquitetura, medicao 2026-08-18)."""
    from src.builder.extraction.content_taxonomy import build_content_taxonomy
    from src.builder.extraction.teaching_plan import _normalize_unit_slug

    plan = "\n".join([
        "## N\u00b0 DA UNIDADE: 01 ",
        "CONTE\u00daDO: Arquitetura de Software ",
        "1.1 Conceito de arquitetura de software ",
    ])
    perfil = {"course_slug": "engenharia-de-software-ii",
              "generic_slug_blacklist": ["engenharia-de-software-ii"]}
    tax = build_content_taxonomy(
        plan, "", "",
        strong_headings=["ENGENHARIA DE SOFTWARE II ---",
                         "Trabalho FinalEngenharia de Software II",
                         "Estilos arquiteturais em camadas"],
        semantic_profile=perfil,
        parse_units_from_teaching_plan=_parse_units_from_teaching_plan,
        topic_text=_topic_text, normalize_unit_slug=_normalize_unit_slug)

    aliases = [a.lower() for u in tax["units"] for t in u["topics"] for a in (t.get("aliases") or [])]
    assert not any("engenharia de software ii" in a for a in aliases), aliases


def test_topico_do_plano_sem_codigo_nao_passa_pelo_filtro_de_heading():
    """IA u05 (2026-08-20): "Modelos Preditivos" sumia da taxonomia porque o plano
    nao tem codigo numerico e `_is_valid_topic_candidate` -- filtro de RUIDO DE
    HEADING -- e aplicado ao CONTEUDOS do plano. O marcador de bibliografia `ed`
    casa substring em "prEDitivos". Medido nos 5 cursos: o filtro rejeita 27 de
    127 topicos do plano, todos legitimos ("Logica de Hoare", "Teorema de
    Cook-Levin"); sobrevivem so pela isencao de codigo. Plano e fonte humana:
    nao e heading, nao passa pelo filtro."""
    from src.builder.extraction.content_taxonomy import build_content_taxonomy
    from src.builder.extraction.teaching_plan import _normalize_unit_slug

    plan = "\n".join([
        "Unidade de Aprendizagem 5: Aprendizado de m\u00e1quina",
        "Introdu\u00e7\u00e3o ao aprendizado de m\u00e1quina",
        "",
        "Paradigmas de aprendizado",
        "",
        "Modelos Preditivos",
        "",
        "Modelos Descritivos",
        "",
        "M\u00e9tricas de Avalia\u00e7\u00e3o",
    ])
    tax = build_content_taxonomy(
        plan, "", "", strong_headings=[], semantic_profile=None,
        parse_units_from_teaching_plan=_parse_units_from_teaching_plan,
        topic_text=_topic_text, normalize_unit_slug=_normalize_unit_slug)

    slugs = [t["slug"] for u in tax["units"] for t in u["topics"]]
    assert "modelos-preditivos" in slugs, slugs
    assert len(slugs) == 5, slugs


def test_checkbox_markdown_nao_esconde_a_numeracao():
    """Formato COURSE_MAP gerado ("- [ ] **1.1** Topico"): o `[ ]` ficava no
    texto do topico, _NUMBERED_PREFIX_RE nao casava e _finalize_topics achava
    que a unidade nao tinha numerados -- a metodologia ("Uso de projetor")
    sobrevivia como topico (2026-08-20)."""
    plan = "\n".join([
        "### Unidade 01 \u2014 Introdu\u00e7\u00e3o ao estudo de sistemas operacionais",
        "- [ ] **1.1** Evolu\u00e7\u00e3o hist\u00f3rica",
        "- [ ] **1.2** Chamadas de sistema",
        "- [ ] Uso de projetor multim\u00eddia.",
        "- [x] Aulas expositivas nas quais se buscar\u00e1 a participa\u00e7\u00e3o dos alunos.",
    ])
    labels = _labels(plan)
    assert not any("[ ]" in label or "[x]" in label for label in labels), labels
    assert {"1.1", "1.2"} <= _codes(plan)
    assert not any("projetor" in label for label in labels), labels
    assert not any("expositivas" in label for label in labels), labels
