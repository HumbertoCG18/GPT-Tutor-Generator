# Piloto de recuperação estrutural

Gabarito definido antes da instalação/consulta do candidato. Cópia dos fontes atuais,
não apenas HEAD: manifest.json contém SHA-256 por arquivo. Mesmos arquivos Python
para ambos os índices; exclui documentos, testes, perguntas e gabarito.

12 perguntas: 3 localização, 3 chamadas, 3 caminhos e 3 impacto/referências.
Gabarito: leitura de fonte + validação AST das definições. Chamadas dinâmicas são
condicionais: P3 assume que a fábrica fornece RepoBuilder; não prova execução.

Quatro condições: rg/leitura, Graphify 0.9.42, codebase-memory-mcp, ambos.
Três repetições em ordem alternada, sessões independentes, mesmo modelo e esforço.
Registrar comandos, respostas brutas, erros, latência, tamanho de evidência, uso de
tokens quando disponível. Caracteres NÃO são tokens. Falhas de infraestrutura não
contam como respostas erradas. Comparação de índices e avaliação de agentes são
camadas distintas; não apresentar consultas determinísticas como 144 agentes.

Camada de respostas: 144 sessões novas do Codex recebem pacotes fixos de evidência,
sem chamadas de ferramenta pelo agente. Modelo/esforço lidos da config existente.
Não mede planejamento adaptativo de ferramentas: mede respostas com recuperação
determinística. Limite por pacote: 16.000 caracteres de descoberta + 16.000 de fonte;
no combinado cada grafo recebe 8.000 de descoberta. Fonte: ocorrências dos seeds,
cabeçalhos envolventes e até 120 linhas das definições pedidas. A classe explicitada
na pergunta restringe a leitura. IDs de ambiguidades retornadas pelo Graphify são
resolvidos antes da avaliação. MCP JSON é desembrulhado para texto visível ao agente.
Tempo de consulta é CLI a frio, não latência MCP persistente. Tokens incluem overhead
do Codex; distinguir input bruto, cache e output. Nenhuma consulta ao gabarito na
recuperação ou síntese. Respostas exatas e relações plausíveis não são equivalentes.

Correção do harness durante o piloto: a leitura de fonte passou a respeitar também
nomes de arquivo explicitados na pergunta (C1/C2). Antes, arquivos fora do escopo
consumiam o orçamento e ocultavam linhas relevantes. Regra aplicada aos quatro
braços; 24 pacotes anteriores preservados como *.v1.txt. Gabarito inalterado;
respostas de pacotes com hash diferente são repetidas, sem selecionar acertos.

Segunda correção: reconhecer nomes qualificados pontuados devolvidos por trace_path
e resolver o maior prefixo que corresponda a um arquivo real no snapshot. A versão
inicial só extraía caminhos src/...py e omitia a fonte de chamadores encontrados
pelo CBM. Aplicada ao parser compartilhado, sem usar gabarito. Preservar pacotes e
respostas anteriores; repetir somente hashes alterados. A falha de citação inicial
não deve ser atribuída à resolução do grafo. Grader confere evidência por fato
(definição ou callsite), além de conferir se a linha existe.

Qualidade: precisão/recall do conjunto de símbolos esperado; caminhos também exigem
ordem; registrar evidências e ressalvas. Gabarito nunca entra no índice nem no prompt.
Impacto significa referência sintática dentro do escopo, não garantia de execução.

Proposta aprovada: substituir se qualidade não piorar e tempo ou tokens melhorar
>=20%; manter ambos apenas se resolverem >=2 perguntas adicionais sem mais falsos
positivos. Piloto pequeno, não prova superioridade geral. Comparar apenas execuções
com orçamento e condições equivalentes. Mudança controlada em cópia separada para
testar entrada e saída de uma relação. Não alterar fontes vivos.
