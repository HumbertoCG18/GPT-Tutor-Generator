# Auditoria da UI assíncrona e movimento — issue #11

Data: 2026-09-19. Base: `origin/main@be0b195`. Escopo: desktop Python/Tkinter;
campanha web C6 apenas como contrato futuro.

## Baseline medido

`src/ui`: 11 arquivos Python, 27 classes, 17 criações de `threading.Thread`, 58 chamadas
`.after(` após a correção e duas `ttk.Progressbar`. A base tinha 59 chamadas `.after(`; a
removida era o loop manual `after(40)` da barra indeterminada.

| Jornada | Idle / empty | Loading / progresso | Success / error | Cancelamento | Decisão |
|---|---|---|---|---|---|
| Build e fila de repositórios | botões ativos; fila vazia recebe mensagem | determinado por item quando há total; fila sem denominador usa modo nativo indeterminado | status, diálogo e log cobrem ambos | cancelar + pausar/retomar | corrigida nesta entrega; submit duplicado bloqueado |
| Processar/reprocessar item | exige seleção; ausência recebe mensagem | indeterminado nativo; status textual mantém significado com movimento reduzido | sucesso, erro e interrupção encerram a barra | cancelar + pausar/retomar | corrigida nesta entrega |
| Moodle/M365 | seleção de cursos; lista vazia bloqueia início | `_busy` quando total é desconhecido; `_progress_to` em M365 com denominador | diálogo final e erro por etapa | não suportado depois do início | manter; cancelamento cooperativo exige mudança do importador |
| HTML/SARC e plano PDF | campos vazios validados | texto persistente + botão de importação desabilitado; sem denominador comum | retorno ou diálogo de erro | não suportado | barra/skeleton não acrescentam informação confiável |
| Resumos de código | ação explícita; sem seleção não inicia | status por item/lote | conclusão e falha parcial no log | não suportado | gap futuro: cancelamento cooperativo, sem redesign agora |
| Descrever/extrair imagens | galeria vazia explícita | status por lote; backend pode não fornecer total estável | conclusão e erro existentes | não suportado | preservar; progresso só quando o backend expuser denominador real |
| Manutenção/sweep | ação manual | log/status textual | resumo final e erro | não suportado | operação curta/administrativa; impedir duplicação antes de animar |
| Preview de imagens/PDF | “Nenhuma visualização disponível” | “Carregando…” + no máximo seis páginas iniciais + “Carregar mais” | preview ou erro registrado | não aplicável | lazy loading já existe; é o único placeholder previsível útil |

## Movimento e acessibilidade

A referência aplicada foi
[`design-motion-principles@4a9ca879`](https://github.com/kylezantos/design-motion-principles/tree/4a9ca879f24a361f4dca4174fe2da0f67b5ddee3/skills/design-motion-principles),
com Emil Kowalski como lente primária (frequência e restrição), Jakub Krehel como secundária
(polimento de produção) e Jhey Tompkins apenas seletivo. Resultado: nenhuma animação de
entrada/saída foi adicionada. A barra indeterminada é movimento funcional, não decorativo.

- `total > 0`: modo `determinate`, máximo real e atualização por item;
- `total == 0`: `ttk.Progressbar` nativa em modo `indeterminate`;
- “Reduzir movimento”: preferência persistida; barra permanece visível e estática, com o
  estado textual como alternativa funcional;
- pausa/cancelamento: `stop()` imediato; retomada só chama `start(50)` quando movimento está
  permitido;
- fim por sucesso, erro ou cancelamento: `stop()`, ocultação e valor zerado;
- nenhum callback manual recorrente, animação decorativa, zoom, bounce ou atraso de teclado.

Skeleton não se aplica ao Tkinter atual: as superfícies são widgets estáticos e a estrutura
não muda durante carga. Simular cartões criaria movimento/complexidade sem melhorar orientação.
Na web C6, usar skeleton apenas para conteúdo assíncrono de estrutura previsível e
`prefers-reduced-motion` para toda transição. O preview pesado já aplica lazy loading real.

## Evidência

- RED: 6 falhas específicas; 13 testes existentes verdes;
- GREEN: `19 passed` em `tests/test_ui_queue_dashboard.py`;
- regressão: `1126 passed, 1 deselected`; o teste excluído de corpus externo já falha em
  `origin/main@be0b195`;
- Ruff: 13 achados nos três módulos UI antes e depois; zero achado novo; teste novo verde;
- cenários: lentidão/indeterminado, movimento reduzido, denominador real, pausa/retomada e
  encerramento comum a sucesso/erro/cancelamento;
- persistência: round-trip de `reduce_motion` em arquivo temporário;
- visual: `motion-audits/academic-tutor-repo-builder-2026-09-19.html` validado em Edge normal
  e com `prefers-reduced-motion=reduce`; captura nativa sintética em
  `.workflow-local/evidence/tk-progress-states.png`, sem dados privados;
- limite: a captura prova o tema nativo apenas no Windows desta entrega, não em todas as versões.

Rollback: reverter o PR restaura a barra anterior e remove a chave. Configurações antigas
continuam válidas porque `reduce_motion=False` é default; configurações novas perdem apenas essa
preferência ao voltar.
