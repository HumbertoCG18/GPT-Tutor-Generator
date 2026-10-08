---
name: setup
description: How to set up, run, and test GPT-Tutor-Generator
triggers:
  - setup
  - install
  - run
  - environment
  - test
  - pytest
  - gitleaks
  - credentials
edges:
  - target: context/stack.md
    condition: when exact technology or manifest details are needed
  - target: context/architecture.md
    condition: when understanding runtime behavior after startup
last_updated: 2026-09-24
---

# Setup

## Requirements From Brief

| Requirement | Source |
|---|---|
| Python `>=3.8`; `3.11` recommended | `pyproject.toml` and README requirements section. |
| Tkinter | README identifies the UI as Tkinter. |
| Git | README requirements section. |
| Ollama | README identifies Vision support through Ollama. |
| Datalab | README identifies the PDF backend as Datalab. |
| pytest | Brief tooling identifies `pytest` as the test runner. |

The manifest declares runtime dependencies and the `dev`/`code-summarization` extras. It still does not declare project scripts, a formatter, or a linter.

## Install

Use a Python virtual environment and install the editable package with the development extra.

```powershell
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
python -m pip install -U pip setuptools wheel
pip install -e .[dev]
```

For Gemini-backed code/reference summarization, install the optional extra:

```powershell
pip install -e .[code-summarization]
```

Servidor MCP do graphify no Windows: `mcp` 2.x importa `pywintypes`; sem `pywin32` o
processo morre antes do `initialize`. `python -m pip check` acusa; `pip install pywin32`
resolve (medido 2026-09-10).

### Linux (sessão na nuvem)

```bash
# dependências (o script do ambiente já instala; repetir só se faltarem)
python3 -m pip install pydantic cffi "pymupdf4llm==1.27.2.3" "pytest>=7" "pytest-cov>=4.1" "ruff>=0.6"
# hook do repositório (o script do ambiente roda fora do clone; a sessão instala).
# Sem chmod o git ignora o hook em silêncio.
H="$(git rev-parse --git-common-dir)/hooks/pre-commit"
cp scripts/hooks/pre-commit.sh "$H" && chmod +x "$H"
# suíte: não para na coleta; os erros de coleta continuam contados no resumo
python3 -m pytest tests -q --continue-on-collection-errors \
  --deselect tests/test_core.py::TestCliResolution::test_marker_cli_prefers_project_venv
```

Instalação editável não é necessária: o `pytest` roda da raiz com `pythonpath = ["."]`. O
`tkinter` fica ausente por decisão: o `python3.11-tk` só existe no PPA `deadsnakes`, bloqueado (403)
pela rede Confiável, e o `python3-tk` do Ubuntu é do 3.12. Sem ele, só os testes de UI citados
abaixo são afetados. O `gitleaks` também fica ausente; o hook só avisa.

Medido nos pilotos de 24/09 na imagem da nuvem (Python 3.11.15), relatórios em
`docs/reports/_archive/2026-09-24-handoff-nuvem-piloto-ambiente.md`,
`docs/reports/_archive/2026-09-24-handoff-nuvem-piloto-ambiente-2.md` e
`docs/reports/2026-09-24-handoff-nuvem-piloto-ambiente-3.md` (este confirmou a base e o hook ativo):

- `pydantic` vai à parte: é importado no topo de módulos puxados por `engine.py`, mas não está
  declarado no `pyproject.toml` desta branch (a `main` declara). Sem ele, 45 erros de coleta.
- `cffi` vai à parte: o `cryptography` do Debian, puxado por `pdfplumber`, não acha
  `_cffi_backend` e derruba a coleta inteira.
- `pymupdf4llm` fixado na versão da máquina do usuário: com 1.28.2, `test_fracao_empilhada_vira_divisao`
  falha (a fração some da saída); com 1.27.2.3 passa (piloto 2, issue #71).
- O teste deselecionado força `os.name = "nt"` no processo e derruba o pytest no Linux.
- Sem `tkinter`, dois módulos de teste falham na coleta e um mock de `tkinter` vaza entre módulos
  (`test_image_curation.py`, `test_datalab_captions.py`), mudando o resultado conforme a ordem.
- Base Linux conhecida (piloto 2, `tkinter` ausente, comando acima): 25 failed, 2341 passed,
  30 skipped, 2 erros de coleta. Das falhas, 21 dependem de caminho `C:\...`, `robocopy` ou barra
  invertida (#68), 3 são o vazamento do mock de `tkinter` (#69) e 1 exige o extra `google-genai`.
  Todas preexistentes; a lista completa está no relatório do piloto 2. Comparar com ela antes de
  atribuir falha nova à sessão.
- Testes que leem repositórios-tutor reais (`TUTOR_REPOS`, `TUTOR_COURSES_DIR`, glob `*-Tutor`)
  dão skip sem eles. Não criar dados para contornar o skip.
- Guia completo da nuvem: [sessao-nuvem.md](sessao-nuvem.md).

## Run

The application main entry point is:

```powershell
python app.py
```

## Test

The test runner is `pytest`.

```powershell
python -m pytest tests -q
```

Teste dirigido: `python -m pytest tests/test_<topico>.py -q` (descubra os módulos com
`rg --files tests` e filtre pelos nomes iniciados em `test_`; inventário completo removido
na dieta MEX 2026-08-06 — envelhecia).

## Segredos e credenciais (#80-#82; incidente de 24/09/2026)

- Hook obrigatorio, compartilhado por todas as worktrees:
  `cp scripts/hooks/pre-commit.sh "$(git rev-parse --git-common-dir)/hooks/pre-commit"`.
  Sem gitleaks 8.30.1 ou sem Python 3.8+, o commit falha; nao ha modo de aviso.
- gitleaks fixado: `python scripts/security/gitleaks_scan.py install --dest <dir no PATH>` baixa a release oficial e
  confere o SHA-256 antes de extrair (Windows x64, Linux e macOS x64/arm64). Na nuvem, o SessionStart de
  `.claude/settings.json` roda `scripts/security/setup_nuvem.sh` (so com `CLAUDE_CODE_REMOTE=true`): instala o
  gitleaks em `~/.local/bin` e o pre-commit com `chmod +x`. Se o download falhar, os commits ficam bloqueados.
- Varredura manual, saida so com regra, arquivo, linha e commit:
  `gitleaks_scan.py staged | range BASE..HEAD | history`. Higiene: `check_repo_hygiene.py tree | range BASE..HEAD | staged`.
- CI: `.github/workflows/security.yml` roda as duas verificacoes nos commits novos de PR e de push na `main`.
- Token M365: fora do repositorio, protegido pelo Windows (DPAPI), em
  `%LOCALAPPDATA%\GPTTutorGenerator\credentials\m365_refresh_token.dpapi`. `GPT_TUTOR_CREDENTIALS_DIR` (absoluto, fora
  do repositorio) troca o diretorio; `GPT_TUTOR_M365_NO_PERSIST=1` desliga a persistencia (login a cada sessao; unico
  modo fora do Windows). O cache antigo `moddle/.m365_token.json` nao e lido nem migrado: apagar manualmente.

## Operational Flow

After launching the app:

1. Create or select a subject.
2. Define the generated repository folder.
3. Import files and links.
4. Process the queue.
5. Review outputs in the generated repository's manual review area when needed.
6. Use Image Curator for extracted images or photos.
7. Build or update the final repository.
8. Use Reprocess Repository to reapply the current architecture to existing repositories.
9. Use Repository Tasks to queue builds, reprocessing, and individual processing.
10. Use Dashboard to monitor operational repository state.
11. Use Cronograma to inspect file-to-block allocation and persist manual block overrides.
12. For Moodle-backed repositories, use the signal migration/probe scripts when backfilling labels, posting dates, card maps, or gold templates for attribution evaluation.
