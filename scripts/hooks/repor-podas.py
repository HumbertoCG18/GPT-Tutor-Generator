#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Repoe as podas de skills do ECC e do claude-mem no Codex e no agy.

Nenhum dos dois tem equivalente ao skillOverrides do Claude Code. O controle e
podar a copia que cada um materializa — e essa poda nao sobrevive a um
`agy plugin install` ou a um update do plugin no Codex, que recopiam tudo.

Fonte da verdade: o skillOverrides de ~/.claude/settings.json. O que estiver
visivel la fica; o resto sai. O que for visivel e faltar na copia (poda antiga,
nome promovido depois) volta a partir do marketplace do Claude. Assim os tres
CLIs derivam da mesma decisao e nao ha uma segunda lista para manter em sincronia.

O Codex tambem converte commands em skills (.codex-plugin/migrated-command-skills)
e instala o claude-mem sem node_modules; os hooks do plugin morrem com
"Cannot find module 'zod/v3'". A copia do Claude da mesma versao tem as
dependencias, entao o script liga uma junction para ela.

Roda no SessionStart do Claude Code e do Codex. Com --aplicar so imprime quando
mudou algo, para nao injetar ruido no contexto da sessao.

Uso:
    python scripts/hooks/repor-podas.py            # mostra o que faria
    python scripts/hooks/repor-podas.py --aplicar  # aplica
"""

import json
import os
import shutil
import subprocess
import sys

H = os.path.expanduser("~")
ECC_FONTE = os.path.join(H, ".claude", "plugins", "marketplaces", "ecc")
MEM_FONTE = os.path.join(H, ".claude", "plugins", "marketplaces", "thedotmack", "plugin")
MEM_CACHE_CLAUDE = os.path.join(H, ".claude", "plugins", "cache", "thedotmack", "claude-mem")

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


# (rotulo, prefixo no skillOverrides, fonte, pasta, materializa agents,
#  converte command em skill, dependencias vem do cache do Claude)
# O agy converte command em skill: command com skill homonima duplicaria o nome.
ALVOS = [
    ("codex/ecc", "ecc", ECC_FONTE,
     mais_nova(os.path.join(H, ".codex", "plugins", "cache", "ecc", "ecc")), True, False, False),
    ("agy/ecc", "ecc", ECC_FONTE,
     os.path.join(H, ".gemini", "config", "plugins", "ecc"), False, True, False),
    ("codex/claude-mem", "claude-mem", MEM_FONTE,
     mais_nova(os.path.join(H, ".codex", "plugins", "cache", "claude-mem-local", "claude-mem")), False, False, True),
]


def nome(x):
    return x[:-3] if x.endswith(".md") else x


def listar(d):
    return os.listdir(d) if os.path.isdir(d) else []


def visiveis(prefixo, fonte):
    """Nomes do plugin que o Claude Code deixa visiveis ao modelo."""
    s = json.load(open(os.path.join(H, ".claude", "settings.json"), encoding="utf-8"))
    ov = s["skillOverrides"]
    nomes = set(listar(os.path.join(fonte, "skills")))
    nomes |= {nome(f) for f in listar(os.path.join(fonte, "commands")) if f.endswith(".md")}
    return {n for n in nomes if prefixo + ":" + n not in ov}


def remover(p):
    shutil.rmtree(p, ignore_errors=True) if os.path.isdir(p) else os.remove(p)


def sincronizar(base, fonte, manter, com_agents, cmd_vira_skill, aplicar, log):
    total = 0
    so_skills = set(listar(os.path.join(fonte, "skills")))
    for tipo in ("skills", "commands", "agents"):
        d = os.path.join(base, tipo)
        if not os.path.isdir(d) or (tipo == "agents" and not com_agents):
            continue
        alvo = AGENTS if tipo == "agents" else manter
        if tipo == "commands" and cmd_vira_skill:
            alvo = alvo - so_skills
        presentes = {nome(x) for x in os.listdir(d)}
        fora = [x for x in sorted(os.listdir(d)) if nome(x) not in alvo]
        orig = os.path.join(fonte, tipo)
        faltam = [x for x in sorted(listar(orig)) if nome(x) in alvo and nome(x) not in presentes]
        total += len(fora) + len(faltam)
        log.append(f"    {tipo:9} remove {len(fora):3}, repoe {len(faltam):3}, "
                   f"mantem {len(presentes) - len(fora):3}")
        if aplicar:
            for x in fora:
                remover(os.path.join(d, x))
            for x in faltam:
                p = os.path.join(orig, x)
                shutil.copytree(p, os.path.join(d, x)) if os.path.isdir(p) else shutil.copy2(p, d)
    # ponytail: so poda; o Codex gera estas pastas, command promovido depois so volta reinstalando o plugin
    mig = os.path.join(base, ".codex-plugin", "migrated-command-skills")
    if os.path.isdir(mig):
        cmds = manter - so_skills
        fora = [x for x in sorted(os.listdir(mig)) if x.removeprefix("source-command-") not in cmds]
        total += len(fora)
        log.append(f"    migrados  remove {len(fora):3}, mantem {len(os.listdir(mig)) - len(fora):3}")
        if aplicar:
            for x in fora:
                remover(os.path.join(mig, x))
    return total


def repor_deps(base, aplicar, log):
    """Liga node_modules do cache do Claude na copia do Codex (mesma versao)."""
    dst = os.path.join(base, "node_modules")
    if os.path.isdir(dst):
        return 0
    src = os.path.join(MEM_CACHE_CLAUDE, os.path.basename(base), "node_modules")
    if not os.path.isdir(src):
        log.append(f"    deps      FALTA: o Claude nao tem {src}; atualizar o claude-mem no Claude")
        return 1
    log.append(f"    deps      junction {dst} -> {src}")
    if aplicar:
        r = subprocess.run(["cmd", "/c", "mklink", "/J", dst, src], capture_output=True, text=True)
        if r.returncode:
            log.append(f"    deps      ERRO mklink: {(r.stdout + r.stderr).strip()}")
    return 1


def main():
    aplicar = "--aplicar" in sys.argv
    log = ["  fonte: skillOverrides do Claude Code",
           f"  modo: {'APLICANDO' if aplicar else 'simulacao (use --aplicar)'}", ""]
    total = 0
    for rot, prefixo, fonte, base, ag, cvs, deps in ALVOS:
        if not os.path.isdir(base):
            log += [f"  {rot}: {base} nao existe, pulando", ""]
            total += 1  # alvo sumido e anomalia: aparece mesmo com --aplicar
            continue
        manter = visiveis(prefixo, fonte)
        log.append(f"  {rot}: {base} ({len(manter)} visiveis)")
        total += sincronizar(base, fonte, manter, ag, cvs, aplicar, log)
        if deps:
            total += repor_deps(base, aplicar, log)
        log.append("")
    if total or not aplicar:
        print("\n".join(log))


if __name__ == "__main__":
    main()
