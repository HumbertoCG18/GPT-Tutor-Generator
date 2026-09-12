"""Correcao dos registros do C1 item 3 apos o incidente Gemini (60 resumos) e a re-medicao limpa; registro do IDF
intra-unidade (refutado) e da raiz de vocabulario. Idempotente por assert."""
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")


def edit(p: Path, old: str, new: str) -> None:
    t = p.read_text(encoding="utf-8")
    assert t.count(old) == 1, (p.name, old[:70], t.count(old))
    p.write_text(t.replace(old, new), encoding="utf-8")


# ---------- tracker ----------
T = GEN / "docs/reports/pendencias.md"
edit(T, "| subunidade | 82/93 | **81/93** — SO `0704-exemplo-threads-em-java` conceitos-basicos -> escalonamento (0 token perdido; texto combinado) |",
        "| subunidade | 82/93 | **82/93** (a 1a rodada deu 81: era resumo de codigo NOVO do Gemini, nao o title — ver INCIDENTE abaixo) |")
edit(T, "| holdout CG | 31/35, conf-err 0, flag 14 | iguais; 10 subunidades mudam sem gold (4 somem, 3 nascem, 3 trocam) |",
        "| holdout CG | 31/35, conf-err 0, flag 14 | iguais; 2 mudancas sem gold (`intro` sub, `fundamentosmatematicos` metodo); as outras 8 da 1a rodada eram resumo novo |")
edit(T, "**Decisao (registrada em decisions.md):** `title` do manifest FICA o stem;",
        "**INCIDENTE (05/09 tarde): 60 chamadas Gemini NAO autorizadas.** O reprocess (`incremental_build` -> `_run_auto_code_summarization`) re-resume por\n"
        "Gemini todo material de codigo cujo `content_hash` (bundle inclui o `title`) muda, quando a config da UI tem `gemini_auto_summarize=True` + chave\n"
        "(estava: modelo `gemini-3.5-flash`; nao ha interruptor de ambiente). title := label mudou o hash de 60 entries de codigo nas copias (MF 19, SO 8,\n"
        "IA 8, ES2 8, CG 17; 11:45-11:54) e a 1a rodada da B mediu com resumos NOVOS — dai SO sub 81 e as 10 mudancas do CG. Referencias: cache intacto (0\n"
        "diferentes). Originais intactos (0 resumo de hoje). Correcao: tripwire em `c1-3/shim_b.py` (`get_gemini_client` -> None, `GeminiClient.__init__`\n"
        "explode) + `c1-3/check_gemini_hoje.py` como pos-check; B REFEITA LIMPA (0 chamadas, `diff_b2.log`): bloco 184/199 e os 2 confiantes iguais, sub 82 = 82,\n"
        "unidade/cobertura/holdout iguais. **Regra:** todo reprocess (registrado ou de medicao) que mude `title` ou conteudo de codigo chama Gemini com essa\n"
        "config — medir SEMPRE com tripwire, ou desligar `gemini_auto_summarize` na UI enquanto o Gemini estiver bloqueado (decisao do user).\n"
        "**Decisao (registrada em decisions.md):** `title` do manifest FICA o stem;")
edit(T, "**Unica alavanca sem LLM ainda NAO medida:** IDF intra-unidade no scorer de subtopico (causa diagnosticada; teto +4 IA, +1 SO exemplo3; risco nos 35 IA\n"
        "certos) — exige shim no scorer + motor_puro (~5 min). Fora disso, o que sobra e voto (LLM) ou pino (camada humana), por desenho.",
        "**IDF intra-unidade MEDIDO (05/09 tarde, `c1-3/simula_idf_sub.py`: em memoria pela rota real `auto_map_entry_subtopic`, 0 chamadas; base\n"
        "reproduz 92/93 do snapshot):** V1 (tokens do titulo da unidade + tokens em >= 2 irmaos viram genericos) **0 flip** · V2 (V1 + alias repetido ou so\n"
        "de tokens genericos sai) **+1 -5** (+ ES2 `devops` -> `gerenciamento-da-configuracao`, extra do gold; - IA k-means/agrupamento caem em introducao:\n"
        "`Agrupamento` e compartilhado com os aliases-sessao do topico de introducao) · V2s (so alias repetido verbatim em >= 2 irmaos) **0/0**. **REFUTADO.**\n"
        "**Raiz dos 4 do IA e VOCABULARIO, nao scorer:** na copia (motor puro +vocab) `modelos-preditivos` nao tem `perceptron`, `rede neural`, `MLP`, `kNN` —\n"
        "esses termos so existem no glossario MANUAL `.glossary_curation.json` (curadoria 25/08, \"o plano nomeia CATEGORIAS; o material nomeia ALGORITMOS\"),\n"
        "que a ablacao remove; o vocab compilado por LLM tem \"MultiLayer Perceptron\" (frase) e nao o token. Teto da subunidade no motor puro = vocabulario\n"
        "(camada humana, ou re-compilacao por LLM quando liberado). Fora disso, o que sobra e voto (LLM) ou pino (camada humana), por desenho.")

# ---------- handoff ----------
H = GEN / "docs/reports/2026-09-05-handoff-fila-campanhas.md"
edit(H, "   motor puro bloco 186 -> 184/199 (MF, label \"Respostas\" perde `conjuntos`/`arrays`), sub 82 -> 81, 2 confiantes viram flag; holdout CG igual.",
        "   motor puro bloco 186 -> 184/199 (MF, label \"Respostas\" perde `conjuntos`/`arrays`), 2 confiantes viram flag; sub/unidade/holdout iguais (remedido\n"
        "   LIMPO apos o incidente Gemini, ver acima).")
edit(H, "(C1 item 3: piso 0; bloco 186 -> 184, sub 82 -> 81, 2 confiantes\nviram flag;",
        "(C1 item 3: piso 0; bloco 186 -> 184, 2 confiantes\nviram flag, sub/unidade iguais;")
edit(H, "subunidade de codigo de apoio pelo card — nome do card (0 '+', 23 '-') e irmao principal do card (0 '+', 2 '-')\n(§OS 32 ERROS; o scorer de subtopico nao le o card e nao deve) ·",
        "subunidade de codigo de apoio pelo card — nome do card (0 '+', 23 '-') e irmao principal do card (0 '+', 2 '-')\n(§OS 32 ERROS; o scorer de subtopico nao le o card e nao deve) · IDF intra-unidade no scorer de subtopico (V1 0/0, V2 +1/-5, V2s 0/0; a raiz dos 4\ndo IA e vocabulario do glossario MANUAL, camada humana) ·")
edit(H, "pino nao resolver. Custo medido da sessao 04-05/09: travessia 270 chamadas x ~11-13k tokens; voter 23 votos novos; rebuild do CG ~110 chamadas.\n",
        "pino nao resolver. Custo medido da sessao 04-05/09: travessia 270 chamadas x ~11-13k tokens; voter 23 votos novos; rebuild do CG ~110 chamadas.\n"
        "**INCIDENTE 05/09 tarde (sessao 6): 60 chamadas Gemini NAO autorizadas.** O reprocess re-resume codigo por Gemini quando o hash da entry muda\n"
        "(config da UI `gemini_auto_summarize=True` + chave; sem interruptor de ambiente); a medicao title := label nas copias disparou 60 resumos (MF 19,\n"
        "SO 8, IA 8, ES2 8, CG 17). Originais intactos; referencias com cache intacto. Tripwire em `_harness-2026-09-04/c1-3/shim_b.py` + pos-check\n"
        "`check_gemini_hoje.py`. **Regra nova: toda medicao ou reprocess que mude `title`/conteudo de codigo roda com tripwire, ou com\n"
        "`gemini_auto_summarize` desligado na UI** (decisao do user, abaixo). Detalhe no tracker §C1 ITEM 3 (INCIDENTE).\n")
edit(H, "## Decisoes ABERTAS do user (nao travam a campanha 1)\n",
        "## Decisoes ABERTAS do user (nao travam a campanha 1)\n"
        "- **Desligar `gemini_auto_summarize` na UI enquanto o Gemini estiver bloqueado** (incidente de 60 chamadas em 05/09 tarde; sem isso qualquer\n"
        "  reprocess que mude hash de codigo chama a API). O tripwire cobre so as medicoes com o shim.\n")

# ---------- decisions ----------
D = GEN / ".mex/context/decisions.md"
edit(D, "sub 82 -> 81, 2 decisoes confiantes viram flag; holdout CG identico; 0 flip positivo.",
        "2 decisoes confiantes viram flag; subunidade, unidade e holdout CG identicos (remedido limpo, 0 chamadas Gemini, apos o incidente de 60 resumos); 0 flip positivo.")
ENTRY = """

---

### Subunidade do motor puro: IDF intra-unidade refutado; o teto e vocabulario (glossario manual = curadoria); medicao em copia roda com tripwire Gemini

**Date:** 2026-09-05
**Status:** Active
**Decision:** Nao entra IDF intra-unidade no scorer de subtopico. A subunidade do motor puro (82/93) fica como teto de vocabulario: os termos que decidem os 4 notebooks do IA (`perceptron`, `rede neural`, `MLP`, `kNN`) existem so no glossario MANUAL, camada humana que a ablacao remove por desenho. Toda medicao em copia `.ablacao` roda com o tripwire Gemini do `shim_b.py` e o pos-check `check_gemini_hoje.py`.
**Reasoning:** Simulado em memoria pela rota real (base reproduz 92/93): V1 tokens 0 flip; V2 frases +1/-5 (o token `Agrupamento` e compartilhado com aliases-sessao do topico de introducao e V2 tira o dono legitimo); V2s 0/0. Duas variantes de card ja tinham dado 0/+ 23/- e 0/+ 2/-. Incidente: o reprocess chama Gemini para re-resumir codigo quando o hash da entry muda (`gemini_auto_summarize` na UI); a medicao title := label custou 60 resumos nao autorizados e contaminou a 1a rodada (sub 81, CG 10 mudancas); refeita limpa, bloco 184/199 e 2 confiantes iguais, sub 82 = 82.
**Consequences:** §OS 32 ERROS e §C1 ITEM 3 (INCIDENTE) no tracker; NAO fazer do handoff ganha as duas refutacoes; decisao aberta do user: desligar `gemini_auto_summarize` na UI enquanto o Gemini estiver bloqueado. Sem LLM, bloco/unidade/subunidade do motor puro nao sobem: o que resta e voto ou pino.
"""
assert "IDF intra-unidade refutado" not in D.read_text(encoding="utf-8")
D.write_text(D.read_text(encoding="utf-8").rstrip("\n") + ENTRY, encoding="utf-8")

# ---------- padrao + README do harness ----------
P = GEN / ".mex/patterns/medir-alavanca-ablacao.md"
edit(P, "## Gotchas\n",
        "## Gotchas\n"
        "- **O reprocess chama Gemini** (auto-resumo de codigo e referencias, `_run_auto_code_summarization`) para toda entry cujo hash muda quando a UI tem\n"
        "  `gemini_auto_summarize` ligado — 60 chamadas nao autorizadas em 05/09 por title := label. Shim SEMPRE com o tripwire de\n"
        "  `_harness-2026-09-04/c1-3/shim_b.py` e `check_gemini_hoje.py` como pos-check; o tripwire tambem protege a medicao de resumo novo (contaminacao).\n")
R = GEN / "docs/reports/_harness-2026-09-04/c1-3/README.md"
R.write_text(R.read_text(encoding="utf-8").rstrip("\n") + """
- `simula_sub_card.py {A|B}`: subunidade de codigo pelo card (nome / irmao principal) — refutadas (0/+ 23/-; 0/+ 2/-).
- `simula_idf_sub.py <snapshot_antes>` -> `simula_idf_sub.log`: IDF intra-unidade no scorer de subtopico, em memoria pela rota real — refutado
  (V1 0/0, V2 +1/-5, V2s 0/0); raiz dos 4 do IA e vocabulario do glossario manual.
- **Incidente Gemini:** a 1a rodada da B (`b_title_*.log`, `diff_b.log`) disparou 60 resumos de codigo (config `gemini_auto_summarize`); `shim_b.py`
  ganhou tripwire; rodada limpa em `b_title2_*.log` + `diff_b2.log` (0 chamadas, `check_gemini_hoje.py`). Vale a rodada limpa.
""", encoding="utf-8")
print("docs ok")
