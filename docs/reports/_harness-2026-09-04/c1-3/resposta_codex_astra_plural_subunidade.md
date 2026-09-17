**Astra LOW: não abrir braço de plural agora. A estimativa de recuperar 1 dos 5 também não se sustenta.**

1. **Aritmética:** nos zips faltou `×0,88` por `auto_tags_text`: resultado `0,12494592`, abaixo do pai `0,9072` ([index.py:1929](src/builder/timeline/index.py#L1929)). **MEDIDO pelo Astra:** carregando `.frzero/base`, `protocolo`, `protocolos` e `redes` são genéricos, excluídos do overlap ([index.py:1862](src/builder/timeline/index.py#L1862)). **HIPÓTESE corrigida: 0 recuperações nesses cinco.** Braço integral não executado.

2. **Não vale agora:** nenhuma recuperação demonstrada; stem6 global já registra regressão ([index.py:142](src/builder/timeline/index.py#L142)). Singularização que deixa `redes→rede` escapar do filtro mistura dois mecanismos: plural + alteração de genéricos.

3. **Próximo mecanismo:** testar propagação que preserva vencedor positivo da primeira passada, mantendo resgate sem sinal. **HIPÓTESE:** recuperar os dois HTTP sem perder os resgates do CG. Evidência registrada: `diagnostico_frzero_13-09.log:31,103` e `2026-09-12-handoff-regime-cru.md:2256`; ganho ainda não medido.

4. **Pai × filho merece diagnóstico próprio:** os quatro zips repetem um padrão de competição entre evidências. Investigar evidência distintiva do filho; quatro arquivos não são quatro validações independentes. Aceite: ganho no FR do zero e nos sete cursos, sem regressão por curso em bloco/unidade.

5. **Não fazer:** stem6 global, bônus incondicional ao filho, remover genéricos para salvar um exemplo ou chamar “erro com plural” de “erro causado pelo plural”.
