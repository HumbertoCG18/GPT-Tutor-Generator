# Fila de campanhas: detalhes

Movido de [campaigns.md](campaigns.md) (PODA-18, #447). Ler ao gravar o registro (Escrita), registrar ou triar achados, arquivar tarefas, gravar o diário da noite, ajustar vetos ou mudar o gabarito do painel.

## Escrita

- Um coordenador por tarefa e um writer por registro; `estado` relê o arquivo antes de gravar.
- Ler a fila no início/retomada; atualizar ao descobrir pendência e ao concluir tarefa, durante sessão ativa.
- Sessão read-only não escreve: propõe o delta ao coordenador.
- Ideia nova entra como `proposta`, nunca como autoridade para execução. Gates 1/2 permanecem.
- Registro e caixa versionados mudam só no checkout principal e chegam ao tronco por commit `chore(workflow)` feito ali ou por PR `chore(workflow)` que só altera o registro. PR de código nunca altera `.workflow/campanhas.json` nem `.workflow/achados.json`, salvo branch `sync/*`: a cópia viva, ainda sem commit, faria o pull seguinte falhar. O CI de cada projeto reprova (`ci/registry-guard.yml`, copiado sem mudança).
- Antes de puxar o tronco com o registro alterado, commitar o snapshot; conflito nele se resolve no checkout principal, mantendo os dois lados, e `validar` em seguida.
- PR que move arquivo citado no registro (handoff, evidência) lista as trocas de caminho no corpo; depois do merge, o coordenador as aplica no checkout principal e roda `validar`.

## Achados

- Caixa: `.workflow/achados.json` do checkout principal (versionada, mesma trava e escrita atômica do registro). Achado fora da tarefa atual vira uma linha `achado "título" --tipo ideia|bug|risco|divida [--origem TAREFA] [--detalhe T]`, que imprime `ACH-NNNN`; o agente não investiga e segue a tarefa.
- No máximo 3 achados novos por tarefa (`--origem`); título até 100 caracteres, sem duplicar achado não descartado.
- Triagem só quando o usuário pedir ("triar achados"): listar com `achados --novos`, o usuário decide cada um, então `triar ACH-NNNN --virar CAMPANHA [--titulo T] [--nivel Tn]` (cria tarefa `proposta`, origem CODE) ou `--descartar "motivo"`.
- `limpar-achados` remove da caixa os achados com estado diferente de `novo` (mesma trava e escrita atômica) e imprime quantos. O campo `ultimo` de `achados.json` guarda o último número usado, então o id removido nunca é reaproveitado (e `triar` não casa a tarefa antiga); caixa antiga sem o campo usa o maior id. A deduplicação por título deixa de ver os achados removidos.
- `listar --curto` só informa a contagem de achados novos, nunca os títulos.

## Registro: caminhos raros

Movidos da seção Registro de campaigns.md.

- Arquivo: `arquivar` move as tarefas `concluída`/`descartada` (de campanhas paradas há N dias; padrão 0 = todas) para `.workflow/campanhas-arquivo.json` (`{"campanhas": {ID: [tarefa]}}`), sob a mesma trava; a campanha guarda a contagem em `arquivadas` e o progresso não muda. Ids arquivados não se reusam e `estado`/`passo` os tratam como somente leitura.
- Diário da noite: `noite TAREFA --resultado ok|aguarda-voce|falhou|parou --resumo T [--evidencia T]` acrescenta uma entrada em `.workflow/local/noites/<AAAA-MM-DD>.json` do checkout principal (data em que a noite começou: antes de 12:00, ontem); resumo até 120 caracteres; não muda o estado da tarefa. `listar --curto` resume o diário mais recente em "Noite de DD/MM: …".
- Vetos: `.workflow/vetos.json` ao lado do registro lista decisões vigentes (`id`, `fonte`, `palavras`, `janela` opcional, `mensagem`). `validar` imprime `Aviso: TAREFA / veto / fonte: mensagem` para tarefa aberta cujo `titulo` ou `nota` cite uma palavra inteira (sem caixa nem acento) e segue retornando 0; o `verify.py` publica o mesmo em `warnings`. Aviso não bloqueia: "remover o CBM" também casa. Decisão nova que deve ser vigiada entra ali por PR (REC-07, #147).
- Gabarito: o painel do Alethe reimplementa progresso e situação em TS. Ao mudar uma regra, regenerar `bin/fixtures/campanhas.gabarito.json` com `listar --json --registro bin/fixtures/campanhas.exemplo.json` e copiar os dois arquivos para o teste do Alethe; percentual arredonda meio para cima nos dois.
