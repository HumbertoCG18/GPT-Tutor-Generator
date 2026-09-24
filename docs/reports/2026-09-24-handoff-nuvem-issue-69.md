# Handoff nuvem — issue #69, mock de `tkinter` sem vazamento (24/09/2026)

## Pedido, issue, base

- Pedido: Gate 1 aprovado no pedido da sessão. Escopo: só `tests/test_image_curation.py`,
  `tests/test_datalab_captions.py` e `tests/test_core.py` (mesmo padrão); nenhum arquivo de `src/`.
  Objetivo: nenhum módulo de teste altera `sys.modules` de forma persistente; o resultado não
  depende da ordem; sem `tkinter`, testes que precisam dele falham ou dão skip por motivo explícito,
  nunca por Mock.
- Issue: [#69](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/69). O PR usa `Closes #69`
  (pedido do usuário); ver a decisão pendente 1.
- Base: `feat/motor-atribuicao` @ `875f97fc5bb42bfa1b26af257305e8bd905fef7d`.
- Branch: `nuvem/2026-09-24-issue-69`.
- Ambiente: Python 3.11.15, `tkinter` ausente, `pydantic`/`pytest` presentes. Hook do pre-commit
  ausente no início; instalado com `cp` + `chmod +x` (§1 de `sessao-nuvem.md`).

## Arquivos mudados

- `tests/test_image_curation.py`, `tests/test_datalab_captions.py`, `tests/test_core.py`: o bloco
  `sys.modules.setdefault("tkinter*", _tk_mock)` no import do módulo virou a fixture `autouse`
  `_tkinter_stub`. Com `tkinter` real (Windows) ela não faz nada. Sem ele, injeta o stub com
  `monkeypatch.setitem` só durante o teste e, ao final, remove de `sys.modules` (e do pacote pai)
  os módulos importados no teste que ficaram presos ao stub: `src.ui.*` e qualquer módulo com
  atributo Mock (medido: `PIL.ImageTk`).
- Este handoff.

## Causa

O `setdefault` no import deixava o `MagicMock` em `sys.modules` pelo resto do processo. Como
`test_core.py` é coletado cedo (ordem alfabética), o mock valia na coleta de todos os módulos
seguintes. Efeitos: módulos que importam `src.ui.*` passavam no Linux só por causa do vazamento, e
os que precisam de classes reais (`SubjectManagerDialog._save`, `App`) quebravam com
`AttributeError: Mock object has no attribute ...`.

## Testes

Comando (setup.md, Linux):
`python3 -m pytest tests -q --continue-on-collection-errors --deselect tests/test_core.py::TestCliResolution::test_marker_cli_prefers_project_venv`
(com `-p no:cacheprovider`). Ordem inversa: a mesma lista de arquivos passada como
`$(ls tests/test_*.py | sort -r)`.

### Vermelho primeiro (antes da mudança)

| Execução | Resultado |
|---|---|
| Os 3 testes isolados | erro de coleta `ModuleNotFoundError: No module named 'tkinter'` |
| `test_image_curation.py` antes dos 3 | 3 failed, `AttributeError: Mock object has no attribute '_save'` |
| Suíte, ordem direta | 25 failed, 2341 passed, 30 skipped, 2 errors (igual à base conhecida) |
| Suíte, ordem inversa | 23 failed, 2300 passed, 30 skipped, 8 errors (depende da ordem) |

### Depois

| Execução | Resultado |
|---|---|
| `test_image_curation.py` antes dos 3 | erro explícito `No module named 'tkinter'`; nenhum Mock |
| Os 3 módulos alterados, direta e inversa | 454 passed nas duas |
| Suíte, ordem direta | 32 failed, 2261 passed, 30 skipped, 23 errors |
| Suíte, ordem inversa | 32 failed, 2261 passed, 30 skipped, 23 errors; **mesmo conjunto** de FAILED/ERROR |
| `ruff check` nos 3 arquivos | 3 achados antes e depois (sem aumento) |

Comparação com a base, por teste:

- Saíram (as 3 falhas do vazamento): `test_reprocess_flags.py::test_app_build_options_igual_ao_script_para_o_mesmo_perfil`
  e `test_subject_dialog_save.py::test_save_{existing,new}_subject_*`. Agora dão erro explícito
  `No module named 'tkinter'` (o módulo `test_subject_dialog_save.py` falha na coleta; o de
  `test_reprocess_flags.py` falha no fixture que resolve `src.ui.theme`).
- As 22 falhas preexistentes restantes (#68, `google-genai`) e os 2 erros de coleta de base
  continuam iguais.
- Entraram 31 itens, **todos** com motivo explícito de ausência de `tkinter`: as linhas `E` são
  só `ModuleNotFoundError: No module named 'tkinter'` e `ImportError: import error in
  src.ui.theme: No module named 'tkinter'` (do `monkeypatch.setattr` com caminho em texto); nenhum
  por Mock nem por outra causa. São testes que importam
  `src.ui.*` e só passavam no Linux pelo vazamento:
  - erro de coleta: `test_feature_flags.py`, `test_repo_dashboard.py`, `test_subject_dialog_save.py`,
    `test_subunit_unit_map.py`, `test_timeline_dashboard_badges.py`, `test_timeline_dashboard_data.py`,
    `test_timeline_entry_label.py`, `test_timeline_sort.py`, `test_ui_queue_dashboard.py`;
  - erro de fixture: os 12 testes de `test_reprocess_flags.py`;
  - falha: 2 de `test_subject_profile_wiring.py`, 2 de `test_tag_catalog.py`, 6 de
    `test_timeline_curation.py`.

## O que não foi validado

- Windows (o usuário valida na revisão). Esperado sem mudança: lá `tkinter` existe, a fixture sai
  no primeiro `if` e nada toca `sys.modules`, como o `setdefault` já não agia.
- Ordem aleatória com plugin (`pytest-randomly` não está instalado); validado com ordem direta e
  inversa dos arquivos.

## Delta proposto ao tracker

- #69: correção entregue no PR em rascunho; aguarda Gate 2 e a decisão 1 abaixo.
- Base Linux do `setup.md` muda para 32 failed, 2261 passed, 30 skipped, 23 errors (sem `tkinter`),
  agora estável em qualquer ordem. Atualizar `setup.md` depois do Gate 2, não nesta sessão.

## Decisões que ficam para o usuário

1. **Conflito no critério de verificação.** O Gate pediu "nenhuma falha nova", mas cumprir o
   objetivo (nenhum `sys.modules` persistente) torna visíveis 31 itens que dependiam do vazamento.
   Todos têm motivo explícito (critério 2 da issue), e o resultado ficou igual nas duas ordens
   (critério 1). Não há como mantê-los verdes dentro do escopo aprovado sem reintroduzir o
   vazamento. Opções: (a) aceitar como está; (b) abrir issue para um `tests/conftest.py` que dê
   skip explícito (`pytest.importorskip("tkinter")` ou marcador) nos módulos de UI e/ou
   compartilhe o stub com escopo por teste; (c) trocar `Closes #69` por `Refs #69` até (b).
   Recomendo (b), com o stub movido para o `conftest.py` e skip nos módulos que precisam de
   classes reais.
2. A fixture está repetida nos 3 arquivos porque o escopo não incluía `conftest.py`; consolidar lá
   junto com (b).
