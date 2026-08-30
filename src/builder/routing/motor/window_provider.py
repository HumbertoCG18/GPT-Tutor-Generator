"""WindowProvider: cascata de providers por CONFIABILIDADE (P1 manual > P2 labels).

FASE 0: só P1/P2 (card_block_map). P3 (data-no-nome) e P4 (tópico) = FASE 2.
Retorna janela como lista de refs DISPLAY (bloco-NN). [] = sem janela = funil.
"""
from __future__ import annotations

import re
from typing import List, Tuple

from src.utils.helpers import norm_ascii_lower
from src.builder.timeline.card_block import normalized_card_map
from src.builder.text.normalize import normalize_match_text
from src.builder.routing.motor.disambiguator import block_topic_tokens, block_session_tokens, _GENERIC_STEMS
from src.builder.routing.sequence import extract_lecture_ordinal
from src.builder.timeline.classifier import STRONG_EXAM_RE as _STRONG_EXAM_RE
from src.builder.timeline.classifier import WEAK_EXAM_TOKENS as _TOPIC_EXAM_STEMS
from src.builder.timeline.kinds import NEVER_HOSTS_MATERIAL_KINDS

from src.builder.routing.motor.contracts import MotorContext


def _card_entry(entry: dict, ctx: MotorContext) -> dict:
    """Entrada do card_block_map para a source_section da entry (match sem
    acento/caixa via card_block.normalized_card_map — helper ÚNICO; em
    colisão, o último vence)."""
    key = norm_ascii_lower(str(entry.get("source_section") or ""))
    if not key:
        return {}
    # Card malformado (não-dict) degrada para janela vazia, não crashes.
    if ctx._ncm_cache is None:
        ctx._ncm_cache = normalized_card_map(ctx.card_block_map)
    info = ctx._ncm_cache.get(key)
    return info if isinstance(info, dict) else {}


def _window_for_source(entry: dict, ctx: MotorContext, source: str) -> List[str]:
    info = _card_entry(entry, ctx)
    if str(info.get("source") or "") != source:
        return []
    from src.builder.timeline.card_block import card_entry_block_ids
    return card_entry_block_ids(info, ctx.blocks)  # labels: datas do rotulo mandam (2026-08-25)


def provider_manual(entry: dict, ctx: MotorContext) -> List[str]:
    """P1 — card-window MANUAL (verdade humana)."""
    return _window_for_source(entry, ctx, "manual")


def provider_labels(entry: dict, ctx: MotorContext) -> List[str]:
    """P2 — card_block_map LABELS datado (parse_card_dates A-D)."""
    return _window_for_source(entry, ctx, "labels")


def _modal_years(ctx: MotorContext) -> List[str]:
    """Anos das sessions, mais frequente primeiro (curso pode virar o ano)."""
    if ctx._modal_years_cache is not None:
        return ctx._modal_years_cache
    counts: dict = {}
    for b in ctx.blocks:
        for s in b.get("sessions") or []:
            y = str(s.get("date") or "")[:4]
            if y.isdigit():
                counts[y] = counts.get(y, 0) + 1
    years = sorted(counts, key=lambda y: counts[y], reverse=True)
    ctx._modal_years_cache = years
    return years


def provider_date(entry: dict, ctx: MotorContext) -> List[str]:
    """P3 — DATA-no-nome (DD.MM) -> sessão do cronograma -> bloco (janela ~1).

    0 colisão medida no corpus SO; se uma data cair em 2 blocos a janela
    carrega ambos (honesto — o disambiguator decide)."""
    dm = extract_date_in_name(entry)
    if not dm:
        return []
    dd, mm = dm
    for year in _modal_years(ctx):
        iso = f"{year}-{mm:02d}-{dd:02d}"
        refs = [
            str(b.get("id") or "")
            for b in ctx.blocks
            if any(str(s.get("date") or "") == iso for s in b.get("sessions") or [])
        ]
        refs = [r for r in refs if r]
        if refs:
            return refs
    return []


# P4 — topic-bridge (spec §3 [Δ item 9]; F-TCC: o N ordinal NUNCA vira janela).
_SEMANA_TOPIC_RE = re.compile(r"^\s*semana\s*\d+\s*-\s*(.+)$", re.IGNORECASE)
TOPIC_STEM_LEN: int = 6
TOPIC_MIN_TOKEN: int = 3


# Token DIMENSIONAL ("2d", "3d"): 2 chars, morria no piso 3 nos dois lados. E o unico
# discriminador de "Computacao Grafica 3D" vs "Processo de Visualizacao 2D" (holdout CG
# 2026-08-27). Assinatura propria, no texto cru das sessoes, como o identificador t1/t2.
_DIM_TOKEN_RE = re.compile(r"^\d[a-z]{1,2}$")


def _topic_tokens(topic: str) -> set:
    """Tokens do TÓPICO curado do card: >=3 chars, sem genéricos (+ dimensionais 2d/3d).

    Piso 2 seria no-op: a assinatura do bloco (_toks) tem piso 3 — token
    curto do tópico nunca casa. Se a calibração TCC pedir np/t2, o piso-2
    exige assinatura própria do P4 nos DOIS lados (decisão por número)."""
    out = set()
    for t in normalize_match_text(str(topic or "")).split():
        if (len(t) >= TOPIC_MIN_TOKEN and not t.isdigit() and t[:8] not in _GENERIC_STEMS) or _DIM_TOKEN_RE.match(t):
            out.add(t)
    return out


def _course_stems(ctx: MotorContext) -> set:
    """Stems do NOME DO CURSO: boilerplate dos dois lados do P4. "Computacao Grafica" casava
    "Geometria/Visao COMPUTacional" e levava o card "CG 3D" para 20/08 e 01/09 (CG 2026-08-27).
    O disambiguator ja descartava esses tokens da assinatura; o provider nao."""
    return _stems(_topic_tokens(str(getattr(ctx, "course_name", "") or "")))


def _unit_stems(block: dict) -> set:
    """Stems do unit_slug do bloco ("unidade-08-sintese-de-imagens-realisticas"): o professor
    nomeia cards pela UNIDADE do plano e a linha do cronograma diz outra coisa ("Iluminacao");
    o elo card -> unidade -> blocos da unidade ja existe no DP e o P4 nao olhava (CG 2026-08-27)."""
    slug = str(block.get("unit_slug") or "").replace("-", " ")
    return _stems(_topic_tokens(slug) - {"unidade", "aprendizagem"})


def _stems(tokens: set) -> set:
    return {t[:TOPIC_STEM_LEN] for t in tokens}


# Exam-vocab fraco (par do ruling C1): sozinho não indica EXAME, só quando o
# bloco tem sinal FORTE (STRONG_EXAM_RE) em algum outro lugar do próprio bloco.
# Item 8b (cutover passo 3): vocabulario UNIFICADO no classifier (nomes
# publicos STRONG_EXAM_RE/WEAK_EXAM_TOKENS, importados no topo) — os aliases
# locais _STRONG_EXAM_RE/_TOPIC_EXAM_STEMS preservam o vocabulario deste modulo.


def _block_session_hay(b: dict, ctx: MotorContext) -> str:
    """Texto CRU das sessões do bloco (labels + lessons_index) — a MESMA
    fonte de block_session_tokens (disambiguator.py:63-71), só que não
    tokenizado: _STRONG_EXAM_RE precisa ver "p1"/"p2" etc. inteiros, que o
    piso de 3 chars de _toks descartaria."""
    parts = []
    for sess in b.get("sessions") or []:
        parts.append(str(sess.get("label") or ""))
        topic = ctx.lessons_index.get(str(sess.get("date") or ""))
        if topic:
            parts.append(str(topic))
    return " ".join(parts)


def _block_topic_stems(ctx: MotorContext) -> dict:
    """id(block) -> _stems(assinatura) de TODOS os blocos, memoizado por ctx (item 16).

    Assinatura por bloco e invariante por indice; mesmo padrao de
    ctx._global_df_cache (disambiguator.py:123-132).

    Guard C6 (diagnóstico 2026-08-06, re-flip TCC tentativa 4): rótulo de
    taxonomia rica do bloco (primary_topic_label, ex. "Prova da
    Indecidibilidade...") vaza "prova"/"teste" pro stem-matching do P4 via
    block_topic_tokens mesmo quando o bloco é uma AULA, não um exame. O
    ruling C1 (mesmo par prova/teste) só libera esses tokens do lado TOPIC
    quando o bloco tem sinal FORTE de exame (_STRONG_EXAM_RE) no seu próprio
    texto de sessões; o lado SESSION (block_session_tokens) nunca é
    filtrado — é dele que vêm os 8 membros legítimos da janela real."""
    if ctx._stems_cache is not None:
        return ctx._stems_cache
    cache: dict = {}
    for b in ctx.blocks:
        topic_toks = block_topic_tokens(b)
        if topic_toks & _TOPIC_EXAM_STEMS and not _STRONG_EXAM_RE.search(_block_session_hay(b, ctx)):
            topic_toks = topic_toks - _TOPIC_EXAM_STEMS
        sig = topic_toks | block_session_tokens(b, ctx)
        cache[id(b)] = (_stems(sig) | _unit_stems(b)) - _course_stems(ctx)
    ctx._stems_cache = cache
    return cache


def _session_ordinal_index(ctx: MotorContext) -> dict:
    """ordinal de ENCONTRO (1..N, cronologico) -> ref do bloco que o contem.

    O professor numera "Aula N" por ENCONTRO, nao por bloco: um bloco tematico
    pode agrupar varias aulas (TCC bloco-03 = 3 encontros), entao contar blocos
    desanda o alvo. Memoizado por ctx (mesmo padrao de _block_topic_stems).
    """
    if getattr(ctx, "_session_ordinal_cache", None) is not None:
        return ctx._session_ordinal_cache
    pairs = []
    for b in ctx.blocks:
        if str(b.get("kind") or "") != "class":
            continue
        ref = str(b.get("id") or "")
        if not ref:
            continue
        # Aula de CORRECAO de prova e class para o conteudo (classifier.py:144),
        # mas o professor nao a numera: no TCC "Aula 16" e 15/05, nao o dia da
        # correcao (13/05). Contando-a, o 16o encontro caia na correcao —
        # janela-1, band alta, bloco errado. Medido: 16/19 -> 17/19, 0 regressoes.
        if "correcao" in normalize_match_text(_block_session_hay(b, ctx)):
            continue
        for s in (b.get("sessions") or []) or [{}]:
            pairs.append((str(s.get("date") or ""), ref))
    pairs.sort(key=lambda p: p[0])
    index = {i + 1: ref for i, (_d, ref) in enumerate(pairs)}
    try:
        ctx._session_ordinal_cache = index
    except AttributeError:  # ctx sem slot (fixture minima)
        pass
    return index


def provider_ordinal(entry: dict, ctx: MotorContext) -> List[str]:
    """P3b — ORDINAL-no-nome ("Aula 14") -> N-esimo ENCONTRO -> bloco.

    Depois de DATA (data e mais forte: aponta o dia exato) e antes de TOPICO.
    Medido no TCC: alvo por encontro bate o gold em 16/19; por bloco, 1/19.
    Fora do range de encontros -> sem janela (nunca chuta o ultimo bloco).
    """
    ordinal = extract_lecture_ordinal(normalize_match_text(str(entry.get("title") or "")))
    if ordinal is None:
        ordinal = extract_lecture_ordinal(normalize_match_text(str(entry.get("raw_target") or "")))
    if ordinal is None:
        return []
    ref = _session_ordinal_index(ctx).get(ordinal)
    return [ref] if ref else []


# Identificador de TRABALHO no card e nas sessoes ("Semana 14 - Apresentacoes T2" <->
# "oficina de problemas entrega t2"; "Trabalho T1" <-> "t1 em aula"). Tem 2 chars: o
# piso 3 de _topic_tokens/_toks o descartava nos DOIS lados, e as 5 apresentacoes do
# TCC iam ao llm-funil (gold = a 2a linha "entrega t2"). Assinatura propria, nos dois
# lados, sobre o texto CRU (_block_session_hay). "pN" continua com o prep-prova.
_WORK_ID_RE = re.compile(r"(?:^|[^a-z0-9])((?:tp|t)\d{1,2})(?![a-z0-9])")


def _work_ids(text: str) -> set:
    return set(_WORK_ID_RE.findall(normalize_match_text(str(text or ""))))


def provider_topic(entry: dict, ctx: MotorContext) -> List[str]:
    """P4 — TÓPICO do card ↔ topic_text/sessions[].label.

    Card "Semana N - Tópico" usa o tópico; qualquer outro card usa o NOME
    inteiro (2026-08-25: exigir o prefixo era vício do formato do IA — o card
    "Threads" do SO é tópico puro e o bloco-04 tem "threads" nas sessões;
    sem isto as 3 `exemplo-threads` iam ao funil e o LLM errava). Medido nos
    19 do funil dos 5 cursos: 9 ganham janela, gold dentro em 9/9, 3 viram
    janela-1 certa; cards genéricos ("Informações Gerais", "TDE") não casam
    bloco nenhum e seguem ao funil."""
    sec = str(entry.get("source_section") or "")
    m = _SEMANA_TOPIC_RE.match(sec)
    tstems = _stems(_topic_tokens(m.group(1) if m else sec)) - _course_stems(ctx)
    dims = {t for t in tstems if _DIM_TOKEN_RE.match(t)}
    tstems -= dims
    wids = _work_ids(sec)
    if not tstems and not wids and not dims:
        return []  # card só-ordinal: week-math PROIBIDO -> sem janela
    stems_by_block = _block_topic_stems(ctx)
    refs = []
    for b in ctx.blocks:
        hit = bool(tstems & stems_by_block.get(id(b), set()))
        if not hit and (wids or dims):
            hay = _block_session_hay(b, ctx)
            hit = bool(wids & _work_ids(hay)) or bool(dims & set(normalize_match_text(hay).split()))
        if hit:
            ref = str(b.get("id") or "")
            if ref:
                refs.append(ref)
    if not tstems and not wids and dims and len(refs) == 1:
        # Dimensao SOZINHA ("Exercicios 2D") e escopo, nao aula: com 1 bloco so, e fina demais para
        # forcar janela-1 — vai ao funil (o LLM ve a timeline inteira e acertava). Com >= 2 blocos
        # ("CG 3D" -> 27/10 e 29/10) a janela vale. Mesma etica do ordinal: nunca chuta.
        return []
    return refs


# Cascata em ordem de CONFIABILIDADE. Cada par (fn, nome).
_CASCADE = (
    (provider_manual, "manual"),
    (provider_labels, "labels"),
    (provider_date, "data"),
    (provider_ordinal, "ordinal"),
    (provider_topic, "topic"),
)


def drop_never_hosts(window: List[str], ctx: MotorContext) -> List[str]:
    """Tira da janela os kinds que nunca hospedam material (feriado, atendimento,
    oficina, evento, administrativos — kinds.NEVER_HOSTS_MATERIAL_KINDS). So
    quando sobra algum bloco: janela toda desses kinds fica como esta (o
    disambiguator/funil respondem honestamente)."""
    # Bloco de PROVA tambem nao hospeda material (holdout CG 2026-08-27): nos 5 golds,
    # 0/212 entries tem bloco-verdade `assessment` (provas/listas/gabaritos vivem em
    # review/deliverable). O topic_text da prova e a COBERTURA ("Conteudo: unidade-01,
    # unidade-08...") e casa qualquer card com nome de unidade: na CG 40/70 janelas
    # traziam 2-3 provas e 10 decisoes cairam nelas (P1, P2, G2). Fallback mantido:
    # janela so de provas fica como esta (o funil/disambiguator respondem).
    kept = []
    for ref in window:
        b = ctx.block_by_ref(ref)
        kind = str(b.get("kind") or "") if b is not None else ""
        if b is not None and (kind in NEVER_HOSTS_MATERIAL_KINDS or kind == "assessment"):
            continue
        kept.append(ref)
    return kept or list(window)


def resolve_window(entry: dict, ctx: MotorContext) -> Tuple[List[str], str]:
    """1º provider com janela não-vazia -> (janela, nome_provider). ([], "") = funil.

    A janela sai sem os kinds que nunca hospedam material (medido 2026-08-21:
    0 golds em feriado/atendimento/oficina/evento). Card manual do TCC
    "Semana 12" = [oficina, aula de Cook-Levin]: o slide "Aula 17" e da aula."""
    for fn, name in _CASCADE:
        win = fn(entry, ctx)
        if win:
            return drop_never_hosts(win, ctx), name
    return [], ""


# P3 — data-no-nome (spec §8: extrator DD.MM de title/moodle_label/source_path).
# Reimplementado PURO: o sinal DD.MM legado vive em símbolo condenado do cutover.
# F9 (censo 2026-08-28): Lab SO nomeia "07/08 Slides: ..." (barra) e Lab Redes usa
# o CARD "[03/08] - Introdução" (colchete) — separador aceita ./espaço/barra, "["
# opcional, e o card entra na varredura. Só data no PREFIXO: "Semana 13/04/2026 a
# ..." (cards MF/ES2) segue fora. Falso positivo tipo "Tutorial 1.2" morre no
# calendário — provider_date exige sessão real naquela data.
_DATE_PREFIX_RE = re.compile(r"^\s*\[?\s*(\d{1,2})[./ ](\d{1,2})\b")


def _moodle_label_text(entry: dict) -> str:
    ml = entry.get("moodle_label")
    return ml.get("text", "") if isinstance(ml, dict) else str(ml or "")


def extract_date_in_name(entry: dict):
    """(dd, mm) do PREFIXO de title/moodle_label/card/basename(source_path); None se ausente."""
    basename = re.split(r"[\\/]", str(entry.get("source_path") or ""))[-1]
    for text in (str(entry.get("title") or ""), _moodle_label_text(entry),
                 str(entry.get("source_section") or ""), basename):
        m = _DATE_PREFIX_RE.match(text)
        if not m:
            continue
        dd, mm = int(m.group(1)), int(m.group(2))
        if 1 <= dd <= 31 and 1 <= mm <= 12:
            return dd, mm
    return None
