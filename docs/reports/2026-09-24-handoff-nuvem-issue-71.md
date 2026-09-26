# Handoff nuvem — issue #71, faixa do `pymupdf4llm` (24/09/2026)

## Pedido, issue, base

- Pedido: Gate 1 aprovado no pedido da sessão noturna. Reproduzir
  `tests/test_pdf_markdown.py::test_fracao_empilhada_vira_divisao` com `pymupdf4llm` 1.27.2.3 e
  1.28.x no mesmo ambiente; se, e só se, confirmar, declarar `"pymupdf4llm>=0.0.10,<1.28"` e
  registrar o porquê. Sem adaptar `src/`. Restaurar 1.27.2.3 e rodar a suíte contra a base.
- Issue: [#71](https://github.com/HumbertoCG18/GPT-Tutor-Generator/issues/71). O PR usa `Closes #71`.
- Base: `feat/motor-atribuicao` @ `875f97fc5bb42bfa1b26af257305e8bd905fef7d`. Branch criada da
  base, não da #70.
- Branch: `nuvem/2026-09-24-issue-71`.
- Arquivos mudados: `pyproject.toml` (faixa + 1 linha de comentário com o porquê) e este relatório.
- Mesma sessão e ambiente da #70
  ([handoff](2026-09-24-handoff-nuvem-issue-70.md), primeira ação da §1 registrada lá). O ambiente
  já tinha o `pydantic` e o pacote editável instalados pela #70.

## Reprodução

`pymupdf4llm` fixa `pymupdf` e `pymupdf_layout` na mesma versão exata (`Requires-Dist` do wheel),
então trocar o `pymupdf4llm` troca os três. A 1.28.2 também traz `psutil`. Na PyPI, a série 1.28
tem só 1.28.0 e 1.28.2.

| `pymupdf4llm` / `pymupdf` / `pymupdf-layout` | Teste da fração | Suíte (comando do `setup.md`) |
|---|---|---|
| 1.27.2.3 (ambiente original) | passa | 25 failed, 2341 passed, 30 skipped, 2 errors (base) |
| 1.28.0 | **passa** | 25 failed, 2341 passed; lista igual à base |
| 1.28.2 | **falha** | 26 failed, 2340 passed; única falha nova é este teste |

Falha na 1.28.2: `stacked_fractions` ainda detecta `("G1 =", "P1 + P2 + TP", "3")`, mas o
markdown vem como `'Avaliacao: \n\n\n\nOnde: P1 - prova 1 \n\n'`, sem a linha da fração; o
`splice_fractions` não tem o que trocar. Mesmo sintoma descrito na issue.

Conclusão: a reprodução confirma o critério do pedido (passa na 1.27.2.3, falha numa 1.28.x), e a
faixa aprovada foi declarada. A regressão, porém, entrou na 1.28.2, não na 1.28.0; ver decisões.

### Bisseção diagnóstica (fora do pino, só para localizar)

Com `pip install --no-deps`. O `pymupdf4llm` recusa na importação um `pymupdf` de outra versão
(`ImportError: Requires PyMuPDF VERSION='1.28.2'`), então só o `pymupdf-layout` varia sozinho.

| llm / pymupdf | layout | Teste |
|---|---|---|
| 1.28.2 | 1.28.2 | falha |
| 1.28.2 | 1.28.0 | passa |
| 1.28.0 | 1.28.2 | passa |
| 1.28.0 | 1.28.0 | passa |

A saída só perde a fração com os três em 1.28.2. Não dá para separar `pymupdf4llm` de `pymupdf`
por causa da trava de versão.

## Mudança

```diff
-    "pymupdf4llm>=0.0.10",
+    # <1.28: com 1.28.2 a fração empilhada some do markdown (#71).
+    "pymupdf4llm>=0.0.10,<1.28",
```

Nenhum arquivo de `src/` mudou.

## Verificação final

- Ambiente restaurado: `pymupdf4llm`, `pymupdf` e `pymupdf-layout` 1.27.2.3; `psutil` removido.
  `pip freeze` igual ao de antes da #71 (`diff` vazio); `pip check` sem conflito de `pymupdf`.
- `packaging.SpecifierSet(">=0.0.10,<1.28")`: aceita 1.27.2.3; recusa 1.28.0 e 1.28.2.
- `pip install --dry-run -e ".[dev]"`: resolve `pymupdf4llm<1.28,>=0.0.10` para a 1.27.2.3 instalada.
- Suíte com o comando Linux do [setup.md](../../.mex/context/setup.md) (com `-p no:cacheprovider`):
  25 failed, 2341 passed, 30 skipped, 1 deselected, 2 errors; lista de `FAILED`/`ERROR` idêntica à
  base, teste a teste. Nenhuma falha nova.

## O que não foi validado

- Adaptação de `src/` à 1.28.2 (fora do escopo, por pedido).
- Qual dos dois pacotes travados (`pymupdf4llm` ou `pymupdf` 1.28.2) muda a saída.
- Efeito da 1.28.2 em PDFs reais além deste teste (sem PDFs nem tutores na nuvem).
- Durante as duas execuções da suíte com 1.28.x, o proxy registrou 4 conexões recusadas para
  `mobile.events.data.microsoft.com:443`, não vistas na base com 1.27.2.3. A origem não foi
  identificada: o host não aparece em arquivos de texto dos pacotes Python; o `onnxruntime`
  (dependência do `pymupdf-layout`) é suspeita não confirmada.
- Commit com hook ativo, mas sem `gitleaks` (o hook só avisa). Diff revisado: sem segredo.

## Delta proposto ao tracker (não aplicado)

- "#71 (24/09, nuvem): `pymupdf4llm>=0.0.10,<1.28` declarado. Fração empilhada some com 1.28.2
  (passa com 1.27.2.3 e 1.28.0; falha só com `pymupdf`/`pymupdf4llm`/`pymupdf-layout` todos em
  1.28.2). Adaptação à 1.28 pendente de decisão. PR em rascunho de `nuvem/2026-09-24-issue-71`."

## Decisões para o usuário

1. **Largura da faixa**: `<1.28` (aprovado e aplicado) exclui também a 1.28.0, que passa na suíte
   inteira. Alternativas: `<1.28.1` ou `!=1.28.2`. Manter `<1.28` é o mais conservador enquanto a
   causa não é conhecida.
2. **Adaptação à 1.28.2**: adaptar `splice_fractions`/extração à nova saída, ou esperar correção a
   montante. Pede issue própria.
3. **Teto do `pymupdf`**: o `pyproject.toml` declara `pymupdf>=1.24.0` sem teto; na prática o
   `pymupdf4llm<1.28` já trava `pymupdf` em 1.27.x pelo pino exato. Decidir se declara explícito.
4. **Após o merge**: o comando Linux do `setup.md` fixa `pymupdf4llm==1.27.2.3` à mão; com a faixa,
   pode passar a depender só do `pyproject.toml`.
5. **Telemetria**: investigar as conexões a `mobile.events.data.microsoft.com` com 1.28.x
   (regime cru pede 0 rede no produto).
