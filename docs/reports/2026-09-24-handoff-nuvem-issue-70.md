# Handoff nuvem — issue #70, `pydantic` no pyproject do motor (24/09/2026)

## Pedido, issue, base

- Pedido: Gate 1 aprovado no pedido da sessão noturna. Só `pyproject.toml`: acrescentar
  `"pydantic>=2.0"` como último item de `[project] dependencies`, igual à `main`; reproduzir os
  erros de coleta sem `pydantic`, aplicar, reinstalar com `pip install -e ".[dev]"` e comparar a
  suíte com a base.
- Issue: [#70](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/70). O PR usa `Closes #70`.
- Base: `feat/motor-atribuicao` @ `875f97fc5bb42bfa1b26af257305e8bd905fef7d`.
- Branch: `nuvem/2026-09-24-issue-70`.
- Arquivos mudados: `pyproject.toml` (+1 linha) e este relatório.

## Primeira ação da §1 de `sessao-nuvem.md`

| Passo | Resultado |
|---|---|
| `python3 -c "import pydantic, pytest"` | OK, `pydantic` 2.13.5 |
| Hook `pre-commit` | Ausente; instalado com `cp scripts/hooks/pre-commit.sh` + `chmod +x` |
| `/tmp/setup-nuvem.log` | Existe; script rodou como `root` em `/home/user`, terminou sem erro |

`pymupdf4llm` 1.27.2.3, `tkinter` e `gitleaks` ausentes, como na base conhecida.

## Mudança

```diff
     "jsonschema>=4.0.0",
+    "pydantic>=2.0",
 ]
```

Idêntica à linha da `main` (`git show origin/main:pyproject.toml`), na mesma posição, para não
conflitar na integração do PR #9. O mínimo 2.0 é coerente com o código: `model_dump()` em
`src/builder/core/code_summarization.py` e `src/builder/core/reference_summary.py` só existe no
pydantic v2.

## Verificação

Comando de testes do [setup.md](../../.mex/context/setup.md) (Linux), com `-p no:cacheprovider`
para não gravar cache no clone.

| Etapa | Comando | Resultado |
|---|---|---|
| Base, ambiente intacto | suíte | 25 failed, 2341 passed, 30 skipped, 1 deselected, 2 errors |
| Sem `pydantic` | `pip uninstall -y pydantic`; `pytest tests --collect-only -q` | 1635 collected, **47 errors**: 45 `No module named 'pydantic'` + 2 `tkinter` |
| Reinstalação | `pip install -e ".[dev]"` | `Collecting pydantic>=2.0 (from academic-tutor-repo-builder==3.0.0)`; instalou `pydantic-2.13.5` |
| Coleta depois | `pytest tests --collect-only -q` | 2397 collected, 2 errors (só `tkinter`) |
| Suíte depois | suíte | 25 failed, 2341 passed, 30 skipped, 1 deselected, 2 errors |

- `pip freeze` antes × depois: só `pydantic==2.13.5` e o pacote editável entraram. Nada foi
  atualizado.
- Lista de `FAILED`/`ERROR` idêntica à da base, teste a teste (`diff` vazio). Nenhuma falha nova.
  As 25 falhas e 2 erros são os preexistentes do `setup.md` (#68, #69, `google-genai`, `tkinter`).
- `*.egg-info/` gerado pelo editável está no `.gitignore`; `git status` mostra só o `pyproject.toml`.

## O que não foi validado

- Instalação num venv realmente limpo: o ambiente da nuvem já tinha as outras dependências; a prova
  é a do `pydantic` removido e trazido de volta só pela declaração.
- Ruff, app, testes com `tkinter`, replay e tudo que usa tutores, rede ou LLM.
- Commit com hook ativo, mas sem `gitleaks` (o hook só avisa). Diff revisado: sem segredo.

## Estado do ambiente ao sair

`pydantic` 2.13.5 instalado (pela declaração) e o pacote editável `academic-tutor-repo-builder`
apontando para o clone. Sem efeito na suíte, que roda com `pythonpath = ["."]`.

## Delta proposto ao tracker (não aplicado)

- "#70 (24/09, nuvem): `pydantic>=2.0` declarado no `pyproject.toml` do motor, igual à `main`.
  Sem ele, 45 erros de coleta; com `pip install -e \".[dev]\"`, 0. Suíte igual à base. PR em
  rascunho de `nuvem/2026-09-24-issue-70` para `feat/motor-atribuicao`."
- Em `.mex/context/setup.md` e §12 de `sessao-nuvem.md`, após o merge: remover "`pydantic` vai à
  parte" e a lacuna correspondente. Não editado aqui para manter o escopo em `pyproject.toml`.

## Decisões para o usuário

1. Atualizar `setup.md` e `sessao-nuvem.md` depois do merge (item acima), e se o comando Linux do
   `setup.md` deve passar a `pip install -e ".[dev]"` em vez da lista de pacotes avulsos.
