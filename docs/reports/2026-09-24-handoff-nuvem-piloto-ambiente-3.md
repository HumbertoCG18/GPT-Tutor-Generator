# Handoff nuvem — piloto de ambiente 3 (24/09/2026)

Só diagnóstico. Nenhum arquivo do projeto foi alterado além deste relatório. A única instalação
foi o hook do pre-commit, exigida pela §1 de
[sessao-nuvem.md](../../.mex/context/sessao-nuvem.md).

## Pedido, issue, base

- Pedido: registrar `/tmp/setup-nuvem.log` e o resultado cru de `import tkinter`, `pydantic`,
  `pytest` e `id -un` antes de instalar qualquer coisa; fazer a primeira ação da §1, incluindo o
  hook; rodar o comando de testes do [setup.md](../../.mex/context/setup.md) (Linux) e comparar
  com a base conhecida; não corrigir nada.
- Issues: nenhuma específica. Relacionadas e abertas:
  [#68](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/68) (suíte portável no Linux) e
  [#69](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/69) (mock de `tkinter` vaza).
  O PR usa `Refs`.
- Base: `fix/workflow-claude-code` @ `027ad0f0e553d075b72e7a6c284dc8357055490a`.
- Branch: `nuvem/2026-09-24-piloto-ambiente-3`.
- Arquivo mudado: só este.
- Base de comparação: "Base Linux conhecida" do `setup.md` (medida no
  [piloto 2](2026-09-24-handoff-nuvem-piloto-ambiente-2.md)).

## 1. Antes de qualquer instalação

### 1.1 `/tmp/setup-nuvem.log`

Existe (`-rw-r--r-- root root 895`, 24/09 02:04 -0300). Conteúdo integral:

```
[setup] 2026-09-24T05:04:19+00:00 usuario=root cwd=/home/user
WARNING: Running pip as the 'root' user can result in broken permissions and conflicting behaviour with the system package manager. It is recommended to use a virtual environment instead: https://pip.pypa.io/warnings/venv
E: Failed to fetch https://ppa.launchpadcontent.net/deadsnakes/ppa/ubuntu/dists/noble/InRelease  403  Forbidden [IP: 185.125.189.188 443]
E: The repository 'https://ppa.launchpadcontent.net/deadsnakes/ppa/ubuntu noble InRelease' is no longer signed.
E: Failed to fetch https://ppa.launchpadcontent.net/ondrej/php/ubuntu/dists/noble/InRelease  403  Forbidden [IP: 185.125.189.188 443]
E: The repository 'https://ppa.launchpadcontent.net/ondrej/php/ubuntu noble InRelease' is no longer signed.
[setup] python3.11-tk não instalado
[setup] fim; o hook do pre-commit é instalado pela sessão (sessao-nuvem.md §1)
```

### 1.2 Resultado cru

| Comando | Saída | exit |
|---|---|---|
| `python -c "import tkinter"` | `ModuleNotFoundError: No module named 'tkinter'` | 1 |
| `python -c "import pydantic"` | OK, 2.13.5 | 0 |
| `python -c "import pytest"` | OK, 9.1.1 | 0 |
| `id -un` | `root` | 0 |

`python` e `python3` são `/usr/local/bin/python{,3}`, Python 3.11.15.

### 1.3 O que o log explica

- O script roda como `root` e em `cwd=/home/user`, fora do clone. Por isso não instala o hook, o
  que a própria última linha do log assume.
- `python3.11-tk` não foi instalado. `apt-cache policy python3.11-tk` mostra o candidato
  `3.11.15-1+noble1` vindo só do PPA `deadsnakes`, cujo `InRelease` deu **403 Forbidden** no
  `apt-get update`. Causa provável da falha: o PPA bloqueado pelo proxy, não falta de root.
  Não confirmado com tentativa de instalação, por pedido. O `python3-tk` do Ubuntu é do 3.12.
- O `pip` rodou (aviso de root) e instalou o esperado: `pydantic`, `pytest`, `cffi` 2.1.1,
  `pymupdf4llm` 1.27.2.3, `pytest-cov` 7.1.0, `ruff` 0.16.8 presentes.

## 2. Primeira ação da §1

| Passo | Resultado |
|---|---|
| `python3 -c "import pydantic, pytest"` | exit 0 |
| `ls "$(git rev-parse --git-common-dir)/hooks/pre-commit"` | `No such file or directory`, exit 2 (só `*.sample`; `core.hooksPath` não definido) |
| Ler `/tmp/setup-nuvem.log` | Seção 1.1 |
| Dependências | Presentes; nada instalado |
| Hook ausente → `cp scripts/hooks/pre-commit.sh "$(git rev-parse --git-common-dir)/hooks/pre-commit"` | exit 0 |

### 2.1 O hook copiado fica inativo

O `cp` documentado gera `.git/hooks/pre-commit` com modo `-rw-r--r--`, porque a fonte está no
índice como `100644`. O git 2.43 ignora hook sem execução:

```
$ git hook run pre-commit
hint: The '.git/hooks/pre-commit' hook was ignored because it's not set as executable.
hint: You can disable this warning with `git config advice.ignoredHook false`.
error: cannot find a hook named pre-commit
```

No `git commit` isso aparece só como `hint`, e o commit passa sem guarda. Para cumprir o aceite
(commit com hook ativo) foi aplicado `chmod +x .git/hooks/pre-commit`, só no hook instalado, fora
do repositório. Depois disso:

```
$ git hook run pre-commit
[pre-commit] gitleaks nao instalado: o stage NAO foi verificado por segredos.
[pre-commit]   instalar: winget install Gitleaks.Gitleaks
exit=0
```

O guarda Gemini roda (`node` v22.22.2 presente) e passa em silêncio. O `gitleaks` segue ausente,
então o hook só avisa. A saída do hook no commit deste relatório está na mensagem do commit.

### 2.2 Condição de parada

`docs/reports/pendencias.md` do clone não tem `<!-- fila-campanhas-start -->` (`grep -c` = 0). A
§1 manteria esta sessão em diagnóstico, que é o que o pedido exige.

## 3. Suíte

Comando literal do `setup.md` (Linux):

```
python3 -m pytest tests -q --continue-on-collection-errors \
  --deselect tests/test_core.py::TestCliResolution::test_marker_cli_prefers_project_venv
```

```
25 failed, 2341 passed, 30 skipped, 1 deselected, 11 warnings, 2 errors in 18.97s
```

exit 1. Segunda execução (com `-rs -p no:cacheprovider`, só para listar skips): mesmo resultado,
com 3 warnings. Os 8 warnings extras são `invalid escape sequence` de `tests/test_moodle_sync.py`
e `tests/test_vocabulary_compile.py`, emitidos só na primeira compilação, como no piloto 2.

## 4. Comparação com a base conhecida

| | Base (`setup.md`, piloto 2) | Agora |
|---|---|---|
| failed | 25 | 25 |
| passed | 2341 | 2341 |
| skipped | 30 | 30 |
| deselected | 1 | 1 |
| errors (coleta) | 2 | 2 |
| warnings | 3 (11 na primeira compilação) | 11 na primeira, 3 na segunda |

### 4.1 Melhorou

- Hook do pre-commit instalado e ativo (piloto 2: ausente).
- O comando documentado agora roda a suíte sem `tkinter`, graças a
  `--continue-on-collection-errors` (piloto 2: parava na coleta com o comando da época).
- Existe um log do script do ambiente, que explica o que ele fez e por que o `tkinter` falhou.

### 4.2 Piorou

Nada. Nenhuma falha, erro ou skip novo.

### 4.3 Igual

Lista de falhas idêntica à do piloto 2, teste a teste:

| Grupo | Testes |
|---|---|
| Sem `tkinter` (coleta) | `test_assessment_label_and_plan_section.py`, `test_codes_panel_label.py` |
| Vazamento do mock de `tkinter` (#69) | `test_reprocess_flags.py::test_app_build_options_igual_ao_script_para_o_mesmo_perfil`; `test_subject_dialog_save.py::test_save_existing_subject_keeps_feature_flags_identical`, `::test_save_new_subject_keeps_empty_feature_flags` |
| Sem `google-genai` | `test_gemini_generate_text.py::test_generate_text_sends_prompt_and_image_part` |
| `robocopy` (#68) | `test_glossary_structured.py::test_fresh_copy_copies_source_and_propagates_failure` |
| Caminho `C:\...` (#68) | `test_moodle_structure.py` (5), `test_moodle_sync.py` (13) |
| Barra invertida (#68) | `test_section_from_source_path.py::test_lida_com_backslash`, `test_stash_import.py::test_id_de_tar_gz_nao_carrega_tar` |
| `os.name` global (#68) | `test_core.py::...test_marker_cli_prefers_project_venv`, deselecionado |

Skips (30), mesma distribuição: `test_caracterizacao_blocos_atual.py` 4, `test_pdf_markdown.py` 3,
`test_timeline_kinds.py` 10, `test_timeline_schema.py` 10, `test_unit_matcher.py` 2,
`test_voter_lock.py` 1. Também iguais: `tkinter`, `gitleaks`, `google-genai` e o pacote editável
ausentes.

## 5. Divergências com o guia

1. `setup.md` e o cabeçalho de `scripts/hooks/pre-commit.sh` mandam só `cp`. No Linux o hook
   resultante fica sem execução e o git o ignora (2.1). Falta `chmod +x`, ou marcar a fonte como
   `100755` no índice.
2. `setup.md` diz que o `tkinter` "exige root e não foi instalado pelo script". O script já roda
   como `root`; o bloqueio provável é o 403 do PPA `deadsnakes` (1.3).
3. A mensagem do hook sugere `winget install Gitleaks.Gitleaks`, que só vale no Windows.

## 6. O que não foi validado

- Testes com `tkinter` real e o deselecionado de `test_core.py`.
- Se `apt-get install python3.11-tk` falha mesmo pelo 403 (não tentado, por pedido).
- Hook com `gitleaks` presente: este relatório foi commitado com o hook ativo, mas sem varredura
  de segredo. Revisado manualmente: não contém segredo.
- Ruff, app, replay, zero-diff e tudo que usa repositórios-tutor, rede ou LLM.

## 7. Delta proposto ao tracker (não aplicado)

- "Piloto 3 (24/09): script do ambiente roda como root em `/home/user`, instala as deps pip e grava
  `/tmp/setup-nuvem.log`; `python3.11-tk` falha (PPA `deadsnakes` 403). Hook instalado pela sessão,
  mas o `cp` do guia o deixa sem `+x` e o git o ignora. Suíte igual à base: 25 failed, 2341 passed,
  30 skipped, 2 erros de coleta. Ver `docs/reports/2026-09-24-handoff-nuvem-piloto-ambiente-3.md`."

## 8. Decisões para o usuário

1. **Hook sem execução**: corrigir o guia (`cp` + `chmod +x`), gravar `scripts/hooks/pre-commit.sh`
   como `100755` no git, ou as duas coisas. Pede issue própria.
2. **`tkinter` na nuvem**: liberar `ppa.launchpadcontent.net` na política de rede do ambiente,
   aceitar a ausência (só 5 testes afetados), ou trocar a origem do Python 3.11.
3. **`gitleaks` na nuvem**: instalar no script do ambiente, para o hook deixar de só avisar.
