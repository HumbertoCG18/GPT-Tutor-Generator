"""Rotulos de LEITURA para os artefatos (FILE_MAP, COURSE_MAP, UI).

Compoem numero + nome a partir do que a taxonomia ja guarda separado (`code` e `label`), sem tocar em chave nem em
matching: slug, label e code continuam como estao. Formato pedido pelo user em 07/09/2026:
  unidade   -> "03 - Processamento de Imagens e Visao Computacional"
  subtopico -> "3.5 - Segmentacao"
Sem `code` (planos que nao numeram, como IA e LR) devolve so o nome — nunca inventa numero.
"""
from __future__ import annotations

import re

_UNIT_NUM_RE = re.compile(r"^unidade(?:-de-aprendizagem)?-0*(\d{1,2})(?:$|[^0-9])")
_TITLE_PREFIX_RE = re.compile(r"^\s*unidade(?:\s+de\s+aprendizagem)?\s*\d*\s*[\u2014\u2013:-]?\s*", re.IGNORECASE)


def nome_da_unidade(unit: dict) -> str:
    """Titulo da unidade sem o prefixo "Unidade NN —"."""
    return _TITLE_PREFIX_RE.sub("", str((unit or {}).get("title") or "")).strip()


def numero_da_unidade(unit: dict) -> str:
    """Numero com dois digitos, do slug (que ja e zero-padded); "" quando o slug nao numera."""
    m = _UNIT_NUM_RE.match(str((unit or {}).get("slug") or ""))
    return f"{int(m.group(1)):02d}" if m else ""


def rotulo_unidade(unit: dict) -> str:
    """"03 - Nome" quando ha numero; so o nome quando nao ha."""
    nome = nome_da_unidade(unit)
    num = numero_da_unidade(unit)
    return f"{num} - {nome}" if num and nome else (nome or num)


def rotulo_topico(topic: dict) -> str:
    """"3.5 - Nome" quando ha `code`; so o nome quando nao ha."""
    label = str((topic or {}).get("label") or "").strip()
    code = str((topic or {}).get("code") or "").strip().rstrip(".")
    return f"{code} - {label}" if code and label else (label or code)


def mapa_rotulos(taxonomy: dict) -> tuple:
    """({unit_slug: rotulo}, {topic_slug: rotulo}) para os renderizadores."""
    unidades, topicos = {}, {}
    for u in (taxonomy or {}).get("units") or []:
        slug = str(u.get("slug") or "")
        if slug:
            unidades[slug] = rotulo_unidade(u)
        for t in u.get("topics") or []:
            ts = str(t.get("slug") or "")
            if ts:
                topicos[ts] = rotulo_topico(t)
    return unidades, topicos
