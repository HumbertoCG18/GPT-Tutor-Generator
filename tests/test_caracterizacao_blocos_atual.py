"""Testes de CARACTERIZAÇÃO do sistema de blocos/cronograma — estado ATUAL.

Objetivo: travar o comportamento de HOJE (antes das Fases 2/3 do refactor de
divisão de blocos), para que a refatoração mostre exatamente o que muda. NÃO
testam o comportamento DESEJADO — testam o que o sistema faz agora. Alguns destes
snapshots VÃO mudar nas Fases 2/3 do plano; a mudança é o sinal e deve ser
revisada no diff, não temida.

NOTA DE ESTADO (verificado contra dado vivo, 2026-06-22): a Fase 1 (identidade
estável) JÁ ENTROU nesta branch — todo bloco carrega `block_uuid` além do
`id=bloco-NN` posicional (display/fallback legado). `computed_block_id`/
`temporal_block_id` dos entries já são UUIDs. Portanto este arquivo trava o
baseline das Fases 2/3 (atribuição por data-membership + over-merge), não da
Fase 1. O over-merge ainda é real (IA bloco-05 = 9 sessões / 28 dias).

Como rodar:
    set TUTOR_REPOS=C:\\Users\\Humberto\\Documents\\GitHub
    python -m pytest tests/test_caracterizacao_blocos_atual.py -q

Primeira execução: gera os baselines em tests/_golden/ e marca skip ("baseline criado").
Rode de novo: agora compara. Versione os tests/_golden/*.json no git — eles SÃO o "antes".
"""
from __future__ import annotations

import json
import os
import re
from datetime import date
from pathlib import Path

import pytest

GOLDEN = Path(__file__).parent / "_golden"
GOLDEN.mkdir(exist_ok=True)


# --------------------------------------------------------------------------- descoberta de repos

def _repo_roots() -> list[Path]:
    base = os.environ.get("TUTOR_REPOS")
    candidates: list[Path] = []
    if base:
        candidates = sorted(Path(base).glob("*-Tutor"))
    if not candidates:
        here = Path.cwd()
        candidates = sorted(here.glob("*-Tutor")) or sorted(here.parent.glob("*-Tutor"))
    return [r for r in candidates if (r / "manifest.json").exists()]


ROOTS = _repo_roots()
needs_repos = pytest.mark.skipif(
    not ROOTS, reason="nenhum repo *-Tutor com manifest.json encontrado (set TUTOR_REPOS)"
)


def _repo_id(p: Path) -> str:
    return p.name


# --------------------------------------------------------------------------- leitura de artefatos

def _load(repo: Path) -> tuple[dict, dict]:
    manifest = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
    tl_path = repo / "course" / ".timeline_index.json"
    timeline = json.loads(tl_path.read_text(encoding="utf-8")) if tl_path.exists() else {}
    return manifest, timeline


def _blocks(timeline: dict) -> list[dict]:
    for key in ("blocks", "timeline", "blocos"):
        val = timeline.get(key)
        if isinstance(val, list):
            return val
    return []


def _entries(manifest: dict) -> list[dict]:
    return manifest.get("entries", []) if isinstance(manifest, dict) else []


def _iso(v) -> date | None:
    try:
        return date.fromisoformat(str(v)[:10])
    except (ValueError, TypeError):
        return None


def _span_dias(block: dict) -> int:
    """Amplitude do bloco em dias, pela primeira/última sessão datada, com fallback
    pra period_start/period_end. -1 quando não dá pra datar."""
    datas = [d for d in (_iso(s.get("date")) for s in (block.get("sessions") or [])) if d]
    if not datas:
        ini, fim = _iso(block.get("period_start")), _iso(block.get("period_end"))
        datas = [d for d in (ini, fim) if d]
    if not datas:
        return -1
    return (max(datas) - min(datas)).days


def _topico(block: dict) -> str:
    tops = [str(t).strip() for t in (block.get("topics") or []) if str(t).strip()]
    return "; ".join(tops) if tops else str(block.get("primary_topic_label") or "").strip()


# --------------------------------------------------------------------------- snapshot helper

def _snapshot(name: str, data) -> None:
    path = GOLDEN / f"{name}.json"
    payload = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)
    if not path.exists():
        path.write_text(payload, encoding="utf-8")
        pytest.skip(f"baseline criado: _golden/{path.name} (revise e versione)")
    assert path.read_text(encoding="utf-8") == payload, (
        f"comportamento atual mudou vs baseline _golden/{path.name} — revise o diff "
        f"(se a mudança for esperada pela fase do refactor, atualize o baseline de propósito)"
    )


# --------------------------------------------------------------------------- testes

@needs_repos
@pytest.mark.parametrize("repo", ROOTS, ids=_repo_id)
def test_identidade_do_bloco_posicional_e_uuid(repo: Path):
    """Documenta a identidade do bloco HOJE: id POSICIONAL (bloco-NN) como display
    + block_uuid estável (Fase 1 JÁ entrou). O snapshot registra quantos blocos
    têm cada um — a prova de que a chave estável existe e o posicional virou rótulo."""
    _, timeline = _load(repo)
    blocks = _blocks(timeline)
    ids = [str(b.get("id") or "") for b in blocks]
    assert ids, f"{repo.name}: nenhum bloco no .timeline_index.json (confira a chave em _blocks)"
    posicionais = [i for i in ids if re.fullmatch(r"bloco-\d+", i)]
    assert posicionais, f"{repo.name}: nenhum id no formato bloco-NN — o esquema pode já ter mudado"
    com_uuid = sum(1 for b in blocks if str(b.get("block_uuid") or "").strip())
    _snapshot(f"{repo.name}__id_scheme", {
        "total": len(ids),
        "posicionais": len(posicionais),
        "com_uuid": com_uuid,
    })


@needs_repos
@pytest.mark.parametrize("repo", ROOTS, ids=_repo_id)
def test_divisao_de_blocos_atual(repo: Path):
    """Snapshot da divisão ATUAL. É aqui que o over-merge aparece (IA deve ter um
    bloco bem largo, ~9 sessões / ~28 dias). Este snapshot DEVE mudar na Fase 3
    (split do over-merge) — o diff é a prova de que a fronteira foi corrigida."""
    _, timeline = _load(repo)
    divisao = [
        {
            "id": str(b.get("id") or ""),
            "n_sessoes": len(b.get("sessions") or []),
            "span_dias": _span_dias(b),
            "topico": _topico(b),
        }
        for b in _blocks(timeline)
    ]
    _snapshot(f"{repo.name}__divisao_blocos", divisao)


@needs_repos
@pytest.mark.parametrize("repo", ROOTS, ids=_repo_id)
def test_maior_bloco_documenta_over_merge(repo: Path):
    """Marca explícito o maior bloco por nº de sessões — o sintoma do over-merge.
    Não é assert de pass/fail rígido; é um snapshot pra ver encolher no fim."""
    _, timeline = _load(repo)
    blocks = _blocks(timeline)
    if not blocks:
        pytest.skip(f"{repo.name}: sem blocos")
    maior = max(blocks, key=lambda b: len(b.get("sessions") or []))
    _snapshot(f"{repo.name}__maior_bloco", {
        "id": str(maior.get("id") or ""),
        "n_sessoes": len(maior.get("sessions") or []),
        "span_dias": _span_dias(maior),
    })


# Casos-chave por repo: arquivos que sabemos hoje estarem no bloco errado ou na fronteira.
# IDs reais dos relatórios; chave = repo.name real (nome da pasta), não o apelido curto.
# ES2 sem casos: os 12/14 miss-de-tópico do baseline 2026-07-01 nunca tiveram ids
# nomeados em relatório (ground_truth_ES2.csv não chegou às fixtures) — mapear
# quando a régua ES2 entrar.
CASOS_CHAVE: dict[str, list[str]] = {
    "Inteligencia-Artifical-Tutor": [
        "aprendizadonaosupervisionado-agrupamento-parte2",  # hierárquico: hoje vai pra "dúvidas t1"?
        "introducao-a-busca-informada",                     # Semana 12: card diz busca, sessão = agentes
        "mlp-novaversao",                                   # posting_date 24/02 (slide reusado)
    ],
    # FAILs vivos da régua MF (eval_ground_truth 2026-08-14, 50/57) + pin aberto.
    "Metodos-Formais-Tutor": [
        "tiposindutivos",  # confiante-errado: band alta, prevê b15, verdade b13 (lesson fino do card Verificação)
        "t1-2026-1",       # confiante-errado: band alta, prevê b11, verdade b05 — salto não-adjacente (família t1/.thy)
        "introducao",      # confiante-errado: band alta, prevê b02, verdade b12 — título genérico atravessa o curso
        "eth2",            # pin-vs-gold aberto (tracker): pino manual→b01, gold diz b12 — snapshot muda no ruling
    ],
    # Mecanismo "data no filename = POSTAGEM, não aula" (so-differs-classification 2026-06-21).
    "Sistemas-Operacionais-Tutor": [
        "0206-laminas-gerencia-de-i-o-livro-texto",  # 02/06 = dia do enunciado TP2; conteúdo é I/O (b05)
        "0904-laminas-semaforos",                    # 09/04 = aula de processador/deadlock; semáforos é b07
        "0704-exemplo-threads-em-java",              # "07.04" é seção Moodle, NEM É data — armadilha de parse
    ],
    # Fronteira Semana-1 + dup-divergence (poda/reprocess TCC 2026-07-01).
    "TCC-Tutor": [
        "aula-01-apresentacao-da-disciplina-revisao-de-teoria-de-conjuntos-e-enumerabilidade",  # true b01, temporal b02 (janela Semana-1 ambígua)
        "aula-06-revisao-alfabeto-cadeia-linguagem-hierarquia-de-chomsky-lemas-e-propriedades-de-automatos",  # dup md5 caiu em 3 blocos; hoje temporal≠computed AO VIVO
    ],
}


@needs_repos
@pytest.mark.parametrize("repo", ROOTS, ids=_repo_id)
def test_atribuicao_dos_casos_chave_atual(repo: Path):
    """Snapshot do bloco/unidade/band ATUAL dos casos-chave. A Fase 2 deve mudar
    estes (ex.: agrupamento-parte2 muda de bloco). Diff = correção comprovada."""
    casos = CASOS_CHAVE.get(repo.name, [])
    if not casos:
        pytest.skip(f"sem casos-chave mapeados pra {repo.name}")
    manifest, _ = _load(repo)
    by_id = {str(e.get("id")): e for e in _entries(manifest)}
    snap = {}
    for cid in casos:
        e = by_id.get(cid, {})
        snap[cid] = {
            "presente": bool(e),
            "computed_block_id": e.get("computed_block_id", ""),
            "temporal_block_id": e.get("temporal_block_id", ""),
            "computed_unit_slug": e.get("computed_unit_slug", ""),
            "band": e.get("computed_block_band", ""),
            "source_section": e.get("source_section", ""),
            "moodle_label": e.get("moodle_label", ""),
        }
    _snapshot(f"{repo.name}__casos_chave", snap)


def test_render_cronograma_golden_master():
    """Golden master do render ATUAL de cronograma_detalhado_md, sobre fixture
    controlada (independe de repo em disco). Trava o formato visível antes do
    refactor; a Fase 3 atualiza este golden com o diff esperado. Garante também o
    requisito do user: o cronograma CONTINUA renderizando."""
    from src.builder.artifacts import repo as repo_mod

    blocks = [
        {
            "id": "bloco-04",
            "period_label": "15 dias · 11/03 a 25/03",
            "primary_topic_label": "ML supervisionado",
            "topics": ["perceptron", "mlp"],
            "unit_slug": "unidade-02",
            "sessions": [
                {"id": "s1", "date": "2026-03-11", "kind": "class", "label": "perceptron", "signals": []},
                {"id": "s2", "date": "2026-03-18", "kind": "class", "label": "mlp", "signals": []},
            ],
        },
        {
            "id": "bloco-09",
            "period_label": "Semana 22/04",
            "primary_topic_label": "",
            "topics": [],
            "unit_slug": "unidade-02",
            "sessions": [
                {"id": "s3", "date": "2026-04-22", "kind": "assessment", "label": "prova p1", "signals": []},
            ],
        },
    ]
    md = repo_mod.cronograma_detalhado_md({"course_name": "IA"}, [], {}, blocks)
    assert "### Sessões" in md  # invariante do Degrau 1: o render lista sessões
    _snapshot("render_cronograma", {"md": md})
