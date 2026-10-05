# Revisão independente do P1 (#90): job-30 (run-15), papel reviewer, 02/10/2026

O texto final entregue pelo worker (`alethe_check`, outcome `succeeded`) está transcrito integralmente abaixo. O conjunto
revisado está em `registros/revisao_conjunto_sha256.txt`; o worker confirmou os 6 hashes e que o diff atual coincide com
o artefato.

---

SEM BLOQUEADOR

Parecer técnico independente; **não é Gate**. Nenhum achado CRITICAL ou MAJOR. Dois MINOR de cobertura de testes.

1. **Contagem por tópico: conforme.** Em index.py:1846, cada tópico contribui no máximo uma vez por `any(...)`; o matcher recebe `(q, k)`, direção correta. Contador e pontuador usam a mesma `_frases_do_topico`: mesma normalização, prioridade label > alias > slug e remoção da chave vazia. Aliases repetidos e slug equivalente ao rótulo não multiplicam chaves.

2. **Divisão somente no acerto: conforme.** Em index.py:1886, a divisão está dentro do matcher; não há recíproco antecipado. `cpu` tem divisor zero e nunca entra nesse ramo. `exact_hits` continua incrementado uma vez por acerto; penalidades permanecem iguais. Em file_map.py:186, filtro, divisores e pontuação usam o mesmo `topic_index`: nenhum tópico pontuado fica fora de C. Sem unidade vencedora, C contém todos os tópicos; lista vazia retorna antes da pontuação. Não identifiquei caminho ligado legítimo com `KeyError` ou divisão por zero. Uma chamada direta ao pontuador com divisores incompletos poderia falhar, mas o seletor não produz essa combinação.

3. **Recálculo e duas passadas: conforme por inspeção.** file_map.py:203 calcula divisores localmente em cada chamada, depois do filtro; não há cache. A primeira passada chama o callback em resolver_apply.py:561; o mesmo callback segue para a propagação, cuja repontuação recebe a taxonomia copiada e enriquecida em resolver_apply.py:331. Um `partial` do seletor com `divisores_de_frase=_divisores_de_frase`, fornecido nesse ponto comum, alcança ambas as passadas. Não encontrei impedimento nem aplicação fora da subunidade.

4. **Desligado e escopo: conformes no diff.** A extração preserva o bloco anterior. `.items()` percorre os valores na mesma ordem de `.values()`; campos, expressão `weight * factor` e ordem das somas permanecem iguais com `None`. Busca em `src` e `scripts` não encontrou chamador de produção passando os novos parâmetros. Unidade continua usando `stem_fallback=True` sem divisor em file_map.py:545; bloco × tópico também não recebe divisor em index.py:2018. Tokens, penalidades, propagação, seção, título e limiares não foram alterados. **Conferido:** seis SHA-256 coincidem com o registro; diff atual coincide com o artefato entregue.

5. **Testes: valores esperados coerentes; cobertura parcial.** E1/E2 detectam divisor errado e alteração da contribuição; E1 cobre a preservação das penalidades dependentes de `exact_hits`; E4b detecta divisão antecipada por zero; E7 detecta reutilização dos divisores entre chamadas. Não encontrei esperado numericamente errado.

   - **MINOR — contagem de chaves poderia passar pelos testes.** test_p1_frases_compartilhadas.py:51 e `:113` não incluem duas chaves distintas do mesmo tópico contendo k. Uma implementação que somasse chaves após a deduplicação poderia passar. **Correção mínima:** caso com label e alias distintos contendo k no mesmo tópico, aliases repetidos, slug equivalente e chave vazia; exigir uma contribuição desse tópico.
   - **MINOR — E6 não testa as rotas de unidade e bloco.** test_p1_frases_compartilhadas.py:99 compara padrão com `None` no código atual, sem chamar essas rotas. Vazamento futuro de P1 para elas poderia passar. **Correção mínima:** testes sintéticos das duas rotas com o seletor de subunidade ligado. Também faltam casos do filtro `winning_unit_slug` e da propagação real; E7 usa taxonomias prontas e iterador simulado.

**Não conferido em execução:** o comando autorizado de pytest falhou antes da coleta com `FileNotFoundError: No usable temporary directory found`; nenhum teste executou. A suíte sem regressão nova e os 350/350 idênticos permanecem afirmações do relatório do implementador, não resultados reproduzidos nesta revisão. Não rodei replay, cursos ou gold; não usei rede nem editei arquivos. O estado local da tarefa estava ausente.
