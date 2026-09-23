# Importar cronograma do SARC por URL — Design

date: 2026-06-03
status: aprovado (aguardando review do spec)

## Problema

Hoje, no **Gerenciador de Matérias** (`SubjectManagerDialog`), para preencher o
campo **Cronograma** o usuário abre o `HTMLImportDialog` e **cola o elemento HTML
inteiro** da tabela do cronograma (ex.: SARC/PUCRS, Moodle, Portal). É manual e
propenso a cópia parcial.

O SARC expõe um endpoint de export público por URL, ex.:

```
https://sarc.pucrs.br/Default/Export.aspx?id=<GUID>&ano=2026&sem=1
```

Essa URL é **acessível sem login** (o `id` GUID funciona como token) e retorna a
mesma tabela HTML que o usuário copia à mão.

## Objetivo

Permitir importar o cronograma do SARC **colando a URL** em vez do HTML.
Importação **uma vez** (fetch → converte → preenche o campo; usuário revisa e
salva). Sem persistir a URL, sem rede no build.

## Decisões (do brainstorm)

- **Comportamento:** importar uma vez. A URL **não** é guardada no perfil; sem
  re-sync automático e sem dependência de rede no build.
- **Escopo:** específico do SARC — valida domínio `sarc.pucrs.br`.
- **Entrada:** colar a **URL inteira** do SARC (o exemplo do usuário já é a URL
  completa com `id/ano/sem`). Não pedimos id/ano/sem em campos separados.
- **Abordagem:** A — estender o `HTMLImportDialog` existente (um único lugar para
  "importar cronograma").

## Insight-chave (reuso máximo)

O conversor já existente `parse_html_schedule` (`src/utils/helpers.py:414`) **já
suporta o formato SARC**: detecta a tabela ASP.NET via `_is_aspnet_schedule`
(`dgAulas` / spans `*_lblData`) e converte via `_parse_aspnet_schedule`, lendo
`_lblData`, `_lblDescricao`, `_lblDia`, `_lblAtividade`, `_lblRecursos` e
mapeando cor→kind (prova/suspensão/g2/etc).

Logo, **nenhum parser novo é necessário**. Só falta: buscar o HTML da URL e
passá-lo ao conversor que já existe. `requests` e `beautifulsoup4` já são
dependências do projeto.

## Componentes

### 1. `fetch_schedule_html(url) -> str` (novo, em `src/utils/helpers.py`)

Único propósito: dada uma URL, retornar o HTML cru.

- GET com `requests` (timeout `(connect=10, read=30)`), `raise_for_status()`,
  retorna `response.text`.
- **Não** valida domínio aqui (responsabilidade da UI) nem faz parse — fica
  isolável/testável. Levanta exceção em falha de rede/HTTP (a UI traduz para
  mensagem amigável).
- Reusa o padrão de timeout-tupla introduzido no `datalab_client`.

### 2. UI — `HTMLImportDialog` estendido (`src/ui/dialogs.py:1019`)

- Adiciona no topo um rótulo + `Entry` "URL do SARC (opcional)".
- `_process` passa a:
  1. Se a URL estiver preenchida:
     - valida domínio `sarc.pucrs.br` (senão, `messagebox` de erro e aborta);
     - faz o fetch **em `threading.Thread`** (lição do freeze: rede nunca na UI
       thread), com status "Buscando…" e tratamento de erro via `self.after(...)`;
     - usa o HTML retornado.
  2. Senão, usa o HTML colado (comportamento atual, inalterado).
  3. Em ambos os casos: `parse_html_schedule(html)` → preenche `_syllabus_text`
     (mesma lógica de hoje, incluindo o tratamento de `res.startswith("Erro:")`).
- O label do diálogo deixa claro: "Cole a URL do SARC **ou** o HTML da tabela".

### Fluxo de dados

```
URL (UI) → [valida domínio] → fetch_schedule_html (thread) → html
        → parse_html_schedule (caminho ASP.NET já existente) → markdown
        → _syllabus_text (usuário revisa) → salvar perfil (como hoje)
```

## Tratamento de erros

- Domínio inválido → `messagebox` claro, sem fetch.
- Timeout / HTTP erro / sem rede → `messagebox` com a causa; o campo Cronograma
  fica intocado; UI não trava (fetch em thread).
- `parse_html_schedule` retornando `"Erro: …"` → mesmo `messagebox` de hoje.
- HTML do SARC sem tabela reconhecível → cai no erro do conversor existente.

## Testes

- `fetch_schedule_html`: mock de `requests.get` —
  - sucesso retorna `.text`;
  - timeout/ConnectionError propaga exceção;
  - HTTP 4xx/5xx (via `raise_for_status`) propaga.
- Integração (fetch mockado → `parse_html_schedule`): HTML SARC de fixture
  (tabela `dgAulas` mínima) produz a tabela/linhas Markdown esperadas (reusa o
  caminho ASP.NET).
- Validação de domínio: helper de validação aceita `sarc.pucrs.br`, rejeita
  outros domínios.

## Fora de escopo (YAGNI)

- Persistir a URL no perfil / re-sync automático / fetch no build.
- Suporte a outras instituições além do SARC (o colar-HTML genérico já cobre).
- Parser próprio do formato SARC (o conversor existente já cobre).

## Follow-up (próxima sessão, separado)

Investigar como melhorar a atribuição de arquivos a blocos temporais /
cronograma (continuação do trabalho de block-match). Spec própria.
