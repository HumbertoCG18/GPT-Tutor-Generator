#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Repoe as podas de skills do ECC no Codex e no agy.

Nenhum dos dois tem equivalente ao skillOverrides do Claude Code. O controle e
podar a copia que cada um materializa — e essa poda nao sobrevive a um
`agy plugin install` ou a um update do plugin no Codex, que recopiam tudo.

Fonte da verdade: o skillOverrides de ~/.claude/settings.json. O que estiver
visivel la fica; o resto sai. Assim os tres CLIs derivam da mesma decisao e nao
ha uma segunda lista para manter em sincronia.

Uso:
    python scripts/hooks/repor-podas.py            # mostra o que faria
    python scripts/hooks/repor-podas.py --aplicar  # aplica
"""

import json
import os
import shutil
import sys

H = os.path.expanduser("~")
ECC_FONTE = os.path.join(H, ".claude", "plugins", "marketplaces", "ecc")

# Agents que o orch-pipeline invoca por nome. So valem no Codex, que
# materializa agents; o agy nao os expoe e o Claude nao permite filtra-los.
AGENTS = {
    "planner", "architect", "code-architect", "tdd-guide", "code-reviewer",
    "security-reviewer", "code-explorer", "build-error-resolver", "python-reviewer",
}

ALVOS = [
    ("codex", os.path.join(H, ".codex", "plugins", "cache", "ecc", "ecc", "2.2.1"), True),
    ("agy", os.path.join(H, ".gemini", "config", "plugins", "ecc"), False),
]


def visiveis():
    """Nomes do ECC que o Claude Code deixa visiveis ao modelo."""
    s = json.load(open(os.path.join(H, ".claude", "settings.json"), encoding="utf-8"))
    ov = s["skillOverrides"]
    nomes = {d for d in os.listdir(os.path.join(ECC_FONTE, "skills"))}
    nomes |= {f[:-3] for f in os.listdir(os.path.join(ECC_FONTE, "commands")) if f.endswith(".md")}
    return {n for n in nomes if "ecc:" + n not in ov}


def podar(base, manter, com_agents, aplicar):
    total = 0
    for tipo in ("skills", "commands", "agents"):
        d = os.path.join(base, tipo)
        if not os.path.isdir(d):
            continue
        alvo = AGENTS if tipo == "agents" else manter
        if tipo == "agents" and not com_agents:
            continue
        fora = [x for x in sorted(os.listdir(d))
                if (x[:-3] if x.endswith(".md") else x) not in alvo]
        total += len(fora)
        print(f"    {tipo:9} remove {len(fora):3}, mantem {len(os.listdir(d)) - len(fora):3}")
        if aplicar:
            for x in fora:
                p = os.path.join(d, x)
                shutil.rmtree(p, ignore_errors=True) if os.path.isdir(p) else os.remove(p)
    return total


def main():
    aplicar = "--aplicar" in sys.argv
    manter = visiveis()
    print(f"  fonte: skillOverrides do Claude Code, {len(manter)} nomes visiveis")
    print(f"  modo: {'APLICANDO' if aplicar else 'simulacao (use --aplicar)'}\n")
    for rot, base, ag in ALVOS:
        if not os.path.isdir(base):
            print(f"  {rot}: {base} nao existe, pulando\n")
            continue
        print(f"  {rot}:")
        podar(base, manter, ag, aplicar)
        print()


if __name__ == "__main__":
    main()
