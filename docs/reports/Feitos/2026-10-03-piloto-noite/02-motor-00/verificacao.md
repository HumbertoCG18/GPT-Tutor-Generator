# PILOTO-02: preparo do MOTOR-00 (replay_base.json e024d396)

- Origem (somente leitura): `GPT-Tutor-Generator-cru05/docs/reports/2026-10-01-cru05-cru03/replay_base.json`.
  A CRU05 está em fix/cru05-acentos-espacadores @ bf46d51f.
- Destino: `docs/reports/2026-10-01-cru05-cru03/replay_base.json` nesta worktree (noite/piloto @ 163f779d).
  Diretório criado; não existia.

## Verificação

| Checagem | Resultado | Aceite |
|---|---|---|
| sha256 da origem | e024d396bf1cc84c33cc6735718803411cfe6bf2a57a7485501e8c4f81b77dd7 | começa por e024d396bf1cc84c ✔ |
| Cópia | `cp --preserve=timestamps` (binário), exit 0 | — |
| sha256 do destino | e024d396bf1cc84c33cc6735718803411cfe6bf2a57a7485501e8c4f81b77dd7 | = origem ✔ |
| Bytes origem / destino | 63359 / 63359; `cmp` sem diferença | mesmo tamanho ✔ |
| `git check-ignore -v <destino>` | sem saída, exit 1 | não ignorado ✔ |
| `gitleaks dir <destino> --no-banner --redact` (8.30.1) | exit 0, "no leaks found" | 0 ✔ |
| `git -C CRU05 status --porcelain`, antes e depois | idênticos (`cmp`), 3 linhas: ` M src/builder/text/normalize.py`, ` M tests/test_text_normalize.py`, `?? docs/reports/2026-10-01-cru05-cru03/` | idêntico ✔ |

O JSON não foi aberto, reformatado nem usado em replay. Nada foi escrito na CRU05.
Status desta worktree depois da cópia: `?? docs/reports/2026-10-01-cru05-cru03/` e `?? docs/reports/2026-10-03-piloto-noite/`.

## Comando sugerido para o Gate 2 (não executado)

```
git add docs/reports/2026-10-01-cru05-cru03/replay_base.json
git commit -m "docs(motor): versionar a referência de medição replay_base.json (e024d396) - MOTOR-00"
```

A branch onde o commit entra (noite/piloto ou dev) fica a seu critério. O add é do arquivo, não da pasta, para
não levar o restante de 2026-10-01-cru05-cru03/, que só existe na CRU05.

## Observação do piloto

- Início: 05:17; fim: 05:18.
- Permissões negadas: o hook `git-lock.py` (PreToolUse:Bash) bloqueou o comando Bash que gravava este arquivo
  por heredoc. Mensagem: "bloqueado: git add altera o repositório; só git de leitura enquanto durar a trava
  ativa em …\.workflow\local\git-write.lock". Foi falso positivo: o texto `git add` estava dentro do heredoc,
  e nada foi executado. O arquivo foi gravado com a ferramenta Write.
- Onde travou: só nesse bloqueio.
- Desvios do handoff:
  - `cp --preserve=timestamps` em vez de `cp` simples; o conteúdo não muda;
  - `cmp` acrescentado à comparação de bytes;
  - o `git status` da CRU05 rodou sem `GIT_OPTIONAL_LOCKS=0` e pode ter atualizado o cache de stat do index. Isso
    é metadado do .git, não arquivo da worktree; não medido;
  - diretório de destino criado com `mkdir -p`.

## Gate 2 (03/10, aprovado pelo usuário)

- `aa2e4239` (noite/piloto): o arquivo foi versionado, mas o `* text=auto` gravou o blob com LF (sha256 31d7f9…, 61406 B).
- `f3edbc65`: a regra `-text` no .gitattributes renormalizou o arquivo; o blob em HEAD voltou a ser e024d396bf1cc84c… em qualquer SO.
- PR #93 (issue #92), mergeado na dev em `f8e7406e`. A revisão independente sobre conflito com a campanha MOTOR
  (Alethe job-32, gpt-6.1-sol) não achou conflito no PR. Ressalvas de integração futura: ACH-0005 (CRU05) e ACH-0006 (P1).
