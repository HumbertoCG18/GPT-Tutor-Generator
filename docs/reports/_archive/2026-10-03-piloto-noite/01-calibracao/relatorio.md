# PILOTO-01: calibração da suíte na worktree noite

Worktree GPT-Tutor-Generator-noite, branch noite/piloto @ 163f779d (sem diff em src/ e tests/ contra 163f779d).
Comando: `python -m pytest tests -q -p no:cacheprovider`.

## Resultado

| | passed | failed | skipped | total | exit |
|---|---|---|---|---|---|
| Base documentada (bf46d51f) | 2447 | 2 | 4 | 2453 | — |
| Tentativa 2 (05:14:32–05:15:36, 58,50 s) | 2448 | 1 | 4 | 2453 | 1 |

Linha-resumo: `1 failed, 2448 passed, 4 skipped in 58.50s` (suite.txt).

## Falhas

| Teste | Classificação |
|---|---|
| test_caracterizacao_blocos_atual.py::test_divisao_de_blocos_atual[Fundamentos-de-Redes-Tutor] | da base |
| test_pdf_markdown.py::test_respect_actualtext_tira_a_flag_e_restaura | da base, **não reproduzida**: passou nesta worktree |

Falhas novas: 0.

A falha de caracterização é a da base: o campo `topico` do bloco esperado ("P1 – unidades 01 a 03 e unidade 04
até a aula de 17/09 (ICMPv4)") difere do gerado ("Conteúdo: unidade-01-…, unidade-02-…, unidade-04-…").
O teste de ActualText passou nas duas tentativas. Hipótese, não medida: depende do ambiente ou é intermitente.
Achado registrado para triagem, sem investigar.

## Tentativas

1. Sessão 3708b792, 05:09:41–05:12:40, exit 1, **sem linha-resumo**: o log para em ~97% (2389/2453).
   Evidência: suite-tentativa1-interrompida.txt. Até esse ponto, o progresso é idêntico ao da tentativa 2
   (uma única F na posição 175). Indício, não confirmado: o pytest foi encerrado junto com a sessão.
2. Sessão c10f3cad, rodada em segundo plano, terminou normalmente (dados acima). Foi repetida para ter linha-resumo,
   não para limpar falha: a mesma falha da base continua.

## git status --porcelain

- Antes (tentativa 1 e tentativa 2): `?? docs/reports/2026-10-03-piloto-noite/`
- Depois: `?? docs/reports/2026-10-03-piloto-noite/`

Só a pasta do piloto foi acrescentada.

## Observação do piloto

- Início: 05:10 (sessão 3708b792); retomada às 05:14 (c10f3cad); fim: 05:17.
- Permissões negadas: nenhuma na sessão c10f3cad. Não há registro sobre a 3708b792.
- Onde travou: a tentativa 1 terminou sem linha-resumo, e o suite.txt dela não permitia cumprir o aceite.
- Desvios do handoff:
  - `-p no:cacheprovider` acrescentado ao comando para não gravar .pytest_cache (feito na sessão 3708b792 e mantido);
  - segunda execução da suíte;
  - suite.txt da tentativa 1 renomeado para suite-tentativa1-interrompida.txt;
  - linha `tentativa:` acrescentada ao suite.txt.
