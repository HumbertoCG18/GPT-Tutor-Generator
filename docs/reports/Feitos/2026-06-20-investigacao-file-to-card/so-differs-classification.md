# SO DIFFERS Classification
date: 2026-06-21
analyst: Claude Sonnet 4.6 (read-only, no repo changes)

## Sources used
- `course/CRONOGRAMA_DETALHADO.md`
- `course/.timeline_index.json`

## Session calendar (relevant dates)

| Date    | Block    | Session label (from .timeline_index.json)              | Kind      |
|---------|----------|--------------------------------------------------------|-----------|
| 07/04   | bloco-05 | gerencia do processador sincronizacao e deadlock aula  | class     |
| 09/04   | bloco-05 | gerencia do processador sincronizacao e deadlock aula  | class     |
| 14/04   | bloco-05 | especificacao tp1                                      | class     |
| 16/04   | bloco-05 | especificacao tp1                                      | class     |
| 02/06   | bloco-12 | enunciado do tp2                                       | class     |

## Classification table

| # | entry | DD.MM | is class day? | session topic that day | matches material? | verdict | final placement |
|---|-------|-------|---------------|------------------------|-------------------|---------|-----------------|
| 1 | `0206-laminas-gerencia-de-i-o-livro-texto` | 02/06 | YES (bloco-12) | "enunciado do tp2" — posting of TP2 spec | NO — Gerência de I/O != TP2 announcement | POSTAGEM | bloco-05 (auto_tag) |
| 2 | `0704-laminas-comunicacao-e-sincronizacao` | 07/04 | YES (bloco-05) | "gerencia do processador sincronizacao e deadlock" (unidade-02) | NO — material is unidade-03 IPC-level comunicação e sincronização, not processador/deadlock | POSTAGEM | bloco-07 (auto_tag) |
| 3 | `0904-laminas-semaforos` | 09/04 | YES (bloco-05) | "gerencia do processador sincronizacao e deadlock" (unidade-02) | NO — Semáforos is unidade-03/bloco-07 primitive; session is processador/deadlock | POSTAGEM | bloco-07 (auto_tag) |
| 4 | `14-04-troca-de-mensagens` | 14/04 | YES (bloco-05) | "especificacao tp1" — work specification session | NO — Troca de mensagens != TP1 spec | POSTAGEM | bloco-07 (auto_tag) |
| 5 | `1404-laminas-ipc` | 14/04 | YES (bloco-05) | "especificacao tp1" — work specification session | NO — IPC != TP1 spec | POSTAGEM | bloco-07 (auto_tag) |
| 6 | `0704-exemplo-threads-em-java` | 07/04 | YES (bloco-05) | "gerencia do processador sincronizacao e deadlock" | NO — Threads em Java is bloco-03 content (see CRONOGRAMA_DETALHADO: code listed under 10/03–31/03 block; `07.04` is a Moodle section number, not a date) | POSTAGEM | bloco-03 (auto_tag) |
| 7 | `0206-laminas-mecanismos-de-interrupcao` | 02/06 | YES (bloco-12) | "enunciado do tp2" | NO — Mecanismos de interrupção != TP2 announcement | POSTAGEM | bloco-03 (auto_tag) |
| 8 | `0206-laminas-memoria-virtual-livro-texto` | 02/06 | YES (bloco-12) | "enunciado do tp2" | NO — Memória virtual != TP2 announcement | POSTAGEM | bloco-11 (auto_tag) |

## Summary

All 8 DIFFERS → POSTAGEM. None flip to SESSÃO.

- 0 entries flip to date-based placement.
- 8 entries stay on auto_tag/scorer block.

## Final count

SO authoritative-by-date map = 16 OK + 0 (SESSÃO from DIFFERS) = **16/36**

The 8 DIFFERS all remain at auto_tag placement:
- bloco-07: entries 2, 3, 4, 5
- bloco-05: entry 1 (I/O livro-texto)
- bloco-03: entries 6, 7
- bloco-11: entry 8

## Reasoning notes

**07/04 and 09/04 (bloco-05):** These are genuine class days but cover "gerencia do processador sincronizacao e deadlock" (unidade-02). The materials tagged with these dates (comunicação e sincronização, semáforos, IPC) belong to unidade-03/bloco-07. The date prefix likely reflects a Moodle section or card reorganization where the professor uploaded/moved slides from an earlier block.

**14/04 (bloco-05):** Two sessions labeled "especificacao tp1" — administrative, no thematic content. Materials about Troca de mensagens and IPC cannot anchor to a TP specification session.

**02/06 (bloco-12):** Single session labeled "enunciado do tp2" — another administrative posting day. Three materials with unrelated topics (Gerência de I/O, Mecanismos de interrupção, Memória virtual) all posted on the same date. Classic batch-upload artifact.

**0704-exemplo-threads-em-java (entry 6):** The `07.04` in the filename is a Moodle section number (prefix pattern), not a date. The CRONOGRAMA_DETALHADO.md already correctly lists this code under bloco-03 (10/03–31/03 period). auto_tag bloco-03 is correct.
