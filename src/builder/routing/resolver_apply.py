"""Helper compartilhado: montagem de inputs + aplicação do concept resolver.

Usado por produção (pedagogical_regeneration, atrás de flag) e pelo harness
(compare_resolver), eliminando duplicação da lógica de montagem de signals.

Por que aqui e não em engine.py: lógica de routing pertence ao pacote routing;
engine.py é reservado para orquestração de alto nível (non-negotiable do projeto).
"""
from __future__ import annotations

import copy
import re
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import List, Optional, Tuple

from src.builder.artifacts.navigation import _entry_markdown_text_for_file_map
from src.builder.extraction.content_taxonomy import _NO_TIMELINE_CATEGORIES
from src.builder.extraction.entry_signals import collect_entry_unit_signals
from src.builder.text.normalize import normalize_match_text
from src.builder.routing.concept_resolver import resolve_material_assignment
from src.builder.routing.revisar import revisar_de
from src.builder.routing.sequence import annotate_class_ordinals
from src.builder.timeline.card_block import resolve_block_ref
from src.utils.helpers import collapse_ws as _collapse_ws_cat
from src.models.core import moodle_label_text  # leitor unico (07/09)


def _display_id_for_block(block_id: str, blocks: List[dict]) -> str:
    """Resolve um block_id (uuid OU bloco-NN legado) ao seu display id (bloco-NN).

    A tag bloco: DEVE permanecer display (file_map.py:506 parseia bloco-(\\d+)).
    Se block_id é uuid, encontra o bloco e devolve seu id; senão (já é display
    ou não resolve), devolve block_id intacto.
    """
    bid = str(block_id or "").strip()
    if not bid:
        return ""
    for b in blocks:
        if str(b.get("block_uuid") or "") == bid:
            return str(b.get("id") or bid)
    return bid


def _is_material(entry: dict) -> bool:
    """Mesmo predicado do harness compare_resolver."""
    return str(entry.get("file_type") or "") == "pdf" or bool(entry.get("category"))


def load_lessons_index(root: Optional[Path]) -> Optional[dict]:
    """Carrega course/.lessons_index.json (índice course-level data->tópico).

    INFRA (não consumida ainda): a captação (build_lesson_topic_index no import)
    está ativa, mas o termo de fusão por lesson foi REVERTIDO — casar o tópico da
    aula contra os `concepts` ruidosos do Gemini regredia o gold (11->10). Será
    consumida pela alavanca 1, quando o `moodle_label` der a identidade LIMPA do
    material pra casar contra a lesson. Ausente/inválido -> None (degradação honesta).
    """
    if root is None:
        return None
    path = Path(root) / "course" / ".lessons_index.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None
    return data if isinstance(data, dict) else None


def assemble_resolver_inputs(
    root: Optional[Path],
    entry: dict,
    code_curation: dict,
) -> Tuple[dict, dict, dict]:
    """Monta os três inputs que resolve_material_assignment precisa.

    Fiel ao harness compare_resolver (compare_repo:124-145): markdown cru,
    signals via collect_entry_unit_signals, summary da curation, e injeção
    de entry["concepts"] apenas quando summary.concepts existe.

    Retorna (entry_for_resolver, signals, summary).
    summary é {} quando ausente — passa como llm_curation=None ao resolver.
    """
    entry_id = str(entry.get("id") or "")
    rec = (code_curation.get("entries") or {}).get(entry_id) or {}
    summary_raw = rec.get("summary")
    summary: dict = summary_raw if isinstance(summary_raw, dict) else {}

    markdown = _entry_markdown_text_for_file_map(root, entry) if root is not None else ""
    signals = collect_entry_unit_signals(entry, markdown or "")

    entry_for_resolver = dict(entry)
    if summary.get("concepts"):
        entry_for_resolver["concepts"] = summary["concepts"]

    return entry_for_resolver, signals, summary


def apply_concept_resolver(
    entries: list,
    blocks: List[dict],
    units: List[dict],
    code_curation: dict,
    root: Optional[Path],
) -> list:
    """Aplica o resolver sobre os entries materiais, sobrescrevendo APENAS campos
    de bloco (computed_block_id, band, method, confidence + tag bloco: em auto_tags).

    Unit fields (computed_unit_slug, unit:/subunit: em auto_tags) ficam intocados —
    BLOCK-only cutover (Fase 3.3; a unidade é Fase 4).

    Cutover passo 3: o motor é o atribuidor ÚNICO — semeia entries novos (sem
    computed_block_id) e re-resolve os existentes. Categorias fora da timeline
    (_NO_TIMELINE_CATEGORIES) são LIMPAS e puladas — porte da limpeza B1 do
    funil legado (resolve_unit_block_tags, content_taxonomy), morto neste passo.

    Idêntico ao harness: faz annotate_class_ordinals numa cópia dos blocks antes
    de resolver (o harness também faz isso antes do loop). Muta entries in-place.
    """
    blocks = annotate_class_ordinals(copy.deepcopy(blocks))
    lessons_index = load_lessons_index(root)

    for entry in entries:
        if not _is_material(entry):
            continue
        category = _collapse_ws_cat(str(entry.get("category") or "")).lower()
        if category in _NO_TIMELINE_CATEGORIES:
            # Categoria fora da timeline: limpa atribuicao antiga (senao um
            # manifest com historico carrega bloco orfao — caso real do B1).
            for k in ("computed_block_id", "computed_block_confidence",
                      "computed_block_band", "computed_block_method"):
                entry.pop(k, None)
            if entry.get("auto_tags"):
                entry["auto_tags"] = [t for t in entry["auto_tags"] if not str(t).startswith("bloco:")]
            continue

        entry_for_resolver, signals, summary = assemble_resolver_inputs(root, entry, code_curation)
        assignment = resolve_material_assignment(
            entry_for_resolver,
            blocks,
            units,
            signals=signals,
            llm_curation=summary or None,
            lessons_index=lessons_index,
        )

        # Sobrescreve SÓ campos de bloco. computed_block_id é uuid (join interno):
        # resolve_block_ref faz passthrough se já-uuid e mapeia bloco-NN legado
        # (compat enquanto o resolver ainda retorna display id — migra na Task 4).
        _raw_block_id = assignment["block_id"]
        _uuid_block_id = resolve_block_ref(_raw_block_id, blocks) or _raw_block_id
        entry["computed_block_id"] = _uuid_block_id
        entry["computed_block_confidence"] = assignment["confidence"]
        entry["computed_block_band"] = assignment["band"]
        entry["computed_block_method"] = assignment["method"]

        # Mirror de tag: troca bloco:<old> por bloco:<new> em auto_tags
        # (mesma mecânica de pedagogical_regeneration.py:110-112). A tag DEVE
        # continuar display (bloco-NN) — resolve uuid->display antes de montar.
        new_block_id = _display_id_for_block(_uuid_block_id, blocks)
        tags = [t for t in (entry.get("auto_tags") or []) if not str(t).startswith("bloco:")]
        if new_block_id:
            tags.append(f"bloco:{new_block_id}")
        entry["auto_tags"] = tags

    return entries


_PROPAG_REASON = "propagado-headings"
_DECOMP_REASON = "rotulo-decomposto"
_TITULO_REASON = "titulo-nomeia-subtopico"
_SECAO_REASON = "secao-nomeia-subtopico"
from src.builder.text.patterns import SECTION_NUM_PREFIX_RE as _SECAO_NUM_RE  # regex unica (07/09)


def _tokens_headings(signals: dict, generic_stems) -> set:
    txt = f"{signals.get('markdown_headings_text', '')} {signals.get('title_text', '')}"
    return {t for t in txt.split() if len(t) >= 4 and not any(t.startswith(s) for s in generic_stems)}


def _partes_de_rotulo(units: dict, passe1: list, df_max: float) -> dict:
    """Subunidade, 2a fonte de aliases da 2a passada (2026-09-06). O plano nomeia o subtopico por uma FRASE
    composta ('Bezier e Algoritmo de Casteljau', 'Algoritmos de Geometria Computacional') e o material nomeia a
    parte ('bezier-cpp'); o scorer casa frases inteiras, entao a parte sozinha valia 0. Cada parte do rotulo
    (`timeline.index._label_parts`) vira alias do proprio topico se: tem token especifico; nao nomeia mais nada
    no curso (nao esta contida no rotulo/aliases de outro topico nem no titulo de uma unidade — sem isso 'saida'
    de "Dispositivos de entrada e saida" no SO e 'Internet' do rotulo-aspirador do FR viravam aliases); e aparece
    em <= df_max dos materiais (mesmo teto da propagacao: 'internet' num curso de redes nao discrimina).
    Medido em memoria pela 1a passada nos 6 golds (233): +9 -1; entra pela 2a passada (so onde a 1a nao decidiu),
    o que preserva a decisao confiante. Devolve {(unit_slug, topic_slug): {partes}}."""
    from src.builder.timeline.index import _label_parts, _specific_tokens
    heads: Counter = Counter()
    todos = [(str(u.get("slug") or ""), t) for u in units.values() for t in (u.get("topics") or [])]
    for _, t in todos:
        m = re.match(r"^(\w+)\s+(de|da|do|das|dos|para|em)\s+", str(t.get("label") or ""), re.I)
        if m:
            heads[normalize_match_text(m.group(1))] += 1
    generic_heads = {h for h, n in heads.items() if n >= 2}
    vocab = {id(t): {normalize_match_text(x) for x in [str(t.get("label") or "")] + list(t.get("aliases") or [])} for _, t in todos}
    titulos = " | ".join(normalize_match_text(str(u.get("title") or "")) for u in units.values())
    textos = [normalize_match_text(texto or "") for _, texto, _, _ in passe1]
    out: dict = defaultdict(set)
    for unit_slug, t in todos:
        outros = " | ".join(x for _, o in todos if o is not t for x in vocab[id(o)])
        for part in _label_parts(str(t.get("label") or ""), generic_heads):
            n = normalize_match_text(part)
            if not n or n in vocab[id(t)] or not _specific_tokens(part):
                continue
            pat = r"(^|\s)" + re.escape(n) + r"(\s|$)"
            if re.search(pat, outros) or re.search(pat, titulos):
                continue
            if sum(1 for x in textos if n in x) > df_max * max(1, len(textos)):
                continue
            out[(unit_slug, str(t.get("slug") or ""))].add(part)
            vocab[id(t)].add(n)
    return out


def _frase_no_texto(texto_norm: str, frase: str) -> bool:
    n = normalize_match_text(frase or "")
    return bool(n) and re.search(r"(^|\s)" + re.escape(n) + r"(\s|$)", texto_norm) is not None


def _subtopico_nomeado_no_titulo(entry: dict, unit_slug: str, vencedor: str, partes: dict, frases_topico: dict) -> str:
    """Subtopico Y (!= vencedor, mesma unidade) cuja parte de rotulo esta no titulo + label do Moodle do material,
    desde que nenhuma frase (rotulo/aliases) do vencedor esteja no titulo e Y seja unico. "" se nao houver."""
    ml = moodle_label_text(entry)
    tit = normalize_match_text(f"{entry.get('title') or ''} {ml or ''}")
    if not tit:
        return ""
    cand = [y for (u, y), ps in partes.items() if u == unit_slug and y != vencedor and any(_frase_no_texto(tit, p) for p in ps)]
    if len(cand) != 1 or any(_frase_no_texto(tit, f) for f in frases_topico.get(vencedor, [])):
        return ""
    return cand[0]


def _secao_nomeia_subtopico(entry: dict, topicos_da_unidade: list, generic_stems) -> str:
    """Subtopico que a SECAO do Moodle do material nomeia, se for exatamente um (06/09; oraculo: a secao "Curvas
    Parametricas" do CG nomeia o subtopico). 'Nomeia' = rotulo/alias contido na secao ou secao contida nele (palavra
    inteira), ou os tokens especificos de um contidos nos do outro (fora genericos do motor e do curso). "" se 0 ou 2+."""
    sec = normalize_match_text(_SECAO_NUM_RE.sub("", str(entry.get("source_section") or "")))
    if not sec:
        return ""
    def _toks(text: str, generic: set) -> set:
        return {t for t in normalize_match_text(text).split() if len(t) >= 4 and t not in generic
                and not any(t.startswith(g) for g in generic_stems)}
    hits = []
    for t in topicos_da_unidade:
        generic = set(t.get("generic_tokens") or [])
        frases = [normalize_match_text(x) for x in [t.get("topic_label") or ""] + list(t.get("aliases") or [])]
        if any(f and (_frase_no_texto(sec, f) or _frase_no_texto(f, sec)) for f in frases):
            hits.append(t["topic_slug"])
            continue
        st, lt = _toks(sec, generic), _toks(t.get("topic_label") or "", generic)
        if st and lt and (st <= lt or lt <= st):
            hits.append(t["topic_slug"])
    return hits[0] if len(hits) == 1 else ""


def propagar_vocabulario_por_headings(passe1: list, content_taxonomy: dict, auto_map_entry_subtopic_fn, *,
                                      conf_min: float, min_entries: int, df_max: float) -> int:
    """2a passada da subunidade (sessao 6, 2026-09-05). Token EXCLUSIVO dos headings/titulo dos materiais
    que a 1a passada atribuiu com confianca a um subtopico vira alias desse subtopico; so os materiais em
    que a 1a passada NAO decidiu (vazio, ambiguo ou conf < conf_min) sao repontuados. O plano nomeia
    categorias e o material nomeia algoritmos ("Modelos Preditivos" <- perceptron, rede neural); sem isto
    esse vocabulario so existia por glossario manual (IA). Medido nos 6 golds (233): +5 -0, FR/LR 0.
    Salvaguardas, cada uma medida: sem stems genericos do motor ('exemplo'/'respostas' viravam alias e
    derrubavam CG slab e MF respostas), df <= df_max dos materiais ('sumario'/'aula' do TCC), >= min_entries
    confiantes, exclusivo de UM subtopico da unidade, e nunca sobre decisao confiante (o CG perdia 8).
    Devolve quantos materiais mudaram."""
    from src.builder.text.stopwords import MOTOR_GENERIC_STEMS as _GENERIC_STEMS
    from src.builder.routing.thresholds import T
    units = {str(u.get("slug") or ""): u for u in (content_taxonomy or {}).get("units", []) or []}
    if not units or not passe1:
        return 0
    toks_by_entry: dict = {}
    df: Counter = Counter()
    for entry, texto, unit_slug, match in passe1:
        toks = _tokens_headings(collect_entry_unit_signals(entry, texto), _GENERIC_STEMS)
        toks_by_entry[id(entry)] = toks
        df.update(toks)
    vocab_unit = {}
    for slug, u in units.items():
        parts = [str(u.get("title") or "")] + [f"{t.get('label', '')} {' '.join(t.get('aliases') or [])}"
                                                for t in (u.get("topics") or [])]
        vocab_unit[slug] = {x for x in normalize_match_text(" ".join(parts)).split() if len(x) >= 4}
    owners: dict = defaultdict(lambda: defaultdict(set))
    n_conf: Counter = Counter()
    for entry, texto, unit_slug, match in passe1:
        if not match or not match.topic_slug or match.ambiguous or match.confidence < conf_min:
            continue
        for tok in toks_by_entry[id(entry)] - vocab_unit.get(unit_slug, set()):
            if df[tok] > df_max * len(passe1):
                continue
            owners[unit_slug][tok].add(match.topic_slug)
            n_conf[(unit_slug, match.topic_slug, tok)] += 1
    extra: dict = defaultdict(set)
    for unit_slug, toks in owners.items():
        for tok, subs in toks.items():
            if len(subs) == 1 and n_conf[(unit_slug, next(iter(subs)), tok)] >= min_entries:
                extra[(unit_slug, next(iter(subs)))].add(tok)
    partes = _partes_de_rotulo(units, passe1, df_max)   # 2a fonte (06/09): partes do rotulo composto do plano
    for key, ps in partes.items():
        extra[key] |= ps
    # (sem `if not extra: return 0`: a regra do titulo e a da secao, abaixo, valem mesmo sem alias novo)
    tax = copy.deepcopy(content_taxonomy)
    for u in tax.get("units", []) or []:
        for t in u.get("topics") or []:
            add = extra.get((str(u.get("slug") or ""), str(t.get("slug") or "")))
            if add:
                t["aliases"] = list(t.get("aliases") or []) + sorted(add)
    mudou = 0
    frases_topico = {str(t.get("slug") or ""): [str(t.get("label") or "")] + list(t.get("aliases") or [])
                     for u in units.values() for t in (u.get("topics") or [])}
    decididos_na_2a: set = set()
    for entry, texto, unit_slug, match in passe1:
        if match and match.topic_slug and not match.ambiguous and match.confidence >= conf_min:
            # Decisao confiante da 1a passada so cai quando o TITULO do material nomeia outro subtopico da unidade por
            # uma parte do rotulo e NAO nomeia o vencedor (06/09, `simula_titulo_confiante.py`: +2 -0 nos 6 golds; CG
            # "Exercicios de geometria computacional" ia para `entidades-geometricas` por 'Vetor/Pontos/Retas' no corpo).
            y = _subtopico_nomeado_no_titulo(entry, unit_slug, str(match.topic_slug), partes, frases_topico)
            if y:
                entry["computed_subunit_slug"] = y
                entry["subunit_match_reasons"] = list(match.reasons) + [_TITULO_REASON]
                tags = [t for t in (entry.get("auto_tags") or []) if not str(t).startswith("subunit:")]
                entry["auto_tags"] = tags + [f"subunit:{y}"]
                mudou += 1
            continue  # fora isso, decisao confiante da 1a passada nunca e sobreposta
        novo = auto_map_entry_subtopic_fn(entry, tax, texto, winning_unit_slug=unit_slug)
        slug_novo = str(getattr(novo, "topic_slug", "") or "")
        slug_ant = str(getattr(match, "topic_slug", "") or "") if match else ""
        if not slug_novo or (slug_novo == slug_ant and float(novo.confidence) <= float(match.confidence)):
            continue
        entry["computed_subunit_slug"] = slug_novo
        texto_norm = normalize_match_text(texto or "")
        por_parte = any(normalize_match_text(p) in texto_norm for p in partes.get((unit_slug, slug_novo), ()))
        entry["subunit_match_reasons"] = list(novo.reasons) + [_DECOMP_REASON if por_parte else _PROPAG_REASON]
        entry["subunit_match_confidence"] = float(novo.confidence)
        tags = [t for t in (entry.get("auto_tags") or []) if not str(t).startswith("subunit:")]
        if not novo.ambiguous and float(novo.confidence) >= T.SUBUNIT_TAG:
            tags.append(f"subunit:{slug_novo}")
        entry["auto_tags"] = tags
        decididos_na_2a.add(id(entry))
        mudou += 1
    # Ultimo recurso (06/09, S1b): onde NEM a 1a NEM a 2a passada decidiram (vazia ou empatada), a SECAO do Moodle que
    # nomeia exatamente um subtopico da unidade decide. Medido pela rota real nos 6 golds: +3 -0 (MF exemplos-zip, CG intro,
    # CG curvasparametricas). Versoes mais agressivas (sobrepor a 2a passada: +5 -3; sobrepor decisao confiante: +5 -13)
    # REFUTADAS: a secao do professor nomeia o pai quando o gold quer o filho (z-buffer, k-nn, escalonamento).
    from src.builder.timeline.index import _iter_content_taxonomy_topics
    por_unidade: dict = defaultdict(list)
    for t in _iter_content_taxonomy_topics(content_taxonomy) or []:
        por_unidade[str(t.get("unit_slug") or "")].append(t)
    for entry, texto, unit_slug, match in passe1:
        reasons = [str(r) for r in (entry.get("subunit_match_reasons") or [])]
        indecisa_2a = any(r == "ambiguous" or r.startswith("empate-exato") for r in reasons)
        indecisa_1a = id(entry) not in decididos_na_2a and (not match or not match.topic_slug or match.ambiguous)
        if entry.get("computed_subunit_slug") and not indecisa_2a and not indecisa_1a:
            continue
        y = _secao_nomeia_subtopico(entry, por_unidade.get(unit_slug, []), _GENERIC_STEMS)
        if not y or y == str(entry.get("computed_subunit_slug") or ""):
            continue
        entry["computed_subunit_slug"] = y
        entry["subunit_match_reasons"] = [r for r in reasons if r != "ambiguous" and not r.startswith("empate-exato")] + [_SECAO_REASON]
        entry["subunit_match_confidence"] = float(conf_min)
        tags = [t for t in (entry.get("auto_tags") or []) if not str(t).startswith("subunit:")]
        entry["auto_tags"] = tags + [f"subunit:{y}"]
        mudou += 1
    return mudou


def apply_unit_subunit_fields(
    entries: list,
    blocks: List[dict],
    course_meta: dict,
    subject_profile,
    root: Optional[Path],
    code_curation: dict,
    *,
    auto_map_entry_unit_fn,
    auto_map_entry_subtopic_fn,
    build_file_map_unit_index_from_course_fn,
    iter_content_taxonomy_topics_fn,
    entry_markdown_text_for_file_map_fn,
) -> list:
    """Fase 4 do cutover: unit/subunit no caminho do motor.

    Roda DEPOIS de apply_concept_resolver, sob a mesma flag: recomputa a
    unidade com o scorer sobrevivente e reconcilia contra o bloco que o
    motor acabou de gravar (fecha o gap 1.2 para os campos de unidade).
    Só toca entries que o motor decidiu (material + computed_block_id).
    """
    from src.builder.routing.file_map import (
        reconcile_unit_with_block, resolve_temporal_block, unit_of_block_or_neighbor,
    )
    from src.builder.routing.thresholds import T
    from src.models.tag_profile import build_learned_unit_boosts, load_tag_profile
    from src.utils.helpers import collapse_ws as _collapse_ws

    unit_index = build_file_map_unit_index_from_course_fn(course_meta, subject_profile)
    content_taxonomy = (
        course_meta.get("_content_taxonomy")
        or course_meta.get("_content_taxonomy_for_tests")
        or {}
    )
    if not content_taxonomy and course_meta.get("_repo_root"):
        from src.builder.extraction.content_taxonomy import load_internal_content_taxonomy
        content_taxonomy = load_internal_content_taxonomy(course_meta["_repo_root"])
    topic_index = iter_content_taxonomy_topics_fn(content_taxonomy)
    passe1: list = []   # (entry, texto, unidade, TopicMatchResult) da rota automatica, para a 2a passada

    tag_profile = None
    if root:
        try:
            tag_profile = load_tag_profile(Path(root) / "course")
        except Exception:
            tag_profile = None

    for entry in entries:
        if not _is_material(entry):
            continue
        block_id = str(entry.get("computed_block_id") or "").strip()
        if not block_id and not str(entry.get("temporal_block_id") or "").strip():
            # Bibliografia/referencias/cronograma sao limpas do BLOCO de proposito
            # (`apply_concept_resolver`): nao foram "dadas" numa aula, nao tem eixo
            # temporal. Mas TEM eixo de cobertura — sao material bibliografico DE
            # alguma unidade, e o proprio gold ja as rotula (as laminas de sockets
            # do SO estao em `coverage_gt_SO.csv` como u03, provenance=plano-de-
            # ensino). Sem bloco, `reconcile_unit_with_block` devolve a unidade do
            # scorer intacta (file_map.py:722), entao passar por aqui e seguro.
            # Medido 2026-08-19: 14 entries nesta situacao nos 5 cursos, 6 passam
            # a acertar e NENHUMA passa a errar (as outras 8 morrem no gate).
            categoria = _collapse_ws_cat(str(entry.get("category") or "")).lower()
            if categoria not in _NO_TIMELINE_CATEGORIES:
                continue

        markdown_text = entry_markdown_text_for_file_map_fn(root, entry) if root is not None else ""

        # Zip/codigo nao tem .md: o unico sinal e o resumo do Gemini em
        # `code_curation.json`. O BLOCO ja recebe (`entry["concepts"]`, linha 90)
        # e a SUBUNIDADE tambem (`sub_md` abaixo) — a UNIDADE era a unica cega,
        # decidindo com texto vazio para 25 de 233 materiais dos 5 cursos (11%),
        # entre eles `colecoes-*` e `classes-parte1` do MF, que viviam no balde
        # de erro. Medido 2026-08-19: 129 -> 133 acertos, nenhum curso regride.
        code_rec = (code_curation.get("entries") or {}).get(str(entry.get("id") or "")) or {}
        texto_para_unidade = markdown_text
        if code_rec:
            from src.builder.core.code_summarization import code_curation_signal_text
            resumo = code_curation_signal_text(code_rec)
            if resumo:
                texto_para_unidade = f"{markdown_text}\n\n{resumo}" if markdown_text else resumo

        manual_unit = _collapse_ws(str(entry.get("manual_unit_slug") or ""))
        section_unit = ""
        if manual_unit:
            resolved_unit_slug, unit_confidence = manual_unit, 1.0
            unit_ambiguous, unit_reasons = False, ["manual"]
        else:
            learned = build_learned_unit_boosts(tag_profile, entry) if tag_profile else {}
            match = auto_map_entry_unit_fn(
                entry, unit_index, texto_para_unidade, topic_index,
                learned_unit_boosts=learned,
            )
            resolved_unit_slug = match.slug
            unit_confidence = match.confidence
            unit_ambiguous = match.ambiguous
            unit_reasons = list(match.reasons)
            # #47: a secao so vale corroborada pelo vencedor BRUTO do texto (antes do gate).
            # Sem isso, medido: troca a unidade de uma aula do TCC e perde a subunidade.
            secao = str(getattr(match, "section_slug", "") or "")
            if secao and not unit_ambiguous and secao == resolved_unit_slug:
                section_unit = secao

        gated_unit = resolved_unit_slug if (not unit_ambiguous and unit_confidence >= T.UNIT_TAG) else ""

        # Eixo de COBERTURA (N unidades), separado do 1:1 acima. Prova, lista,
        # plano de ensino e serie de laboratorio cobrem mais de uma unidade —
        # forcar uma so e o erro de cardinalidade que travava a medicao.
        from src.builder.routing.coverage_rules import META_COVERAGE_RULES, derive_coverage_units
        from src.builder.text.normalize import normalize_match_text as _norm_cov
        cobertura = derive_coverage_units(
            entry, unit_index, texto_para_unidade,
            normalize=lambda t: _norm_cov(t, keep="+-./"),
            fallback_unit_slug=gated_unit,
            topic_index=topic_index,
            blocks=blocks,
        )
        if cobertura:
            entry["coverage_units"] = cobertura
        else:
            entry.pop("coverage_units", None)

        # 2026-08-21: o bloco que manda na unidade e o TEMPORAL (ancora:
        # manual > temporal_block_id > computed), o mesmo que a regua mede —
        # nao o computed_block_id do scorer de conceito. Esta fase roda DEPOIS
        # da camada temporal (pedagogical_regeneration) justamente para ve-lo.
        # Bloco sem unit_slug (avaliacao/revisao/overview) herda do vizinho de
        # conteudo. Medido: scorer 130/188 -> bloco temporal + heranca 178/188.
        temporal_id = resolve_temporal_block(entry, blocks)
        block_unit, vizinho = unit_of_block_or_neighbor(temporal_id, blocks)
        blk = next((b for b in blocks
                    if str(b.get("id") or "") == temporal_id or str(b.get("block_uuid") or "") == temporal_id), None)
        block_ref = str((blk or {}).get("id") or temporal_id or block_id)

        # Pino manual direto do entry: computed_block_method pode ter sido
        # trocado p/ consensus/llm_only pelo attach ANTES deste apply — o
        # method nao e prova de pino (review final F4, I2).
        _pin = str(entry.get("manual_timeline_block_id") or "").strip()
        block_is_manual = bool(_pin) and _pin in {temporal_id, block_id, str((blk or {}).get("id") or ""),
                                                  str((blk or {}).get("block_uuid") or "")}

        reconciled, suffix, conflict = reconcile_unit_with_block(
            computed_unit_slug=gated_unit,
            unit_confidence=float(unit_confidence),
            computed_block_id=block_ref if block_unit else "",
            block_confidence=1.0,
            block_unit_slug=block_unit,
            block_is_manual=block_is_manual,
            has_manual_unit=bool(manual_unit),
            unit_is_explicit=any(str(r).startswith("unidade-explicita=") for r in (unit_reasons or [])),
            section_unit_slug=section_unit,
            neighbor_block_id=vizinho,
        )
        if vizinho and reconciled == block_unit and not manual_unit:
            suffix = list(suffix) + [f"herdada_do_vizinho={vizinho}"]
        if suffix:
            unit_reasons = list(unit_reasons) + suffix

        entry["computed_unit_slug"] = reconciled
        entry["unit_match_reasons"] = unit_reasons
        entry["unit_match_confidence"] = unit_confidence
        entry["unit_block_conflict"] = conflict

        tags = [t for t in (entry.get("auto_tags") or []) if not str(t).startswith("unit:")]
        if reconciled:
            tags.append(f"unit:{reconciled}")
        entry["auto_tags"] = tags

        # --- Subunit (rota de tópico, restrita à unidade FINAL reconciliada) ---
        manual_subunit = _collapse_ws(str(entry.get("manual_subunit_slug") or ""))
        regra_meta = str(cobertura[0].get("rule") or "") if cobertura else ""
        if manual_subunit:
            preferred_topic_slug = manual_subunit
            best_subunit_slug = manual_subunit
            subunit_reasons = ["manual"]
            subunit_confidence = 1.0
        elif regra_meta in META_COVERAGE_RULES:
            # Espelho da regra A da cobertura (2026-08-31): doc meta descreve o
            # curso INTEIRO — subunit vazia e a resposta honesta (SO plano/
            # programa caiam em evolucao-historica por vocabulario da ementa).
            preferred_topic_slug = ""
            best_subunit_slug = ""
            subunit_reasons = [f"meta-material:{regra_meta}"]
            subunit_confidence = 0.0
        else:
            # Mesmo texto enriquecido da rota de unidade — montado uma vez só.
            topic_match = auto_map_entry_subtopic_fn(
                entry, content_taxonomy, texto_para_unidade, winning_unit_slug=reconciled,
            )
            passe1.append((entry, texto_para_unidade, reconciled, topic_match))
            best_subunit_slug = str(getattr(topic_match, "topic_slug", "") or "")
            subunit_reasons = list(getattr(topic_match, "reasons", []))
            subunit_confidence = float(getattr(topic_match, "confidence", 0.0))
            preferred_topic_slug = ""
            if (
                topic_match.topic_slug
                and not topic_match.ambiguous
                and topic_match.confidence >= T.SUBUNIT_TAG
            ):
                preferred_topic_slug = topic_match.topic_slug

        entry["computed_subunit_slug"] = best_subunit_slug
        entry["subunit_match_reasons"] = subunit_reasons
        entry["subunit_match_confidence"] = subunit_confidence

        tags = [t for t in (entry.get("auto_tags") or []) if not str(t).startswith("subunit:")]
        if preferred_topic_slug:
            tags.append(f"subunit:{preferred_topic_slug}")
        entry["auto_tags"] = tags

    propagar_vocabulario_por_headings(
        passe1, content_taxonomy, auto_map_entry_subtopic_fn,
        conf_min=T.SUBUNIT_PROPAG_CONF, min_entries=T.SUBUNIT_PROPAG_MIN_ENTRIES, df_max=T.SUBUNIT_PROPAG_DF_MAX,
    )

    # `revisar` (Fase 0, 02/09): fila de revisao, derivada do que ficou gravado,
    # em TODO material — inclusive os que o loop acima pulou por nao ter bloco
    # (justamente os "duvida"). Nao-material nao tem eixo: campo some.
    for entry in entries:
        if _is_material(entry):
            entry["revisar"] = revisar_de(entry)
        else:
            entry.pop("revisar", None)
    return entries
