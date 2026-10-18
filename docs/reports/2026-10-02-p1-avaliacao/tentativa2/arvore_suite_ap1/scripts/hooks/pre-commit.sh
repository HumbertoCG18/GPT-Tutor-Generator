#!/bin/sh
# Pre-commit do repositorio (#54, #56). O Git roda este hook na raiz da worktree do
# commit, para qualquer CLI ou commit manual; os guardas PreToolUse das CLIs veem a
# pasta da sessao e perdem commits feitos com `cd <outra pasta>`.
# Instalar: cp scripts/hooks/pre-commit.sh "$(git rev-parse --git-common-dir)/hooks/pre-commit"
#   e, fora do Windows, chmod +x no destino: o git ignora hook sem execucao (medido na nuvem, 24/09).
# .git/hooks e compartilhado por todas as worktrees; nao usar core.hooksPath (desligaria os hooks do Graphify).
# Emergencia: git commit --no-verify (e registrar o motivo).

# 1. Anti-padroes Gemini nas linhas adicionadas: reusa o guarda das CLIs.
GUARD=scripts/hooks/gemini-antipattern-guard.js
if [ -f "$GUARD" ] && command -v node >/dev/null 2>&1; then
  echo '{"tool_input":{"command":"git commit"}}' | node "$GUARD" || exit 1
elif [ -f "$GUARD" ]; then
  echo "[pre-commit] node ausente: anti-padroes Gemini NAO verificados." >&2
fi

# 2. Segredos no stage.
if ! command -v gitleaks >/dev/null 2>&1; then
  echo "[pre-commit] gitleaks nao instalado: o stage NAO foi verificado por segredos." >&2
  echo "[pre-commit]   instalar: winget install Gitleaks.Gitleaks (Windows) ou binario de github.com/gitleaks/gitleaks/releases" >&2
  exit 0
fi

if gitleaks git --staged --redact --no-banner --exit-code 1 >/dev/null 2>&1; then
  exit 0
fi

echo "[pre-commit] gitleaks encontrou possivel segredo no stage. Detalhes (redigidos):" >&2
gitleaks git --staged --redact --no-banner -v 2>&1 | grep -E 'Finding|RuleID|File|Line' >&2
echo "[pre-commit] Remova do stage ou, se for falso positivo, ajuste .gitleaks.toml." >&2
exit 1
