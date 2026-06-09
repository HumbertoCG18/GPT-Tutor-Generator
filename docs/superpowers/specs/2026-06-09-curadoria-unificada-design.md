# Curadoria Unificada: Revisao Manual e Imagens em Uma Janela

## Contexto

Hoje a tela principal expõe dois botoes separados em `src/ui/app.py`:

- `Image Curator`, que abre `src.ui.image_curator.ImageCurator`
- `Curator Studio`, que abre `src.ui.curator_studio.CuratorStudio`

Ambos sao `tk.Toplevel` independentes. O usuario quer uma unica entrada de
curadoria, com duas abas internas, mantendo Revisao Manual como fluxo principal.
O Image Curator deve continuar disponivel, mas com menor peso operacional porque
as descricoes de imagem estao sendo delegadas ao Datalab na maior parte do uso.

## Objetivo

Substituir os dois atalhos de ferramentas por uma unica entrada `Curadoria`,
abrindo uma janela `CurationWorkspace` com abas:

1. `Revisao Manual`, aberta por padrao.
2. `Imagens`, carregada sob demanda quando selecionada.

O comportamento funcional dos dois curadores deve permanecer equivalente ao
atual: aprovar/reprovar revisoes manuais, restaurar pendentes, salvar curadoria
de imagens, gerar descricoes quando a fonte configurada permitir, capturar
regioes e reinjetar descricoes no Markdown.

## Fora de Escopo

- Mesclar os fluxos de revisao manual e imagem em uma lista unica por entry.
- Alterar o pipeline Datalab, Ollama ou a politica de descricao de imagens.
- Redesenhar visualmente os paineis internos alem do necessario para embuti-los.
- Remover suporte standalone imediatamente se ele ainda for util para testes ou
  compatibilidade interna.

## UX

Na barra `Ferramentas`, trocar:

- `Image Curator`
- `Curator Studio`

por:

- `Curadoria`

Ao clicar em `Curadoria`, abrir uma janela com titulo `Curadoria`. A primeira
aba deve ser `Revisao Manual`. A segunda aba deve ser `Imagens`.

A aba `Imagens` deve mostrar um estado leve ate ser selecionada pela primeira
vez. Ao selecionar a aba, o painel de imagens carrega o manifest, as entries e
os recursos visuais. Isso evita custo de I/O e montagem de thumbnails para um
fluxo secundario.

## Arquitetura

Criar `src/ui/curation_workspace.py` com `CurationWorkspace(tk.Toplevel)`.
Responsabilidades:

- resolver tema e `repo_dir`;
- construir `ttk.Notebook`;
- instanciar o painel de Revisao Manual imediatamente;
- instanciar o painel de Imagens apenas no primeiro `<<NotebookTabChanged>>`
  que selecionar a aba `Imagens`;
- preservar status, foco e lifecycle de cada painel sem chamar diretamente
  `RepoBuilder`.

Refatorar `src/ui/curator_studio.py` para expor um painel embutivel:

- `CuratorStudioPanel(ttk.Frame)` contem o estado e UI hoje dentro de
  `CuratorStudio`;
- `CuratorStudio(tk.Toplevel)` pode virar wrapper fino para manter
  compatibilidade, se houver chamadas diretas ou testes que dependam da classe.

Refatorar `src/ui/image_curator.py` da mesma forma:

- `ImageCuratorPanel(ttk.Frame)` contem o estado e UI hoje dentro de
  `ImageCurator`;
- `ImageCurator(tk.Toplevel)` pode virar wrapper fino;
- o carregamento de manifest deve continuar dentro do painel, mas so sera
  acionado quando o workspace instanciar esse painel.

Atualizar `src/ui/app.py`:

- remover os dois botoes antigos;
- adicionar o botao `Curadoria`;
- trocar `open_curator_studio` e `open_image_curator` por
  `open_curation_workspace`, ou manter wrappers apenas se ainda houver
  referencias internas.

## Limpeza Obrigatoria

A implementacao deve limpar o que ficar sobrando pela unificacao:

- remover botoes, labels e comandos antigos da toolbar principal quando nao
  forem mais usados;
- remover metodos de abertura duplicados em `App` se nao tiverem callers;
- remover imports obsoletos gerados pela troca para `CurationWorkspace`;
- consolidar logica duplicada de titulo, geometria, minsize e aplicacao de tema
  nos wrappers standalone;
- evitar duplicar o carregamento de manifest/imagens quando a aba `Imagens` ja
  tiver sido criada;
- revisar testes para nao manter fixtures ou asserts que assumem dois botoes
  separados;
- manter helpers puros existentes se ainda forem usados pelos testes e pelo
  runtime.

Nao remover helpers de negocio ou funcoes puras apenas porque vivem nos arquivos
dos curadores; a limpeza deve mirar sobras de UI/lifecycle criadas pela antiga
separacao em duas janelas.

## Dados e Estado

Nao ha novo formato persistido. A mudanca e de composicao de UI.

Entradas existentes continuam sendo lidas de:

- `manifest.json`
- diretorios `manual-review`
- `content/images`
- campos de configuracao ja existentes, como `image_description_source`

O painel de imagens deve preservar o comportamento DataLab atual: quando a fonte
de descricao for `datalab`, mostrar o banner informando que descricoes sao
geradas na conversao e que a atualizacao exige reprocessamento.

## Tratamento de Erros

Se `repo_dir` nao estiver preenchido, o app deve mostrar uma mensagem unica
referenciando `Curadoria`, nao `Image Curator` ou `Curator Studio`.

Falhas internas de cada painel devem seguir o comportamento atual. O workspace
nao deve mascarar erros nem mudar a semantica de mensagens de salvamento,
aprovacao ou geracao de descricao.

## Testes

Cobertura esperada:

- testes de helpers existentes em `tests/test_image_curation.py` e
  `tests/test_ui_queue_dashboard.py` continuam passando;
- teste leve para o novo workspace validar que a aba `Revisao Manual` e criada
  primeiro e que a aba `Imagens` e lazy;
- teste ou inspeccao direcionada para confirmar que a toolbar principal tem uma
  unica entrada de curadoria;
- se os wrappers standalone forem mantidos, validar que ainda instanciam os
  paineis corretos.

Verificacao final:

```powershell
python -m pytest tests/test_image_curation.py tests/test_ui_queue_dashboard.py -q
```

Se a refatoracao tocar imports ou inicializacao global, rodar:

```powershell
python -m pytest tests -q
```

## Riscos

- `CuratorStudio` e `ImageCurator` hoje herdam de `tk.Toplevel`; mover estado
  para `ttk.Frame` pode expor dependencias implicitas em metodos de janela.
- Bindings globais como `<Delete>`, `<Control-s>` e `<Configure>` precisam ser
  revisados para funcionar corretamente dentro do workspace.
- O Image Curator monta thumbnails e le manifest; se for carregado cedo por
  acidente, a janela de Curadoria perde a vantagem do lazy loading.
- Testes sem UI real podem nao cobrir todos os eventos Tkinter; manter o escopo
  da refatoracao pequeno reduz esse risco.

## Criterios de Aceite

- A toolbar principal mostra um unico botao `Curadoria` no lugar dos dois
  botoes antigos.
- A janela `Curadoria` abre na aba `Revisao Manual`.
- A aba `Imagens` existe, mas so carrega seu painel quando selecionada.
- As acoes existentes dos dois curadores continuam funcionando.
- Sobras da implementacao antiga, especialmente metodos e comandos sem callers,
  foram removidas ou justificadamente mantidas como wrappers de compatibilidade.
- Testes direcionados passam.
