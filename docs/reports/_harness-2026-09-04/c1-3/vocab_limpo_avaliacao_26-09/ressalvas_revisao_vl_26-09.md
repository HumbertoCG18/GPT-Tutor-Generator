# Rodada VOCAB_LIMPO — ressalvas documentais da revisão independente (26/09/2026)

Registradas por exigência do Gate de avaliação condicional (§7), ANTES da abertura da régua. Nenhuma altera a execução,
o código, os artefatos ou os resultados. Prevalecem sobre as formulações correspondentes de
`../vocab_limpo_26-09/relatorio_vocab_limpo.md`, que fica intacto porque o seu hash está em `manifesto_rodada_vl.json`.

A rodada continua descrita como "recompilação limpa e rastreável sobre os mesmos sete cursos de desenvolvimento". Não é
holdout, não é independente, não é não contaminada e não é livre de ajuste ao benchmark.

## A. Rede da geração

Substitui "Rede: um único host resolvido" e qualquer leitura de "firewall":

> A geração restringiu e registrou a resolução de hostname usada pelo caminho normal do SDK Gemini. A instrumentação
> não é uma sandbox de rede e não intercepta toda forma possível de conexão direta por IP.

`compilacao.json` registra um único hostname resolvido (`generativelanguage.googleapis.com`, 1 resolução).

## B. Leituras

Substitui qualquer leitura de log integral de acessos:

> As leituras passaram pelo mecanismo de controle em memória durante a execução; acessos negados e violações relevantes
> foram preservados. O mapa integral de todos os acessos não foi persistido em `compilacao.json`.

`compilacao.json` preserva `negados` (só o `.env` da raiz, sem escrita) e `violacoes` (vazio).

## C. Response bruta

Substitui "requests e responses brutas" e "request/response brutos":

> Serialização preservada da request e do objeto de resposta disponibilizado pelo SDK.

Cada response é o `model_dump(mode="json", exclude_none=True)` do objeto retornado pelo SDK google-genai. Não é prova de
captura dos bytes HTTP originais e não deve ser chamada de "resposta HTTP bruta integral".
