#!/bin/sh
# Pre-commit: bloqueia segredos no que esta no stage (#54). Repositorio publico.
# Instalar: cp scripts/hooks/pre-commit-secrets.sh "$(git rev-parse --git-common-dir)/hooks/pre-commit"
# O .git/hooks e compartilhado por todas as worktrees; nao usar core.hooksPath (desligaria os hooks do Graphify).
# Emergencia: git commit --no-verify (e registrar o motivo).

if ! command -v gitleaks >/dev/null 2>&1; then
  echo "[pre-commit] gitleaks nao instalado: o stage NAO foi verificado por segredos." >&2
  echo "[pre-commit]   instalar: winget install Gitleaks.Gitleaks" >&2
  exit 0
fi

if gitleaks git --staged --redact --no-banner --exit-code 1 >/dev/null 2>&1; then
  exit 0
fi

echo "[pre-commit] gitleaks encontrou possivel segredo no stage. Detalhes (redigidos):" >&2
gitleaks git --staged --redact --no-banner -v 2>&1 | grep -E 'Finding|RuleID|File|Line' >&2
echo "[pre-commit] Remova do stage ou, se for falso positivo, anote em .gitleaksignore." >&2
exit 1
