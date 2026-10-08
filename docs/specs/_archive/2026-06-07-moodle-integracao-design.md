# Integração Moodle: onboarding automático de matérias + stash por API

> Design doc. Aprovado em 2026-06-07.

## Goal

Transformar o Moodle (Web Services API, token mobile) na **fonte primária** de
matérias e materiais: o aluno conecta a conta uma vez, escolhe os cursos, e o app
**cria as matérias** (Gerenciador de Matérias) e **baixa os stashes** organizados
por seção (`seção do Moodle = card` do gabarito). O fluxo manual ("Importar do
stash" sobre pasta local) permanece como **fallback**. Elimina a organização
manual de pastas e preenche o gap de arquivos não importados.

## Contexto / decisões (aprovadas)

- **Credencial:** senha NUNCA persiste. Usada uma vez em `login/token.php` pra
  obter o `wstoken`; guarda-se **só o token** num arquivo gitignored
  (`moddle/.env`, `MOODLE_TOKEN=`). Token é revogável e escopado mobile.
- **Seleção de cursos:** o aluno tem ~22 matrículas (inclui lixo: "PUCRS
  Carreiras", "Alunos Politécnica", semestres antigos). App lista todos num
  diálogo com **checkbox**; o aluno marca quais viram matéria.
- **Local do stash:** uma **pasta-base** escolhida 1× (no Gerenciador de Aluno,
  junto da conta Moodle) → `<base>/<slug-da-matéria>/<card>/<arquivos>`. O
  `stash_folder` de cada matéria é setado automaticamente.
- **API primária, manual fallback:** o downloader popula o stash; "Importar do
  stash" (já existente) consome qualquer pasta; o matching lexical segue de
  fallback quando não há card.
- **Re-sync incremental:** download pula arquivos já existentes (idempotente).
- **Validado:** cliente WS + probe + downloader já funcionam (66 arquivos / 8
  seções baixados do curso 92717 = exatamente os cards).

## Arquitetura

```
Gerenciador de Aluno
  └─ seção "Conta Moodle": [matrícula] [senha] [Conectar]  +  [pasta-base]
        │ Conectar
        ▼
  MoodleClient.login(user, pass) ──> wstoken ──> grava moddle/.env (só token; senha descartada)
        │
        ▼
  core_enrol_get_users_courses ──> Diálogo de seleção (checkbox; nome/prof/semestre parseados)
        │ Importar (marcados)
        ▼
  para cada curso:
     parse_moodle_course() ──> upsert SubjectProfile (name, professor, semestre, slug,
                                moodle_course_id, stash_folder=<base>/<slug>)
     MoodleClient.download_course(courseid, <base>/<slug>) ──> <card>/<arquivos> (skip existentes)
        │
        ▼
  Matérias populadas + stashes prontos ──> "Importar do stash" ──> fila ──> pipeline ──> gabarito-cards
```

## Componentes

### 1. `MoodleClient.login(base_url, username, password) -> str`
Único método faltante no cliente (`src/builder/sources/moodle.py`). POST em
`{base}/login/token.php?service=moodle_mobile_app` com `username`/`password`;
retorna o `token` do JSON. Erro (`{"error":...}`) → exceção com a mensagem. A
senha só transita aqui; o chamador grava apenas o token.

### 2. Token store (`moddle/.env`)
Reuso do `.env` gitignored já existente. Helper `save_moodle_token(token)` /
`load_moodle_token()` (lê/escreve `MOODLE_TOKEN` preservando `MOODLE_URL`). Nunca
loga o token. A senha nunca é escrita.

### 3. `parse_moodle_course(course: dict) -> dict` (puro)
Extrai de um curso Moodle os campos pra `SubjectProfile`. O `fullname` segue o
padrão `"CODE - Nome - Turma NNN - YYYY/S - Prof. Fulano"`. Retorna
`{name, professor, semester, slug, moodle_course_id, shortname}`. Robusto a
formatos faltantes (campos vazios quando não casa). `slug` via `slugify` existente.

### 4. `SubjectProfile.moodle_course_id: str = ""`
Novo campo (round-trip como os demais). Liga a matéria ao curso Moodle pra
re-sync futuro e evita duplicar no upsert (casa por `moodle_course_id`, senão por
`slug`/`name`).

### 5. Pasta-base (setting)
Escolhida 1× no Gerenciador de Aluno (junto da conta Moodle). Persistida (no
`StudentProfile` ou config do app — `moodle_base_folder`). Os stashes vão pra
`<base>/<slug>`.

### 6. Upsert de matérias (`import_moodle_courses`, orquestração testável)
Função que, dada a lista de cursos selecionados + pasta-base + client, faz por
curso: `parse_moodle_course` → cria/atualiza `SubjectProfile` no `SubjectStore`
(sem duplicar) com `stash_folder=<base>/<slug>` → `client.download_course`. A
parte de upsert/decisão é pura/testável (recebe um store-like e um client-like);
a rede fica no client. Retorna sumário (criadas/atualizadas/arquivos baixados).

### 7. UI — Gerenciador de Aluno: seção "Conta Moodle"
- Campos matrícula + senha (senha em `show="*"`, nunca persistida).
- Botão **Conectar** → `login` → `save_moodle_token` → `get_users_courses` →
  abre o diálogo de seleção. Mostra estado (conectado como Fulano / token salvo).
- Campo/botão **Pasta-base** (picker de diretório).
- Botão **Reconectar/Atualizar token** (quando expira).

### 8. UI — Diálogo de seleção de cursos
Lista os cursos (checkbox), exibindo `nome | professor | semestre` parseados.
Botão **Importar marcados** → `import_moodle_courses` com barra de progresso
(download pode ser pesado). Roda fora da thread Tk (mesmo padrão do unprocess que
já evita travar a UI).

### 9. Debug CLI
`scripts/moodle_probe.py` (read-only, já existe) + `scripts/moodle_pull.py`
(download, já existe). Adicionar `scripts/moodle_pull.py --login` (ou um
`moodle_login.py`) que cunha o token a partir de user/pass via env/prompt local —
ferramenta de debug isolada, sem tocar a UI.

## Testing

- `parse_moodle_course`: fullname completo → name/professor/semestre corretos;
  fullname degradado (sem "Prof.", sem data) → campos vazios sem crash;
  `moodle_course_id` = `id`.
- `save/load_moodle_token`: round-trip preserva `MOODLE_URL`, grava só token.
- `import_moodle_courses` (com store/client fakes): upsert não duplica (mesmo
  `moodle_course_id` atualiza), seta `stash_folder=<base>/<slug>`, chama
  `download_course` por curso, retorna sumário.
- `MoodleClient.login`: monta a URL/endpoint certo; erro vira exceção (testar com
  client fake / monkeypatch do urlopen, sem rede real).
- `SubjectProfile.moodle_course_id` round-trip.
- UI Tk: não unit-testada (lógica vive nos puros).

## Segurança

- Senha: transitória, só em memória no `login`; nunca escrita, nunca logada.
- Token: arquivo gitignored; tratado como segredo; aviso ao usuário do escopo
  (acesso de aluno à API). Botão de reconectar pra rotacionar.
- Acesso é à conta do PRÓPRIO aluno (perm aluno) — uso legítimo.
- Nunca imprimir token em logs/stdout.

## Fora de escopo

- Sync automático/agendado (só on-demand por enquanto).
- Puxar notas/prazos/quizzes (o amigo já fez metadados; aqui o foco é
  matérias+materiais).
- Refator do pipeline de processamento (continua igual após o import).
- Login SSO/CPF caso a matrícula não passe no token.php (fallback: usuário usa o
  fluxo manual de stash).

## Riscos

- `token.php` pode recusar se o login PUCRS for SSO — mitigar com mensagem clara e
  o fallback manual. (Validado funcionando nesta conta.)
- Token expira → erro nas chamadas; UI deve detectar e pedir reconectar.
- `fullname` fora do padrão → parser retorna campos vazios; usuário edita no
  Gerenciador de Matérias (campos continuam editáveis).
- Download pesado (dezenas de PDFs × N cursos) → rodar off-thread + progresso +
  skip incremental.
- Nome de seção com chars inválidos no Windows → já sanitizado (`sanitize_folder_name`).
