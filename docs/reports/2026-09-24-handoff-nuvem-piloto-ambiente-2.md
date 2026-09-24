# Handoff nuvem — piloto de ambiente 2 (24/09/2026)

Só diagnóstico. Nenhum arquivo do projeto foi alterado além deste relatório, e nada foi instalado
no container.

## Pedido, issue, base

- Pedido: fazer a "primeira ação" de [sessao-nuvem.md](../../.mex/context/sessao-nuvem.md) §1
  antes de instalar qualquer coisa e registrar o resultado cru; rodar o comando de testes de
  [setup.md](../../.mex/context/setup.md) (seção Linux) e comparar com a base conhecida; não
  corrigir nada.
- Issues: nenhuma específica deste piloto. Relacionadas e abertas:
  [#68](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/68) (suíte portável no Linux) e
  [#69](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/69) (mock de `tkinter` vaza).
  O PR usa `Refs`, não `Closes`.
- Base: `fix/workflow-claude-code` @ `cb451dbb8825c769d73b1e8745e852bf75ea46a4`.
- Branch: `nuvem/2026-09-24-piloto-ambiente-2`.
- Arquivo mudado: só este.
- Base de comparação: [piloto 1](2026-09-24-handoff-nuvem-piloto-ambiente.md) e a "Base Linux
  conhecida" de `setup.md`.

## 1. Primeira ação (§1), antes de qualquer instalação

Comandos do guia, literais:

| Comando | Resultado cru |
|---|---|
| `python3 -c "import pydantic, tkinter, pytest"` | `ModuleNotFoundError: No module named 'tkinter'`, exit 1 |
| `ls "$(git rev-parse --git-common-dir)/hooks/pre-commit"` | `ls: cannot access '.git/hooks/pre-commit': No such file or directory`, exit 2 |

Detalhe por item:

| Item | Resultado | No piloto 1 |
|---|---|---|
| `tkinter` | Ausente (`No module named 'tkinter'`); nenhum pacote `python3*-tk` no `dpkg -l` | Ausente |
| `pydantic` | **Presente**, 2.13.5 | Ausente |
| `pytest` | **Presente**, 9.1.1 (pytest-cov 7.1.0) | Ausente |
| `gitleaks` | Ausente (`command -v` vazio) | Ausente |
| Pre-commit em `.git/hooks` | Não instalado: só `*.sample`; `core.hooksPath` não definido | Igual |
| Ferramenta `pre-commit` | Ausente | — |
| Python | `3.11.15`, `/usr/local/bin/python3` | Igual |
| `node` | `v22.22.2` | Igual |

Outros pacotes já presentes na imagem: `cffi` 2.1.1, `pymupdf4llm`/`PyMuPDF`/`pymupdf-layout`
1.27.2.3, `pdfplumber` 0.11.10, `pdfminer.six` 20260107, `cryptography` 41.0.7, `ruff` 0.16.8.
`import pdfplumber` passa (o bloqueio do `_cffi_backend` do piloto 1 não ocorre). `pip check`: sem
requisitos quebrados. Ausentes: `google-genai` e o próprio pacote do projeto
(`academic-tutor-repo-builder` não aparece no `pip list`, nem como editável).

Os `dist-info` de `pytest`, `cffi`, `pydantic` e `pymupdf4llm` têm data de 24/09 01:55 (-0300),
o mesmo minuto do clone. Logo, o script de setup do ambiente passou a instalar parte da lista do
`setup.md`, mas não o `python3.11-tk`, não `pip install -e ".[dev]"` e não a cópia do hook. O
repositório não tem hook `SessionStart` que explique isso; a origem é a configuração do ambiente,
fora do repositório.

Conforme o pedido, nada que faltava foi instalado.

### 1.1 Condição de parada da §1

`docs/reports/pendencias.md` deste clone **não** tem o bloco `<!-- fila-campanhas-start -->`
(`grep -c` = 0), e os handoffs de 21 a 23/09 não existem aqui (o handoff mais recente antes deste
piloto é o do piloto 1; antes dele, 17/09). Pela §1, isso já limitaria a sessão a diagnóstico,
que é o que o pedido exige.

## 2. Suíte

### 2.1 Comando do `setup.md`, literal

```
python3 -m pytest tests -q --deselect tests/test_core.py::TestCliResolution::test_marker_cli_prefers_project_venv
```

Resultado: `Interrupted: 2 errors during collection`, 0 testes executados, `1 deselected, 11
warnings, 2 errors in 4.38s`, exit 2. Os dois erros são `ModuleNotFoundError: No module named
'tkinter'`:

- `tests/test_assessment_label_and_plan_section.py:13`
- `tests/test_codes_panel_label.py:1`

O comando documentado só roda a suíte se o `python3.11-tk` (primeira linha do bloco Linux) estiver
instalado. A base conhecida (26/2340/30) foi medida no piloto 1 com `tkinter` ausente e com
`--continue-on-collection-errors`, flag que o comando do `setup.md` não tem. Ver 4.

Dos 11 warnings, 8 são `DeprecationWarning: invalid escape sequence` em
`tests/test_moodle_sync.py` (linhas 234, 264–266) e `tests/test_vocabulary_compile.py` (380–382,
388). Eles só aparecem quando o módulo é compilado pela primeira vez (sem `__pycache__`); na
execução seguinte somem. Os outros 3 são os `PytestRemovedIn10Warning` já conhecidos.

### 2.2 Mesma medição da base

Para comparar com a base, o mesmo comando com a flag usada no piloto 1:

```
python3 -m pytest tests -q -rfEs -p no:cacheprovider --continue-on-collection-errors \
  --deselect tests/test_core.py::TestCliResolution::test_marker_cli_prefers_project_venv
```

```
25 failed, 2341 passed, 30 skipped, 1 deselected, 3 warnings, 2 errors in 13.49s
```

(`-rfEs` e `-p no:cacheprovider` só mudam o relatório e o cache; não mudam o resultado.)

## 3. Comparação com a base conhecida

| | Base (piloto 1) | Agora |
|---|---|---|
| failed | 26 | **25** |
| passed | 2340 | **2341** |
| skipped | 30 | 30 |
| deselected | 1 | 1 |
| errors (coleta) | 2 | 2 |
| warnings | 3 | 3 (11 na primeira compilação) |

### 3.1 Melhorou

- **Ambiente**: `pydantic`, `pytest`, `cffi` e `pymupdf4llm==1.27.2.3` já vêm instalados. Sem
  nenhuma ação manual, não há os 45 erros de coleta por `pydantic` nem a queda da coleta pelo
  `_cffi_backend` (piloto 1, §2.1–2.2).
- **`test_pdf_markdown.py::test_fracao_empilhada_vira_divisao` passa** (isolado: `2 passed, 2
  skipped, 4 deselected`, com `-k fracao`). Com `pymupdf4llm` 1.28.2 ele falhava. Confirma a
  hipótese 4.1-e do piloto 1: a falha era da versão do `pymupdf4llm`. É a única diferença entre
  26 e 25 falhas.

### 3.2 Piorou

- Nenhum teste piorou. Nenhuma falha nova; a lista de falhas é um subconjunto exato da base.
- Não é regressão, mas vale registrar: o comando literal do `setup.md` não chega a rodar testes
  neste ambiente (2.1), porque o ambiente não instala o `python3.11-tk` e o comando não tem
  `--continue-on-collection-errors`.

### 3.3 Continua igual

25 falhas = 1 + 3 + 21, todas já classificadas no piloto 1:

| Grupo | Testes | Causa (piloto 1) |
|---|---|---|
| Sem `tkinter` (coleta) | `test_assessment_label_and_plan_section.py`, `test_codes_panel_label.py` | 4.1-a |
| Mock de `tkinter` vaza ([#69](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/69)) | `test_reprocess_flags.py::test_app_build_options_igual_ao_script_para_o_mesmo_perfil` (`Mock object has no attribute '_build_options'`); `test_subject_dialog_save.py::test_save_existing_subject_keeps_feature_flags_identical` e `::test_save_new_subject_keeps_empty_feature_flags` (`'_save'`) | 4.1-b/c, 5.1. Isolados, os dois módulos caem na coleta por `tkinter`: o resultado ainda depende da ordem |
| Sem `google-genai` | `test_gemini_generate_text.py::test_generate_text_sends_prompt_and_image_part` | 4.1-d |
| `robocopy` ([#68](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/68)) | `test_glossary_structured.py::test_fresh_copy_copies_source_and_propagates_failure` | 4.2-g |
| Caminho `C:\...` (#68) | `test_moodle_structure.py` (5), `test_moodle_sync.py` (13) | 4.2-h/i |
| Barra invertida (#68) | `test_section_from_source_path.py::test_lida_com_backslash`, `test_stash_import.py::test_id_de_tar_gz_nao_carrega_tar` | 4.2-j/k |
| `os.name` global (#68) | `test_core.py::TestCliResolution::test_marker_cli_prefers_project_venv` segue deselecionado | 4.2-f; não rodado |

Skips, mesma distribuição (30): `test_caracterizacao_blocos_atual.py` 4, `test_pdf_markdown.py` 3,
`test_timeline_kinds.py` 10, `test_timeline_schema.py` 10, `test_unit_matcher.py` 2,
`test_voter_lock.py` 1. Nenhum dado foi criado para contornar skip.

Também igual: `gitleaks` e o hook do pre-commit ausentes.

## 4. Divergências com o guia

- `setup.md` (Linux): o comando de testes não reproduz a base documentada sem `tkinter`; a base
  foi medida com `--continue-on-collection-errors`. A base "26 failed, 2340 passed" está
  desatualizada para a imagem atual: com `pymupdf4llm` 1.27.2.3, fica 25/2341.
- `setup.md` (Linux) manda `pip install -e ".[dev]"`; o ambiente não instala o pacote do projeto.
  A suíte roda mesmo assim porque é executada da raiz do repositório.
- `sessao-nuvem.md` §1 diz que no piloto de 24/09 "o script do ambiente não tinha instalado nada".
  Agora ele instala parte da lista (seção 1 acima).
- `sessao-nuvem.md` §2 manda instalar o hook na primeira ação, se ausente. O pedido deste piloto
  proibiu instalar; o hook não foi instalado.

## 5. O que não foi validado

- Qualquer teste com `tkinter` real (os 2 módulos da coleta e os 3 do vazamento).
- `test_core.py::...test_marker_cli_prefers_project_venv` (deselecionado).
- O caminho com imagem do Gemini (sem `google-genai`).
- Se o resultado muda com `pip install -e ".[dev]"` (não instalado, por pedido).
- Ruff, app (`python app.py`), replay, zero-diff, e tudo que usa repositórios-tutor, rede ou LLM.
- Pre-commit e `gitleaks`: este relatório foi commitado **sem** guarda de segredo. O arquivo foi
  revisado manualmente e não tem segredo.

## 6. Delta proposto ao tracker (não aplicado)

Em `docs/reports/pendencias.md`, junto das entradas do piloto 1:

- "Piloto 2 (24/09): a imagem da nuvem já instala `pydantic`, `pytest`, `cffi` e
  `pymupdf4llm==1.27.2.3`; faltam `python3.11-tk`, `gitleaks`, o hook do pre-commit e o pacote
  editável. Suíte: 25 failed, 2341 passed, 30 skipped (a fração empilhada passou). Ver
  `docs/reports/2026-09-24-handoff-nuvem-piloto-ambiente-2.md`."

## 7. Decisões para o usuário

1. **Setup do ambiente**: acrescentar ao script do ambiente `apt-get install -y python3.11-tk`,
   `pip install -e ".[dev]"`, `gitleaks` e a cópia de `scripts/hooks/pre-commit.sh` para
   `.git/hooks/pre-commit`, ou manter esses passos como primeira ação manual da sessão.
2. **`setup.md`**: atualizar a base Linux para 25/2341/30 e decidir se o comando documentado ganha
   `--continue-on-collection-errors` (roda mesmo sem `tkinter`) ou se continua exigindo o
   `python3.11-tk`.
3. **`pymupdf4llm`**: o piloto confirma que 1.28.2 quebra `test_fracao_empilhada_vira_divisao` e
   1.27.2.3 passa. Fixar uma faixa no `pyproject.toml` ou adaptar o código fica para issue própria.
