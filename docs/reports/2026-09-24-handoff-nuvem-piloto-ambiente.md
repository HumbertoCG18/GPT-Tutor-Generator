# Handoff nuvem — piloto de ambiente (24/09/2026)

Só diagnóstico. Nenhum arquivo do projeto foi alterado além deste relatório.

## Pedido, issue, base

- Pedido: registrar Python, `tkinter`, `pydantic`, `gitleaks` e o pre-commit; rodar
  `python3 -m pytest tests -q` e classificar cada falha; não corrigir nada.
- Issue: nenhuma. A busca por "sessão na nuvem ambiente Linux piloto setup" não achou duplicata, e o
  pedido não autoriza criar uma. O PR usa só o pedido como referência.
- Base: `fix/workflow-claude-code` @ `095e25a6ab52ffbb88d39741f56b25ef6caef75d`.
- Branch: `nuvem/2026-09-24-piloto-ambiente`.
- Arquivo mudado: só este.

## 1. Estado bruto do container (antes de qualquer instalação)

| Item | Resultado |
|---|---|
| `python3 --version` | `Python 3.11.15`. `/usr/local/bin/python3` é symlink para `/usr/bin/python3.11` |
| `import tkinter` | Falha: `ModuleNotFoundError: No module named 'tkinter'` |
| `import pydantic` | Falha: `ModuleNotFoundError: No module named 'pydantic'` |
| `pytest` | Ausente: `No module named pytest` |
| `gitleaks` | Ausente (`command not found`) |
| Pre-commit em `.git/hooks` | Não instalado: só há `*.sample`; `core.hooksPath` não definido |
| `node` | `v22.22.2` (o guarda Gemini do pre-commit rodaria se o hook existisse) |
| `pip` | 24.0, sem requisitos quebrados (`pip check`) |

A imagem traz Python 3.10, 3.11, 3.12 e 3.13. O `python3` padrão é o 3.11, mas os pacotes do
Debian em `/usr/lib/python3/dist-packages` foram compilados para o 3.12 (ex.:
`_cffi_backend.cpython-312-x86_64-linux-gnu.so`). Esse descompasso causa o bloqueio 2.1.

## 2. O que foi instalado para medir (só no container, nada no repositório)

Na ordem, para isolar o efeito de cada dependência:

1. `python3 -m pip install -e ".[dev]"` (instalação do [setup.md](../../.mex/context/setup.md)).
2. `python3 -m pip install cffi` (contorno do bloqueio 2.1; não está no guia).
3. `python3 -m pip install pydantic` (o guia manda instalar à parte).

`git status` continuou limpo (o `*.egg-info` é ignorado). Versões resultantes: pytest 9.1.1,
pytest-cov 7.1.0, ruff 0.16.8, pymupdf 1.28.2, pymupdf4llm 1.28.2, pdfplumber 0.11.10,
pdfminer.six 20260107, cryptography 41.0.7 (Debian), cffi 2.1.1, pydantic 2.13.5. Não instalados:
`tkinter` (pacote de sistema), `google-genai` (extra `code-summarization`), `gitleaks`.

### 2.1 Bloqueio da imagem: `cryptography` do Debian sem `_cffi_backend`

Só com `.[dev]`, a coleta parou com 159 erros. Cadeia: `src/utils/helpers.py:59` importa
`pdfplumber` → `pdfminer` → `cryptography` (Debian, 3.12) → `pyo3_runtime.PanicException: Python
API call failed`, causada por `No module named '_cffi_backend'`. Quase todo o código importa
`helpers.py`, então a suíte inteira fica inutilizável. Não é defeito do projeto. `pip install cffi`
resolveu (`import pdfplumber` passou).

### 2.2 Efeito do `pydantic`

Com `cffi` e sem `pydantic`: 1635 testes coletados, 47 erros de coleta (45 por `pydantic`, 2 por
`tkinter`). Confirma a lacuna 12 de [sessao-nuvem.md](../../.mex/context/sessao-nuvem.md): o pacote
não está declarado no `pyproject.toml` desta base.

## 3. Execução da suíte

### 3.1 Comando pedido, literal

`python3 -m pytest tests -q` → `Interrupted: 2 errors during collection`, 0 testes executados. Os
dois módulos importam `src.ui.*`, que importa `tkinter`:

- `tests/test_assessment_label_and_plan_section.py` (via `src.ui.timeline_dashboard`)
- `tests/test_codes_panel_label.py` (via `src.ui.codes_panel`)

### 3.2 Passando dos erros de coleta

`python3 -m pytest tests -q -rfEs --continue-on-collection-errors` → 310 testes e depois
`INTERNALERROR`: `NotImplementedError: cannot instantiate 'WindowsPath' on your system`, que derruba
o pytest inteiro. Origem: `tests/test_core.py::TestCliResolution::test_marker_cli_prefers_project_venv`
(linha 405) faz `monkeypatch.setattr(helpers_module.os, "name", "nt")`. `helpers_module.os` é o
próprio módulo `os`, então `pathlib.Path()` passa a instanciar `WindowsPath` em todo o processo,
inclusive no pytest ao formatar a falha.

### 3.3 Medição final

Mesmo comando com `--deselect tests/test_core.py::TestCliResolution::test_marker_cli_prefers_project_venv`:

```
26 failed, 2340 passed, 30 skipped, 1 deselected, 3 warnings, 2 errors in 14.13s
```

Os 3 warnings são `PytestRemovedIn10Warning` (iterável `zip` em `parametrize`, em
`tests/test_normalize_consolidation.py`).

## 4. Classificação

Resumo: 1 bloqueio da imagem (2.1); 7 itens por dependência ausente (2 erros de coleta e 5
falhas); 22 só no Linux (21 falhas e o teste deselecionado que derruba o pytest); 30 skips
esperados. Soma das falhas: 5 + 21 = 26. Um item (4.1-e) ficou sem confirmação.

### 4.1 Dependência do ambiente

| # | Teste | Causa |
|---|---|---|
| a | `test_assessment_label_and_plan_section.py`, `test_codes_panel_label.py` (erro de coleta) | Sem `tkinter` |
| b | `test_reprocess_flags.py::test_app_build_options_igual_ao_script_para_o_mesmo_perfil` | Sem `tkinter`; ver 5.1 |
| c | `test_subject_dialog_save.py::test_save_existing_subject_keeps_feature_flags_identical` e `::test_save_new_subject_keeps_empty_feature_flags` | Sem `tkinter`; ver 5.1 |
| d | `test_gemini_generate_text.py::test_generate_text_sends_prompt_and_image_part` | Sem `google-genai` (extra opcional): `src/builder/runtime/gemini_client.py:106` importa `google.genai.types` só no caminho com imagem |
| e | `test_pdf_markdown.py::test_fracao_empilhada_vira_divisao` | **Provável** versão de `pymupdf4llm`, não confirmada. `stacked_fractions` detecta a fração certa, mas `pymupdf4llm.to_markdown` 1.28.2 devolve `'Avaliacao: \n\n\n\nOnde: P1 - prova 1 \n\n'`, sem as linhas da fração, então `splice_fractions` não tem o que trocar. O `pyproject.toml` só fixa mínimo (`>=0.0.10`); a versão da máquina local não é conhecida aqui |

### 4.2 Só no Linux (caminho Windows, comando Windows ou `os.name`)

| # | Teste | Causa |
|---|---|---|
| f | `test_core.py::TestCliResolution::test_marker_cli_prefers_project_venv` | Força `os.name = "nt"` no módulo `os` global; no Linux, `Path()` vira `WindowsPath` e o pytest cai (3.2) |
| g | `test_glossary_structured.py::test_fresh_copy_copies_source_and_propagates_failure` | Chama `robocopy` de verdade (`FileNotFoundError: 'robocopy'`), o mesmo comando de `scripts/ablacao_rapida.py:51` |
| h | `test_moodle_structure.py`: 5 testes (`test_section_and_module_index_follow_moodle_position`, `test_undated_label_does_not_anchor_nor_reset_the_run`, `test_repo_backfill_writes_fields_in_place_and_clears_stale`, `test_regeneration_layer_calls_repo_backfill`, `test_matches_by_stem_when_the_pipeline_changed_the_extension`) | Fixture com `source_path` real `C:\stash\...`; no POSIX a barra invertida não separa partes, então o nome/stem é a string inteira e o casamento com o Moodle falha (`KeyError`) |
| i | `test_moodle_sync.py`: 13 testes (ex.: `test_module_without_entry_is_new_and_url_modules_are_links_not_materials`, `test_plan_ignores_dotfiles_in_ignorados`, `test_pagina_do_moodle_com_html_salvo_vira_entry_html_com_o_mesmo_id`) | Mesma causa: caminhos `C:\stash\...`. Isolado: 13 falham, 13 passam |
| j | `test_section_from_source_path.py::test_lida_com_backslash` | Testa barra invertida explicitamente; devolve `''` em vez de `'Provas por Inducao'` |
| k | `test_stash_import.py::test_id_de_tar_gz_nao_carrega_tar` | Caminho Windows vira id `cstashtcp-chat-c` em vez de `tcp-chat-c` |

Os itens h a k podem ser só da fixture ou também do código de produção (tratar `\` só no Windows).
Este piloto não investigou isso, porque exigiria ler e decidir sobre código fora do escopo.

### 4.3 Dados ausentes, skip esperado (30)

| Teste | Qtde | Motivo |
|---|---|---|
| `test_caracterizacao_blocos_atual.py` | 4 | Sem repositório `*-Tutor` (`TUTOR_REPOS`) |
| `test_pdf_markdown.py` | 3 | PDFs reais ausentes |
| `test_timeline_kinds.py` | 10 | Corpus em `C:\Users\Humberto\Documents\GitHub/<curso>-Tutor/...` |
| `test_timeline_schema.py` | 10 | Mesmo corpus |
| `test_unit_matcher.py` | 2 | Corpus indisponível |
| `test_voter_lock.py:171` | 1 | Só no Linux por projeto: garantia de lock depende do Windows |

Nenhum dado foi criado para contornar skip.

## 5. Achados para decisão do usuário

1. **Vazamento de mock de `tkinter`.** `tests/test_image_curation.py` e
   `tests/test_datalab_captions.py` fazem `sys.modules.setdefault("tkinter", _tk_mock)`. Sem
   `tkinter` real, o mock fica no processo e os testes seguintes importam `src.ui.*` com classes
   falsas. Por isso 4.1-b e 4.1-c aparecem como `AttributeError: Mock object has no attribute
   '_build_options'`/`'_save'` na suíte completa, e como erro de `tkinter` quando rodam isolados. O
   resultado da suíte depende da ordem dos testes. No Windows, com `tkinter` real, o `setdefault`
   não age.
2. **Um teste derruba a suíte no Linux** (4.2-f). Enquanto ele existir assim, nenhuma CI Linux do
   motor passa do primeiro terço.
3. **Setup da nuvem.** Um script de setup precisaria de: `python3.11-tk` (existe no apt:
   `3.11.15-1+noble1`; o `python3-tk` do apt é para o 3.12 e não serve), `cffi` via pip (ou rodar
   com um venv que não enxergue `/usr/lib/python3/dist-packages`), `pip install -e ".[dev]"
   pydantic`, `gitleaks` e a cópia do pre-commit para `.git/hooks`. Nada disso foi aplicado aqui.
4. **Versão de `pymupdf4llm`** (4.1-e): fixar faixa ou adaptar o teste depende de saber a versão
   local em que ele passa.

## 6. Divergências com o guia da nuvem

- [sessao-nuvem.md](../../.mex/context/sessao-nuvem.md) §2 diz "O setup instala o hook". Neste
  container o hook não estava instalado.
- §1: `docs/reports/pendencias.md` deste clone **não** tem o bloco `<!-- fila-campanhas-start -->`,
  e os handoffs de 21 a 23/09 não existem aqui (o mais recente é de 17/09). Pelo guia, o clone está
  atrás da máquina local; por isso esta sessão se limitou a diagnóstico, como o pedido já exigia.
- [setup.md](../../.mex/context/setup.md) (Linux) não menciona o bloqueio do `_cffi_backend` nem o
  pacote `python3.11-tk`.

## 7. O que não foi validado

- Os 2 módulos que dependem de `tkinter` e os 3 testes de 4.1-b/c com `tkinter` real.
- `test_core.py::...test_marker_cli_prefers_project_venv` (deselecionado para a suíte continuar).
- O caminho com imagem do Gemini (sem `google-genai`).
- 4.1-e com outra versão de `pymupdf4llm`.
- Se 4.2-h a k passam no Windows nesta base (não há Windows aqui; presumido pela causa).
- Pre-commit e `gitleaks`: o commit deste relatório foi feito **sem** guarda de segredo. O arquivo
  foi revisado manualmente e não tem segredo.
- Ruff, app (`python app.py`), replay, zero-diff e tudo que usa repositórios-tutor, rede ou LLM.
- Comparação com outra base (`main` ou `feat/motor-atribuicao`).

## 8. Delta proposto ao tracker (não aplicado)

Em `docs/reports/pendencias.md`, na caixa de ideias ou em manutenção:

- "Suíte no Linux: 1 teste derruba o pytest (`os.name` global em `test_core.py`), 21 dependem de
  caminho `C:\...`, `robocopy` ou barra invertida, e o mock de `tkinter` vaza entre módulos. Ver
  `docs/reports/2026-09-24-handoff-nuvem-piloto-ambiente.md`."
- "Setup da nuvem: `python3.11-tk`, `cffi`, `pydantic`, `gitleaks` e instalação do pre-commit."
