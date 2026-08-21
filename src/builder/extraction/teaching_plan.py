from __future__ import annotations

import re

from src.utils.helpers import slugify

_EM_DASH = "\u2014"
_EN_DASH = "\u2013"
_BULLET = "\u2022"
_DEGREE = "\u00b0"
_MASC_ORD = "\u00ba"
_C_CEDILLA_UPPER = "\u00c7"
_A_TILDE_UPPER = "\u00c3"
_U_ACUTE_UPPER = "\u00da"

_ZERO_WIDTH_TABLE = {ord(ch): None for ch in "​‌‍﻿"}
_LINE_STARTS_NUMBERED = re.compile(r"^[-•*\s]*\d+(?:\.\d+)+\.?\s")
_NUMBERED_ITEM_RE = re.compile(
    r"(?<![\w.])(\d+(?:\.\d+)+)\.?\s+(.+?)(?=\s+\d+(?:\.\d+)+\.?\s+|$)"
)
_NUMBERED_PREFIX_RE = re.compile(r"^\d+(?:\.\d+)+\s")

_TEACHING_PLAN_SECTION_STOP = re.compile(
    rf"^(?:AVALIA[{_C_CEDILLA_UPPER}C][A{_A_TILDE_UPPER}]O|BIBLIOGRAFIA)",
    re.IGNORECASE,
)


def _normalize_teaching_plan_heading(line: str) -> str:
    """Normalize markdown-heavy headings before parser checks.

    Ponto UNICO de normalizacao da linha: todo ramo do parser casa contra a saida
    daqui, nunca contra a linha crua. Zero-width vem colado nos titulos extraidos
    de PDF (visto no plano do TCC) e contamina slug e comparacao.
    """
    normalized = (line or "").strip()
    normalized = normalized.translate(_ZERO_WIDTH_TABLE)
    normalized = re.sub(r"^#+\s*", "", normalized)
    normalized = normalized.replace("*", "").strip()
    # Checkbox markdown ("- [ ] 1.1 Topico", formato do COURSE_MAP gerado): o
    # `[ ]` ficava no texto, _NUMBERED_PREFIX_RE nao casava e _finalize_topics
    # nao via numerado nenhum -- a metodologia sobrevivia como topico.
    normalized = re.sub(rf"^([-{_BULLET}*]\s+)\[[ xX]\]\s*", r"\1", normalized)
    return normalized


def _split_numbered_items(line: str) -> list:
    """[(codigo, texto)] de UMA linha. A extracao de PDF cola varios itens numa
    linha so ("4.6.1 Definicao da Classe 4.6.2 Exemplos ..."), entao um item por
    linha perde o resto. Ponto final apos o codigo e opcional (ES2 nao usa)."""
    if not _LINE_STARTS_NUMBERED.match(line or ""):
        return []
    items = []
    for match in _NUMBERED_ITEM_RE.finditer(line):
        text = match.group(2).strip(" .")
        if text:
            items.append((match.group(1), text))
    return items


def _finalize_topics(topics: list) -> list:
    """Numerado presente => bullets sem numero sao metodologia ("Uso de projetor
    multimidia"), nao conteudo. Unidade sem numeracao nenhuma (formato IA) mantem
    tudo, que la os topicos vem em linha solta."""
    numbered = [topic for topic in topics if _NUMBERED_PREFIX_RE.match(str(topic[0]))]
    return numbered or topics


def _parse_units_from_teaching_plan(text: str):
    """
    Extrai (titulo_da_unidade, [topicos]) do texto livre do plano de ensino.

    Cada topico retorna como `(texto, depth)`:
    - depth 0 -> topico principal
    - depth 1+ -> subtopicos numerados
    """
    units: list = []
    current_title = None
    current_unit_num = None
    current_topics: list = []
    current_style = None

    pucrs_unit_re = re.compile(
        rf"N\s*[{_DEGREE}{_MASC_ORD}]?\s*\.?\s*DA\s+UNIDADE\s*:\s*(\d+)",
        re.IGNORECASE,
    )
    pucrs_content_re = re.compile(
        rf"CONTE[{_U_ACUTE_UPPER}{_DEGREE}U]DO\s*:\s*(.+)",
        re.IGNORECASE,
    )
    generic_unit_re = re.compile(
        rf"^(?:#{{0,4}}\s*)?(unidade(?:\s+de\s+aprendizagem)?\s+(?:\d+|[ivxlcdm]+))\s*[-{_EN_DASH}:{_EM_DASH}]\s*(.+)",
        re.IGNORECASE,
    )
    bullet_topic_re = re.compile(rf"^[-{_BULLET}*]\s+(.+)")

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue

        normalized_line = _normalize_teaching_plan_heading(line)
        if _TEACHING_PLAN_SECTION_STOP.match(normalized_line):
            # Parar só se já encontramos unidades ou estamos dentro de uma unidade;
            # caso contrário, alguns documentos têm "PROCEDIMENTOS" antes das unidades.
            if units or current_title is not None:
                break
            continue

        m = pucrs_unit_re.match(normalized_line)
        if m:
            if current_title is not None:
                units.append((current_title, _finalize_topics(current_topics)))
            current_unit_num = m.group(1)
            current_topics = []
            current_style = "pucrs"
            # Conteúdo pode estar na mesma linha — inclusive depois de "N°. DE HORAS":
            # "N°. DA UNIDADE: 07 N°. DE HORAS: 10% CONTEÚDO: Gerência de E/S"
            rest = normalized_line[m.end():].strip()
            mc = pucrs_content_re.search(rest)
            current_title = f"Unidade {current_unit_num} {_EM_DASH} {mc.group(1).strip()}" if mc else None
            continue

        if current_unit_num is not None and current_title is None:
            m = pucrs_content_re.match(normalized_line)
            if m:
                current_title = f"Unidade {current_unit_num} {_EM_DASH} {m.group(1).strip()}"
                continue

        m = generic_unit_re.match(normalized_line)
        if m:
            if current_title is not None:
                units.append((current_title, _finalize_topics(current_topics)))
            current_title = f"{m.group(1).strip()} {_EM_DASH} {m.group(2).strip()}"
            current_unit_num = None
            current_topics = []
            current_style = "learning_unit" if "aprendizagem" in m.group(1).lower() else "generic"
            continue

        if current_title is not None:
            items = _split_numbered_items(normalized_line)
            if items:
                # O codigo fica NO TEXTO: content_taxonomy chama _extract_topic_code
                # sobre ele e so pula o filtro de known_tools quando acha codigo.
                for code, label in items:
                    current_topics.append((f"{code} {label}", max(code.count(".") - 1, 0)))
                continue
            m = bullet_topic_re.match(normalized_line)
            if m:
                current_topics.append((m.group(1).strip(), 0))
                continue
            if current_style == "learning_unit" and not normalized_line.endswith(":"):
                current_topics.append((normalized_line, 0))

    if current_title is not None:
        units.append((current_title, _finalize_topics(current_topics)))

    return units


def _topic_text(topic) -> str:
    """Texto de um topico: tupla (text, depth) do parser, dict da taxonomia, ou
    string legada.

    O ramo do dict e obrigatorio: `build_content_taxonomy` devolve cada topico como
    {code, slug, label, aliases, kind, unit_slug} e, sem ele, o `str(topic)`
    serializava o dict inteiro dentro de `topic_phrases`
    (`build_file_map_unit_index`) — os pesos de FRASE do scorer de unidade nunca
    casavam e o lixo estrutural virava token.
    """
    if isinstance(topic, tuple):
        return topic[0]
    if isinstance(topic, dict):
        label = str(topic.get("label") or "").strip()
        if label:
            return label
        return str(topic.get("slug") or "").replace("-", " ").strip()
    return str(topic)


def _topic_depth(topic) -> int:
    """Extrai a profundidade de um topico, seja tupla (text, depth) ou string legada."""
    if isinstance(topic, tuple):
        return topic[1]
    return 0


def _parse_bibliography_from_teaching_plan(text: str) -> dict:
    """
    Extrai referências bibliográficas do texto do plano de ensino.
    Detecta seção BIBLIOGRAFIA com sub-seções BÁSICA e COMPLEMENTAR.
    Retorna {"basica": [str, ...], "complementar": [str, ...]}.
    """
    result: dict = {"basica": [], "complementar": []}

    bib_match = re.search(r"^BIBLIOGRAFIA", text, re.MULTILINE | re.IGNORECASE)
    if not bib_match:
        return result

    bib_text = text[bib_match.start():]
    current_section = None
    current_ref = None
    ref_start_re = re.compile(r"^\d+\.\s+(.+)")

    def _flush():
        if current_ref and current_section:
            result[current_section].append(current_ref.strip())

    for raw in bib_text.splitlines():
        line = raw.strip()

        if re.match(r"^B[ÁA]SICA\s*:", line, re.IGNORECASE):
            _flush()
            current_ref = None
            current_section = "basica"
            continue

        if re.match(r"^COMPLEMENTAR\s*:", line, re.IGNORECASE):
            _flush()
            current_ref = None
            current_section = "complementar"
            continue

        if not current_section:
            continue

        if not line:
            _flush()
            current_ref = None
            continue

        m = ref_start_re.match(line)
        if m:
            _flush()
            current_ref = m.group(1).strip()
        elif current_ref is not None:
            current_ref += " " + line

    _flush()
    return result


def _normalize_unit_slug(title: str) -> str:
    # Percentual de carga horária no título (caso real IA: "Visão Geral (5%)")
    # não é identidade da unidade — fora do slug, senão vira sufixo numérico
    # ("visao-geral-5") e muda junto com a carga.
    clean = re.sub(r"\(\s*\d+(?:[.,]\d+)?\s*%\s*\)", " ", title or "")
    slug = slugify(clean.replace(_EM_DASH, "-"))
    match = re.match(r"^(unidade(?:-de-aprendizagem)?-)(\d+)(-.+)?$", slug)
    if not match:
        return slug
    prefix, number, suffix = match.groups()
    suffix = suffix or ""
    return f"{prefix}{int(number):02d}{suffix}"
