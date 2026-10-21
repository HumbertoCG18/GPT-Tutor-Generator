# Enxame experimental

Somente tarefas independentes, até três trabalhadores, sem recursão. Uma cópia por escritor ou arquivos disjuntos; portas, saída de build, bancos e serviços também isolados ou serializados, porque worktree separa só arquivos. Na dúvida sobre conflito entre tarefas, rodar em série. Lockfile e configuração compartilhada têm um único dono; os outros trabalhadores pedem a mudança a ele. Integração serial pelo coordenador. Usar o mesmo modelo e esforço nos braços individual/enxame para avaliar concorrência; trocar por modelo mais barato é outro experimento. Comparar aceite, regressões, tempo de parede e uso reportado. Uma execução por braço não prova confiabilidade geral nem economia de assinatura.

Antes de abrir o enxame, `python bin/campanhas.py sobreposicao [ARQUIVO ...]` lista PRs abertos que tocam os arquivos dos trabalhadores (só leitura; sem argumento, usa o diff da branch contra dev).
