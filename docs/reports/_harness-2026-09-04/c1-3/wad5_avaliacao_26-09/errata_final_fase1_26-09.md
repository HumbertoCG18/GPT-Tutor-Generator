# Errata final e encerramento documental da Fase 1 (regime VOCAB) — 26/09/2026

**Resultados inalterados.** Esta errata não altera números, veredictos nem artefatos. Os arquivos originais desta pasta
(`relatorio_avaliacao_fase1.md`, `parada_avaliacao_26-09.md`, `avaliacao_espelho_1.json`,
`avaliacao_espelho_2_conferencia.json`, logs, `manifesto_avaliacao_26-09.json`), as sete capturas W-AD5, o congelamento
`3fe5d1ff97258644b3148860cbe235aa3e16acfac91e9a291ea3c3e63a8e355d` e o espelho da régua ficam como estão, com os
hashes originais. Esta errata os complementa; onde houver conflito de redação, vale esta.

Revisão independente: avaliação da Fase 1 **válida com ressalvas**; resultados e veredictos pré-registrados
confirmados.

## Resultado congelado da Fase 1

- **Subunidade primária:** CRU 86/251; VOCAB_LLM histórico 166/251; VOCAB_ATUAL 171/251 (só referência de proveniência
  mista); CTRL_MAIOR 67/251; CTRL_ALEAT_1/2/3 70/82/67.
- **Bloco:** 223/237 em todos os braços.
- **Unidade:** CRU 249/284; VOCAB_LLM 248/284.
- **VOCAB_LLM na primária:** 87 correções e 7 perdas (saldo +80). **Na unidade:** 3 correções e 4 perdas (saldo −1).
- **Veredictos:** A verdadeiro; B não atendido; C (primária > 90%) só no IA.
- **Conclusão:** "sinal exploratório observado; candidato reprovado para integração".

## Correções de redação

**A. LF × CRLF** — substitui, em `relatorio_avaliacao_fase1.md` §0 item 4 e §3, a frase "Confirma, empiricamente, que
ler a régua normalizada (LF) equivale à leitura histórica" e equivalentes:

> A avaliação utilizou os blobs pré-identificados no congelamento. O CRU reproduziu os placares históricos por curso e
> eixo. Isso demonstra compatibilidade dos placares, mas não constitui, sozinho, prova de igualdade integral entre
> todas as representações históricas da régua.

A parada inicial (`parada_avaliacao_26-09.md`: bytes CRLF da cópia de trabalho × blob normalizado) e a autorização
posterior do espelho endereçado por conteúdo fazem parte da proveniência desta avaliação.

**B. Calibração histórica no IA** — substitui, em `relatorio_avaliacao_fase1.md` §4, "Ela remove a proveniência mista e
a calibração no IA antes de qualquer conclusão sobre o compilador":

> A recompilação limpa produzirá sidecars com entradas, prompt, modelo, filtros e respostas rastreáveis, sem o manual
> no carregamento. Ela não elimina o ajuste histórico do compilador nos cursos conhecidos nem demonstra generalização.

Os sete cursos atuais continuam sendo desenvolvimento contaminado.

**C. Mudanças de unidade** — substitui, em `relatorio_avaliacao_fase1.md` §1 (concentração, unidade) e §3 (último
item), as frases que tratam as mudanças de unidade como "efeito comum aos braços com taxonomia reconstruída" e "comum a
todos os braços":

> Algumas transições de unidade, inclusive as perdas opengl-*, se repetem nos braços examinados. Essa repetição sugere
> um componente compartilhado do efeito, mas o experimento não isolou sua causa.

**Isso não altera o veredicto B:** as perdas de unidade continuam contando integralmente contra o aceite.

## Encerramento

A Fase 1 histórica está encerrada documentalmente. Nenhuma nova interpretação por ID foi feita além destas correções
de redação.
