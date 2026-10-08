# Revisão Astra — issue #19

Sessão: `01a0b29e-7f00-71c0-8641-6461748b69b8`

Resultado: **AJUSTE**; manter a rejeição preventiva.

1. Timeout de 1 ms mede o supervisor do harness, não recuperação integral do hook/host.
2. Backup/restauração byte a byte é procedimento sintético, não rollback operacional do produto.
3. Duplicidade agrupava por `source_hook` e hooks existentes não foram executados em coexistência.
4. Stdout agregado e divisão por três não demonstram custo real de contexto nem teto de tokens.
5. Atribuição do segredo por evento precisava aparecer nos artefatos publicados.

Aplicado: nomes/limites estreitados; chave de duplicidade corrigida; coexistência marcada não avaliada; volume renomeado; fontes seguras dos eventos com segredo publicadas no JSON. Conforme contrato, não houve segunda revisão.
