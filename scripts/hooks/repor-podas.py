#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Repoe as podas de skills do ECC no Codex e no agy.

Nenhum dos dois tem equivalente ao skillOverrides do Claude Code. O controle e
podar a copia que cada um materializa — e essa poda nao sobrevive a um
`agy plugin install` ou a um update do plugin no Codex, que recopiam tudo.

Fonte da verdade: o skillOverrides de ~/.claude/settings.json. O que estiver
visivel la fica; o resto sai. O que for visivel e faltar na copia (poda antiga,
nome promovido depois) volta a partir do marketplace do Claude. Assim os tres
CLIs derivam da mesma decisao e nao ha uma segunda lista para manter em sincronia.

Roda no SessionStart do Claude Code e do Codex. Com --aplicar so imprime quando
mudou algo, para nao injetar ruido no contexto da sessao.

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


def mais_nova(d):
    """Pasta de versao mais nova; fixar 2.2.1 pulava o Codex em silencio no update."""
    try:
        vs = [v for v in os.listdir(d) if v[:1].isdigit()]
    except OSError:
        return d
    if not vs:
        return d
    return os.path.join(d, max(vs, key=lambda v: [int(p) for p in v.split(".") if p.isdigit()]))


# (rotulo, pasta, materializa agents, converte command em skill)
# O agy converte command em skill: command com skill homonima duplicaria o nome.
ALVOS = [
    ("codex", mais_nova(os.path.join(H, ".codex", "plugins", "cache", "ecc", "ecc")), True, False),
    ("agy", os.path.join(H, ".gemini", "config", "plugins", "ecc"), False, True),
]


def nome(x):
    return x[:-3] if x.endswith(".md") else x


def visiveis():
    """Nomes do ECC que o Claude Code deixa visiveis ao modelo."""
    s = json.load(open(os.path.join(H, ".claude", "settings.json"), encoding="utf-8"))
    ov = s["skillOverrides"]
    nomes = set(os.listdir(os.path.join(ECC_FONTE, "skills")))
    nomes |= {nome(f) for f in os.listdir(os.path.join(ECC_FONTE, "commands")) if f.endswith(".md")}
    return {n for n in nomes if "ecc:" + n not in ov}


def sincronizar(base, manter, com_agents, cmd_vira_skill, aplicar, log):
    total = 0
    for tipo in ("skills", "commands", "agents"):
        d = os.path.join(base, tipo)
        if not os.path.isdir(d) or (tipo == "agents" and not com_agents):
            continue
        alvo = AGENTS if tipo == "agents" else manter
        if tipo == "commands" and cmd_vira_skill:
            alvo = alvo - set(os.listdir(os.path.join(ECC_FONTE, "skills")))
        presentes = {nome(x) for x in os.listdir(d)}
        fora = [x for x in sorted(os.listdir(d)) if nome(x) not in alvo]
        fonte = os.path.join(ECC_FONTE, tipo)
        faltam = [x for x in sorted(os.listdir(fonte))
                  if nome(x) in alvo and nome(x) not in presentes] if os.path.isdir(fonte) else []
        total += len(fora) + len(faltam)
        log.append(f"    {tipo:9} remove {len(fora):3}, repoe {len(faltam):3}, "
                   f"mantem {len(presentes) - len(fora):3}")
        if aplicar:
            for x in fora:
                p = os.path.join(d, x)
                shutil.rmtree(p, ignore_errors=True) if os.path.isdir(p) else os.remove(p)
            for x in faltam:
                p = os.path.join(fonte, x)
                shutil.copytree(p, os.path.join(d, x)) if os.path.isdir(p) else shutil.copy2(p, d)
    return total


def main():
    aplicar = "--aplicar" in sys.argv
    manter = visiveis()
    log = [f"  fonte: skillOverrides do Claude Code, {len(manter)} nomes visiveis",
           f"  modo: {'APLICANDO' if aplicar else 'simulacao (use --aplicar)'}", ""]
    total = 0
    for rot, base, ag, cvs in ALVOS:
        if not os.path.isdir(base):
            log += [f"  {rot}: {base} nao existe, pulando", ""]
            total += 1  # alvo sumido e anomalia: aparece mesmo com --aplicar
            continue
        log.append(f"  {rot}: {base}")
        total += sincronizar(base, manter, ag, cvs, aplicar, log)
        log.append("")
    if total or not aplicar:
        print("\n".join(log))


if __name__ == "__main__":
    main()
