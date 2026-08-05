"""TIER 3 (FASE 3): voto LLM nos flagged ∪ same-theme (spec §3 TIER 3 + §12).

Regras (sign-off condicional 03/07 + GO do user 09/07):
- Autoconfianca do LLM e IGNORADA (gravada so p/ auditoria; nenhum gate le).
- Voto BOUNDED a janela: fora da janela = invalido -> mantem FLAG.
- Sem-janela NAO vota (funil-piso responde).
- Cache por IDENTIDADE DE CONTEUDO (md5 do arquivo; fallback id) — gemeos
  compartilham 1 voto (coerente com TIER 0); write atomico; seed MARCO 1.
- Cap de chamadas API por rodada (cache hit nao conta).
- google-genai LAZY dentro do metodo (invariante spec §4).
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import threading
import time
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List, Optional, Set

from pydantic import BaseModel

from src.builder.routing.motor.contracts import MotorContext
from src.builder.text.normalize import normalize_match_text
from src.utils.helpers import norm_ascii_lower

logger = logging.getLogger(__name__)

MD_PROMPT_CAP = 3500   # protocolo MARCO 1
DEFAULT_CAP = 20       # orcamento D8 por rodada/reprocess

SYSTEM_TEMPLATE = (
    "Voce e o desambiguador de atribuicao material->bloco de um tutor de curso "
    "universitario ({course}). Dado um material didatico e os blocos candidatos "
    "da timeline do curso (com datas e topicos do roteiro do professor), escolha "
    "o bloco em que esse material foi usado em aula. Responda APENAS com um dos "
    "block_id candidatos, exatamente como escrito (ex.: bloco-13)."
)


class Voto(BaseModel):
    block_id: str
    confianca: str            # alta|media|baixa — auditoria; NUNCA lida por gate
    justificativa_curta: str


def content_key(entry: dict, repo_dir: Path) -> str:
    """Identidade de conteudo: md5 dos bytes de source_path; fallback = id."""
    rel = str(entry.get("source_path") or "")
    p = Path(repo_dir) / rel
    if rel and p.is_file():
        try:
            h = hashlib.md5()
            with p.open("rb") as fh:
                for chunk in iter(lambda: fh.read(65536), b""):
                    h.update(chunk)
            return h.hexdigest()
        except OSError:
            pass
    return str(entry.get("id") or "")


def load_material_curation(path: Path) -> dict:
    if not Path(path).is_file():
        return {"version": 1, "votes": {}}
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return {"version": 1, "votes": {}}
    if not isinstance(data, dict) or not isinstance(data.get("votes"), dict):
        return {"version": 1, "votes": {}}
    return data


def save_material_curation(path: Path, data: dict) -> None:
    """Write atomico: tmp + os.replace (spec §12 regra 5)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def material_curation_path(repo_dir: Path) -> Path:
    """Sidecar de votos no repo-tutor (spec §12 item 10): raiz, como code_curation.json.

    Escrito SÓ pelo reprocess (ação do user na GUI). Probes usam cache próprio
    em docs/reports/ — nunca este path.
    """
    return Path(repo_dir) / "material_curation.json"


_LOCK_TIMEOUT_S = 10.0   # espera maxima por uma rodada de reprocess concorrente
_LOCK_STALE_S = 60.0     # sentinela mais velho que isso: dono provavelmente morreu
_LOCK_POLL_S = 0.05


class SidecarLockTimeout(RuntimeError):
    """Lock cross-processo do sidecar nao liberado dentro do timeout (T4b)."""


@contextmanager
def _cache_lock(cache_path: Path, timeout: float = _LOCK_TIMEOUT_S,
                stale_after: float = _LOCK_STALE_S):
    """Lock cross-processo (sentinela `O_EXCL`) em volta do read-merge-write do
    sidecar: sem isto, dois reprocess simultaneos podem ler o mesmo estado em
    disco e o segundo save apaga o voto que o primeiro acabou de gravar (item 4
    do mapa). Sentinela mais velho que `stale_after` e tratado como orfao (dono
    morreu sem liberar) e tomado; espera de aquisicao limitada a `timeout`,
    depois desiste com excecao clara — nunca espera infinita.

    # ponytail: lock por sentinela O_EXCL; trocar por portalocker se contencao real aparecer
    """
    lock_path = Path(str(cache_path) + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout
    fd = None
    while fd is None:
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            # deadline+sleep PRIMEIRO, incondicional: todo caminho abaixo (stat
            # falhando, rename perdendo a corrida, dono vivo segurando o handle)
            # tem que passar por aqui, senao um dono lento-mas-vivo (>stale_after
            # sem crashar — laptop suspenso, debugger pausado) vira spin de CPU
            # 100% que nunca levanta SidecarLockTimeout (fix round 1, CRITICAL 1).
            if time.monotonic() >= deadline:
                raise SidecarLockTimeout(
                    f"lock do sidecar ocupado ha mais de {timeout}s: {lock_path}")
            time.sleep(_LOCK_POLL_S)
            try:
                age = time.time() - lock_path.stat().st_mtime
            except OSError:
                continue                    # sentinela sumiu entre EEXIST e stat: retenta
            if age <= stale_after:
                continue                    # dono ainda dentro do prazo: so espera
            # sentinela orfao: takeover single-winner via rename (nao unlink direto).
            # rename tem exatamente um vencedor (quem perde pega FileNotFoundError/
            # PermissionError e NAO rouba); no Windows tambem falha sozinho se o
            # dono ainda segura o handle aberto — nunca toma lock vivo (fix round 1,
            # IMPORTANT 2: unlink() incondicional deixava 2 donos simultaneos).
            stale_name = f"{lock_path}.stale.{os.getpid()}"
            try:
                os.rename(lock_path, stale_name)
            except OSError:
                continue                    # outro dono vivo, ou outro waiter ja venceu
            os.remove(stale_name)           # so o vencedor do rename chega aqui
    try:
        yield
    finally:
        os.close(fd)
        try:
            lock_path.unlink()
        except OSError:
            pass


def import_marco1_seed(seed_votes: dict, entries_by_id: dict, repo_dir: Path) -> dict:
    """Re-chaveia votos do MARCO 1 (por entry-id) para identidade de conteudo.

    Voto com erro/block_id vazio NAO entra (deve re-chamar a API);
    entry que sumiu do manifest NAO entra.
    """
    votes: dict = {}
    for rid, vote in (seed_votes or {}).items():
        if not str((vote or {}).get("block_id") or "").strip():
            continue
        e = entries_by_id.get(str(rid))
        if not e:
            continue
        votes[content_key(e, repo_dir)] = dict(vote)
    return votes


_DIGITS = re.compile(r"\d+")


def detect_same_theme_series(entries: List[dict]) -> Set[str]:
    """Membros de serie same-theme: mesmo card + mesmo stem, >=2 ordinais distintos.

    Porta detect_series do marco0 (metodologia validada no MARCO 1).
    Import lazy de is_out_of_disamb_scope: anchor_engine nao importa llm_vote,
    entao o lazy quebra o ciclo so por higiene de dependencia.
    """
    from src.builder.routing.motor.anchor_engine import is_out_of_disamb_scope

    groups: Dict[tuple, list] = defaultdict(list)
    for e in entries or []:
        if is_out_of_disamb_scope(e):
            continue
        rid = str(e.get("id") or "")
        name = str(e.get("title") or rid)
        nums = _DIGITS.findall(name)
        stem = _DIGITS.sub("", normalize_match_text(name)).strip()
        sec = norm_ascii_lower(str(e.get("source_section") or ""))
        if rid and nums and stem and sec:
            groups[(sec, stem)].append((rid, int(nums[-1])))
    members: Set[str] = set()
    for ms in groups.values():
        if len(ms) >= 2 and len({o for _, o in ms}) >= 2:
            members.update(rid for rid, _o in ms)
    return members


def _block_lines(window: List[str], ctx: MotorContext) -> str:
    out = []
    for ref in window:
        b = ctx.block_by_ref(ref) or {}
        did = str(b.get("id") or ref)
        datas = (f"{str(b.get('period_start') or '')[:10]}.."
                 f"{str(b.get('period_end') or '')[:10]}")
        top = str(b.get("topic_text") or b.get("primary_topic_label") or "").strip()
        rot = " ; ".join(
            ctx.lessons_index.get(str(s.get("date") or "")[:10], "")
            for s in (b.get("sessions") or [])
            if ctx.lessons_index.get(str(s.get("date") or "")[:10])
        )
        out.append(f"- {did} [{datas}] topico: {top[:90]}  roteiro: {rot[:120]}")
    return "\n".join(out)


def build_vote_prompt(entry: dict, window: List[str], ctx: MotorContext,
                      markdown: str = "") -> str:
    """Prompt do MARCO 1 generalizado (roteiro via ctx.lessons_index)."""
    md = (markdown or "")[:MD_PROMPT_CAP]
    return (
        f"MATERIAL:\n"
        f"  titulo: {entry.get('title')}\n"
        f"  categoria: {entry.get('category')}\n"
        f"  secao/card do Moodle: {entry.get('source_section') or '(sem secao)'}\n"
        f"  trecho do conteudo:\n---\n{md or '(sem markdown extraido)'}\n---\n\n"
        f"BLOCOS CANDIDATOS:\n{_block_lines(window, ctx)}\n\n"
        f"Qual bloco? Responda no schema."
    )


def match_window_ref(block_id_vote: str, window: List[str],
                     ctx: MotorContext) -> Optional[str]:
    """Voto -> ref da janela (bounded). Fora da janela = None (mantem FLAG)."""
    v = str(block_id_vote or "").strip().casefold()
    if not v:
        return None
    for ref in window:
        b = ctx.block_by_ref(ref) or {}
        candidates = (str(ref), str(b.get("id") or ""), str(b.get("block_uuid") or ""))
        if v in (c.strip().casefold() for c in candidates):
            return ref
    return None


class LlmVoter:
    """Voto Gemini cacheado com cap por rodada. vote() -> ref da janela ou None.

    client injetavel (testes); em producao lazy via get_gemini_client (spec §4).
    Erro de API NAO e cacheado (rodada seguinte re-tenta); voto fora da janela
    E cacheado (voto real, so nao ancora).
    """

    def __init__(self, config: Optional[dict], cache_path: Path, repo_dir: Path,
                 cap: int = DEFAULT_CAP, client=None):
        self._config = config or {}
        self._cache_path = Path(cache_path)
        self._repo_dir = Path(repo_dir)
        self._cap = int(cap)
        self._client = client
        self._client_loaded = client is not None
        self._data = load_material_curation(self._cache_path)
        self._key_cache: dict = {}   # entry["id"] -> content_key (evita re-md5 por chamada)
        self._lock = threading.Lock()
        self.calls = 0          # chamadas API na rodada (cache hit nao conta)
        self.skipped_cap = 0    # escopo sem voto por cap estourado
        self.errors = 0
        self.no_key = 0
        self.cache_hits = 0

    def _get_client(self):
        if not self._client_loaded:
            from src.builder.runtime.gemini_client import get_gemini_client  # lazy
            self._client = get_gemini_client(self._config)
            self._client_loaded = True
        return self._client

    def _content_key(self, entry: dict) -> str:
        """content_key memoizado por entry["id"] (evita re-md5 do arquivo por chamada)."""
        rid = str(entry.get("id") or "")
        if rid and rid in self._key_cache:
            return self._key_cache[rid]
        key = content_key(entry, self._repo_dir)
        if rid:
            self._key_cache[rid] = key
        return key

    def has_vote(self, entry: dict) -> bool:
        return self._content_key(entry) in self._data["votes"]

    def _persist(self) -> None:
        with _cache_lock(self._cache_path):
            disk = load_material_curation(self._cache_path)
            merged = dict(disk.get("votes") or {})
            merged.update(self._data["votes"])
            self._data["votes"] = merged
            save_material_curation(self._cache_path, self._data)

    def prune(self, live_keys: set) -> int:
        """Remove votos cuja identidade de conteudo sumiu do manifest (item 2)."""
        with self._lock, _cache_lock(self._cache_path):
            disk = load_material_curation(self._cache_path)
            merged = dict(disk.get("votes") or {})
            merged.update(self._data["votes"])
            stale = [k for k in merged if k not in live_keys]
            for k in stale:
                merged.pop(k, None)
            self._data["votes"] = merged
            if stale:
                save_material_curation(self._cache_path, self._data)
        return len(stale)

    def round_summary(self) -> dict:
        return {"calls": self.calls, "errors": self.errors,
                "skipped_cap": self.skipped_cap, "no_key": self.no_key,
                "cache_hits": self.cache_hits}

    def vote(self, entry: dict, window: List[str], ctx: MotorContext,
             markdown: str = "") -> Optional[str]:
        if not window:
            return None                      # sem-janela NAO vota (spec §12)
        key = self._content_key(entry)
        with self._lock:
            cached = self._data["votes"].get(key)
            if cached is None:
                if self.calls >= self._cap:
                    self.skipped_cap += 1
                    return None
                client = self._get_client()
                if client is None:
                    self.no_key += 1
                    logger.info("TIER 3: sem gemini_api_key; voto pulado p/ %s", entry.get("id"))
                    return None               # sem chave -> mantem FLAG
                prompt = build_vote_prompt(entry, window, ctx, markdown)
                system = SYSTEM_TEMPLATE.format(course=ctx.course_name or "curso")
                self.calls += 1
                try:
                    voto = client.summarize_bundle(prompt, Voto, system)
                except Exception as exc:  # noqa: BLE001 — voto falhou: FLAG fica, sem cache
                    self.errors += 1
                    logger.warning("TIER 3: voto falhou p/ %s (%s: %s)",
                                    entry.get("id"), type(exc).__name__, exc)
                    return None
                cached = {
                    "block_id": str(voto.block_id).strip(),
                    "confianca": str(voto.confianca).strip(),  # auditoria; nunca gate
                    "justificativa": str(voto.justificativa_curta)[:200],
                    "model": getattr(client, "model", ""),
                }
                self._data["votes"][key] = cached
                try:
                    self._persist()
                except SidecarLockTimeout as exc:
                    # nao propaga: vote() alimenta anchor_engine -> _run_anchor_engine_layer,
                    # que so tem catch-all (derrubaria a rodada D9 inteira, jogando fora a
                    # chamada de API paga p/ TODOS os materiais, nao so este). O voto ja
                    # esta em self._data["votes"]; o proximo _persist() bem-sucedido
                    # mescla ele de volta ao disco (self-healing; fix round 1, IMPORTANT 3).
                    logger.warning("TIER 3: sidecar ocupado, voto de %s fica so em memoria "
                                    "por agora (%s)", entry.get("id"), exc)
            else:
                self.cache_hits += 1
        return match_window_ref(str(cached.get("block_id") or ""), window, ctx)
