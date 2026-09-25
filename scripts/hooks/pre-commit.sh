#!/bin/sh
# Pre-commit do repositorio (#54, #56). O Git roda este hook na raiz da worktree do
# commit, para qualquer CLI ou commit manual; os guardas PreToolUse das CLIs veem a
# pasta da sessao e perdem commits feitos com `cd <outra pasta>`.
# Instalar: cp scripts/hooks/pre-commit.sh "$(git rev-parse --git-common-dir)/hooks/pre-commit"
# .git/hooks e compartilhado por todas as worktrees; nao usar core.hooksPath (desligaria os hooks do Graphify).
# Emergencia: git commit --no-verify (e registrar o motivo).

# 1. Anti-padroes Gemini nas linhas adicionadas: reusa o guarda das CLIs.
GUARD=scripts/hooks/gemini-antipattern-guard.js
if [ -f "$GUARD" ] && command -v node >/dev/null 2>&1; then
  echo '{"tool_input":{"command":"git commit"}}' | node "$GUARD" || exit 1
elif [ -f "$GUARD" ]; then
  echo "[pre-commit] node ausente: anti-padroes Gemini NAO verificados." >&2
fi

# 2. Segredos e caminhos de credencial no stage (#81): obrigatorio. Sem o scanner, o commit falha.
#    Versao fixada e instalacao verificada: python scripts/security/gitleaks_scan.py install --dest <dir no PATH>
if [ -f scripts/security/gitleaks_scan.py ]; then
  PY=
  for c in python3 python; do
    if "$c" -c 'import sys; sys.exit(sys.version_info < (3, 8))' >/dev/null 2>&1; then PY=$c; break; fi
  done
  if [ -z "$PY" ]; then
    echo "[pre-commit] python 3.8+ ausente: stage NAO verificado; commit bloqueado." >&2
    exit 1
  fi
  "$PY" scripts/security/check_repo_hygiene.py staged || exit 1
  "$PY" scripts/security/gitleaks_scan.py staged || {
    echo "[pre-commit] Remova do stage ou, se for falso positivo, ajuste .gitleaks.toml com excecao estreita." >&2
    exit 1
  }
  exit 0
fi

# Branch que ainda nao tem scripts/security (o hook instalado vale para todas as worktrees): gitleaks direto,
# sem detalhes na saida. Tambem falha sem o scanner.
if ! command -v gitleaks >/dev/null 2>&1; then
  echo "[pre-commit] gitleaks ausente: stage NAO verificado; commit bloqueado." >&2
  exit 1
fi
if gitleaks git --staged --redact --no-banner --exit-code 1 >/dev/null 2>&1; then
  exit 0
fi
echo "[pre-commit] gitleaks: possivel segredo no stage, ou falha do scanner. Detalhes omitidos." >&2
exit 1
