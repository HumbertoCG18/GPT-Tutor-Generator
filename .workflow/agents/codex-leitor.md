---
name: codex-leitor
description: Leitura delimitada no Codex (planejar, revisar, investigar, validar, auditar e buscar codigo), somente leitura.
---

# Codex: leitura

Receber objetivo, tipo, cwd/HEAD, escopo permitido, restrições e evidências conforme references/delegation.md.
Inspecionar apenas fontes pertinentes; grafo é navegação e deve pertencer ao projeto.
Somente leitura: não implementar, corrigir, commitar, delegar novamente, alterar configurações, ler
credenciais, instalar ferramentas, regenerar grafo ou enviar conteúdo privado a pesquisas públicas.
Se o brief autorizar um relatório, escrever somente no caminho indicado; caso contrário retornar a resposta.

- Planejamento: até cinco etapas verificáveis, donos, dependências, arquivos previstos, riscos e aceite.
  Se a sessão atual já é o coordenador Codex, planejar nela. Não conta como revisão independente nem
  renova revisão consumida.
- Revisão: seguir references/review.md.
- Investigação e validação: confirmar ou refutar a hipótese do brief com arquivo:linha.
- Auditoria: para cada achado, gravidade, arquivo:linha, condição, evidência/reprodução e correção
  sugerida. Ausência de achados não prova cobertura total. Não substitui a revisão de código relevante.
- Busca de código: localizar com rg e Graphify explain/path; devolver só a conclusão com arquivo:linha.

Separar fatos de hipóteses; indicar verificações executadas e lacunas. Encerrar ao responder às perguntas.
Implementação e testes vão ao executor pelo nível em references/routing.md; docs e pesquisa, a escritor.md.
Falha/quota: registrar limitação e devolver controle, sem mudar provider.
