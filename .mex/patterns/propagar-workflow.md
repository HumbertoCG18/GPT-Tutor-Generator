# Propagar o pacote do workflow para outras branches

Usar ao levar `.workflow/`, `.mex/`, instruções das CLIs, `.gitignore` e hooks de uma
branch integrada para as demais. Procedimento de 22/09 (#44, PRs #53 e #55).

1. Levantar cada destino: branch, worktree, alterações sem commit, remoto, PR aberto.
   Worktree com alterações sem commit NÃO recebe: registrar e esperar o dono. O
   fallback do caminho legado (.workflow-local) cobre o estado local até a migração.
2. Base comum com a origem do pacote: `git cherry-pick -x` do intervalo, hooks ativos.
   Conflito só no `.gitignore` por blocos acrescentados: união dos dois lados. Conflito
   em qualquer outro arquivo: abort e passar ao passo 3.
3. Sem base comum (ex.: `main` versus motor): um commit de sincronização, arquivo por
   arquivo, comparando destino, ancestral comum (`git merge-base`) e versão final:
   - ausente no destino ou igual à base anterior: versão final;
   - `git merge-file` limpo: resultado do merge;
   - snapshots de `.workflow/` com hash no manifest: sempre a fonte canônica;
   - conflito em conteúdo de governança que a versão final evolui: versão final, somando
     fatos que só o destino registrava (ex.: linhas do `.workflow/PENDING.md`);
   - destino com versão MAIS NOVA (conferir datas e commits): manter a do destino e
     levá-la de volta à origem depois.
4. `main` só por PR. Antes de qualquer push, `git log origin/<base>..HEAD`: nenhum commit
   de outra frente (`.workflow/references/delivery.md`).
5. Conferir: sem marcadores de conflito, manifest com todos os hashes, `git check-ignore`
   do estado local e das configs pessoais, 0 arquivos em `src/`/`tests/`, commit
   passando pelo `pre-commit` (gitleaks + anti-padrão Gemini).
6. Branches de PR em pausa com versões próprias de `.workflow`/`.mex` recebem o pacote
   pela `main` quando o PR for retomado, não por cherry-pick.
