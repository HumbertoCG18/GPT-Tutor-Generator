#!/bin/sh
# SessionStart (.claude/settings.json), #81: na sessao na nuvem, instala o gitleaks fixado e o pre-commit.
# Localmente nao faz nada. O stdout (saida 0) entra no contexto da sessao, que e quem commita: por isso as falhas
# saem ali, alem do stderr. Sem o scanner, o pre-commit instalado bloqueia commits.
[ "$CLAUDE_CODE_REMOTE" = "true" ] || exit 0
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
BIN="$HOME/.local/bin"
falha() { echo "[nuvem] $1"; echo "[nuvem] $1" >&2; }

# O instalador mantem o binario se ja for a versao fixada; outra versao e substituida pela verificada.
python3 scripts/security/gitleaks_scan.py install --dest "$BIN" >/dev/null 2>&1 \
  || falha "gitleaks NAO instalado (rede ou python3?): o pre-commit vai bloquear commits. Ver .mex/context/setup.md."
if [ -n "$CLAUDE_ENV_FILE" ]; then
  echo "export PATH=\"$BIN:\$PATH\"" >> "$CLAUDE_ENV_FILE"
fi

HOOK="$(git rev-parse --git-common-dir)/hooks/pre-commit"
mkdir -p "$(dirname "$HOOK")" && cp scripts/hooks/pre-commit.sh "$HOOK" && chmod +x "$HOOK"
if [ -x "$HOOK" ] && cmp -s scripts/hooks/pre-commit.sh "$HOOK"; then
  echo "[nuvem] pre-commit instalado; gitleaks: $("$BIN/gitleaks" version 2>/dev/null || echo ausente)."
else
  falha "pre-commit NAO instalado: NAO commitar ate instalar (cp scripts/hooks/pre-commit.sh + chmod +x)."
fi
exit 0
