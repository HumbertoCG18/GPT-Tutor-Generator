"""Replay OFFLINE de seleção de memória (piloto, issue #45).

Lê um JSON local redigido manualmente, monta o baseline determinístico por
projeto (com deduplicação exata) e aplica decisões SIMULADAS sobre o mesmo
conjunto elegível. Não chama LLM, rede nem banco, e não grava nada: o
relatório sai em JSON no stdout. Tokens não são medidos (sempre null).

Uso: python replay.py example.json
"""

import argparse
import json
import sys

VERSION = 1
DECISIONS = ("drop", "keep", "uncertain", "error")


class ReplayError(ValueError):
    """Entrada inválida; o replay recusa em vez de adivinhar."""


# --- leitura estrita -------------------------------------------------------


def _no_duplicate_keys(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ReplayError(f"chave JSON duplicada: {key!a}")
        obj[key] = value
    return obj


def _reject_constant(name):
    raise ReplayError(f"constante JSON não permitida: {name}")


def parse(text):
    try:
        return json.loads(text, object_pairs_hook=_no_duplicate_keys, parse_constant=_reject_constant)
    except ReplayError:
        raise
    except (ValueError, RecursionError) as exc:
        raise ReplayError(f"JSON malformado: {exc}") from exc


def load(path):
    try:
        with open(path, encoding="utf-8-sig") as handle:
            text = handle.read()
    except (OSError, UnicodeDecodeError) as exc:
        raise ReplayError(f"não foi possível ler {path!a}: {exc}") from exc
    return parse(text)


# --- validação -------------------------------------------------------------


def _obj(value, where, required, optional=()):
    if not isinstance(value, dict):
        raise ReplayError(f"{where}: esperado objeto")
    missing = [k for k in required if k not in value]
    unknown = [k for k in value if k not in required and k not in optional]
    if missing or unknown:
        raise ReplayError(f"{where}: chaves ausentes {missing!a}, desconhecidas {unknown!a}")


def _str(value, where):
    if not isinstance(value, str) or not value:
        raise ReplayError(f"{where}: esperado string não vazia")
    return value


def _list(value, where):
    if not isinstance(value, list):
        raise ReplayError(f"{where}: esperado lista")
    return value


def _unique_ids(ids, where, known=None):
    seen = set()
    for item in ids:
        if item in seen:
            raise ReplayError(f"{where}: ID repetido {item!a}")
        if known is not None and item not in known:
            raise ReplayError(f"{where}: ID desconhecido {item!a}")
        seen.add(item)
    return seen


def validate(data):
    _obj(data, "raiz", ("version", "task", "project", "candidates", "simulated_decisions"), ("required_ids",))
    # type() e não isinstance(): bool é subclasse de int, e 1.0 == 1.
    if type(data["version"]) is not int or data["version"] != VERSION:
        raise ReplayError(f"version: esperado inteiro {VERSION}")
    _str(data["task"], "task")
    project = _str(data["project"], "project")

    for i, cand in enumerate(_list(data["candidates"], "candidates")):
        where = f"candidates[{i}]"
        _obj(cand, where, ("id", "project", "text", "protected"))
        for key in ("id", "project", "text"):
            _str(cand[key], f"{where}.{key}")
        if type(cand["protected"]) is not bool:
            raise ReplayError(f"{where}.protected: esperado booleano")
        try:
            cand["text"].encode("utf-8")
        except UnicodeEncodeError as exc:
            raise ReplayError(f"{where}.text: não codificável em UTF-8") from exc
        if cand["protected"] and cand["project"] != project:
            raise ReplayError(
                f"{where}: protegido {cand['id']!a} pertence ao projeto {cand['project']!a}, "
                f"não a {project!a}; corrija a entrada em vez de deixá-lo sumir"
            )
    known = _unique_ids([c["id"] for c in data["candidates"]], "candidates")

    if "required_ids" in data:
        required = _list(data["required_ids"], "required_ids")
        for i, item in enumerate(required):
            _str(item, f"required_ids[{i}]")
        _unique_ids(required, "required_ids", known)

    # Estrutura e IDs das decisões são erro de autoria -> recusa. O VALOR de
    # "decision" simula saída de modelo e pode vir torto -> fail-open em _simulate.
    decisions = _list(data["simulated_decisions"], "simulated_decisions")
    for i, entry in enumerate(decisions):
        where = f"simulated_decisions[{i}]"
        _obj(entry, where, ("id",), ("decision",))
        _str(entry["id"], f"{where}.id")
    _unique_ids([d["id"] for d in decisions], "simulated_decisions", known)


# --- seleção (nunca recebe required_ids) ------------------------------------


def _eligible(project, candidates):
    """Baseline: candidatos do projeto, ordem de entrada, dedup por texto idêntico."""
    groups, excluded = {}, []
    for cand in candidates:
        if cand["project"] != project:
            excluded.append(cand["id"])
            continue
        group = groups.setdefault(
            cand["text"], {"id": cand["id"], "text": cand["text"], "sources": [], "protected": False}
        )
        group["sources"].append(cand["id"])
        group["protected"] = group["protected"] or cand["protected"]
    return list(groups.values()), excluded


def _simulate(eligible, decisions):
    """Só sai quem tem decisão explícita e válida 'drop' e não é protegido."""
    by_id = {d["id"]: d.get("decision") for d in decisions}
    kept, dropped = [], []
    preserved = {k: [] for k in ("keep", "uncertain", "error", "missing", "invalid", "protected")}
    for group in eligible:
        decision = by_id.get(group["id"])
        if group["id"] not in by_id:
            reason = "missing"
        elif not isinstance(decision, str) or decision not in DECISIONS:
            reason = "invalid"
        elif decision == "drop":
            reason = "protected" if group["protected"] else None
        else:
            reason = decision
        if reason is None:
            dropped.append(group["id"])
        else:
            kept.append(group)
            preserved[reason].append(group["id"])
    canonical = {g["id"] for g in eligible}
    not_applicable = [d["id"] for d in decisions if d["id"] not in canonical]
    return kept, dropped, preserved, not_applicable


# --- avaliação e métricas ---------------------------------------------------


def _evaluate(groups, required):
    if required is None:
        return {
            "labels": "absent",
            "required_total": 0,
            "lost_ids": None,
            "recall": None,
            "recall_status": "undefined_no_labels",
        }
    retained = {source for g in groups for source in g["sources"]}
    lost = [r for r in required if r not in retained]
    total = len(required)
    return {
        "labels": "present",
        "required_total": total,
        "lost_ids": lost,
        "recall": (total - len(lost)) / total if total else None,
        "recall_status": "measured" if total else "undefined_no_required",
    }


def _branch(groups, required):
    texts = [g["text"] for g in groups]
    return {
        "selected_ids": [g["id"] for g in groups],
        "provenance": {g["id"]: list(g["sources"]) for g in groups},
        "protected_ids": [g["id"] for g in groups if g["protected"]],
        "chars": sum(len(t) for t in texts),
        "utf8_bytes": sum(len(t.encode("utf-8")) for t in texts),
        "tokens": None,  # não medido neste piloto; nunca inferir de chars/bytes
        "evaluation": _evaluate(groups, required),
    }


def replay(data):
    validate(data)
    eligible, excluded = _eligible(data["project"], data["candidates"])
    kept, dropped, preserved, not_applicable = _simulate(eligible, data["simulated_decisions"])

    required = data.get("required_ids")  # só avaliação, depois da seleção
    baseline = _branch(eligible, required)
    simulated = _branch(kept, required)
    simulated.update(dropped_ids=dropped, preserved=preserved, not_applicable_decisions=not_applicable)
    return {
        "version": VERSION,
        "task": data["task"],
        "project": data["project"],
        "candidates_total": len(data["candidates"]),
        "excluded_other_project": excluded,
        "baseline": baseline,
        "simulated": simulated,
        "delta": {
            "chars": simulated["chars"] - baseline["chars"],
            "utf8_bytes": simulated["utf8_bytes"] - baseline["utf8_bytes"],
            "tokens": None,
        },
        "measurement": {
            "tokens": "not_measured",
            "cost": "not_measured",
            "llm_calls": 0,
        },
    }


# --- CLI -------------------------------------------------------------------


def main(argv=None):
    parser = argparse.ArgumentParser(description="Replay offline de seleção de memória (piloto #45).")
    parser.add_argument("input", help="JSON local redigido manualmente")
    args = parser.parse_args(argv)
    try:
        report = replay(load(args.input))
    except ReplayError as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
