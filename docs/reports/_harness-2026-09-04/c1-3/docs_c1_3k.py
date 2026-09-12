"""Registro (06/09): camada 3 (resumos de codigo) medida — ablacao e substituto deterministico — para a regra do user
'no maximo duas camadas LLM'; e a medicao de '% de similaridade vocab x nome do material'. Tracker + handoff + decisions + README."""
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")


def edit(p: Path, old: str, new: str) -> None:
    t = p.read_text(encoding="utf-8")
    assert t.count(old) == 1, (p.name, old[:60], t.count(old))
    p.write_text(t.replace(old, new), encoding="utf-8")


T = GEN / "docs/reports/pendencias.md"
SEC = """## NO MAXIMO DUAS CAMADAS LLM — CAMADA 3 (RESUMOS DE CODIGO) MEDIDA: ABLACAO E SUBSTITUTO DETERMINISTICO (06/09, sessao 6; DECISAO DO USER)
**Pedido do user:** "quero o motor o mais automatico possivel, LLM para 3 camadas fica pesado, queria deixar no maximo duas"; "nao quero ficar criando
novas rotas para o motor". **Peso medido no produto (8 tutores):** vocab = 1 compilacao por curso · resumos de codigo = 85 (1 por arquivo/zip, cache por
hash, so re-roda se o arquivo mudar) · votos = 205 (1 por material incerto, cache). Curso novo do tamanho do CG: 1 + 17 + 42.
**Ablacao da camada 3 (`c1-3/shim_codigo.py {sem|determ} {puro|holdout}`, copias, tripwire, 0 chamadas; motor puro + vocab + propagacao):**
| regime | bloco (199) | unidade (191) | cobertura (57) | subunidade (93) | holdout CG (35) |
|---|---|---|---|---|---|
| COM resumos do Gemini (referencia, `b_prop_*.log`) | 186 | 183 | 53 | **87** (83 primario) | 31 |
| SEM resumos (`code_curation.json` vazio, `codigo_sem_*.log`) | 186 | 183 | 53 | **71** (67) | 31 |
| substituto deterministico v1: zip/ipynb crus (`codigo_determ_*.log`) | 186 | 183 | 53 | 79 (75) | 31 |
| substituto deterministico v2: os `.md` que o motor JA gera para codigo/zip = o mesmo bundle que o Gemini recebe (`codigo_determ2_*.log`) | 186 | 183 | 53 | 78 (74) | 31 |
**Leitura:** a camada 3 so sustenta a SUBUNIDADE (+16 sobre nada, +8 sobre o melhor substituto); bloco, unidade, cobertura e holdout nao a sentem.
Os 8 que SO o resumo do Gemini acerta (listados na copia, `winner_score`/`empate`): SO threads x3 (empate exato 0,11: 'pthread' esta no vocab mas
empata; o Gemini injeta 'gerenciamento de processos'/'programacao concorrente') · IA perceptron x4 + mlp-xor (na copia 'perceptron' NAO e alias de
`modelos-preditivos`, so 'MultiLayer Perceptron'; o notebook tem 'Generalizacao', alias de `introducao`; o Gemini injeta 'Perceptron'/'Classificacao')
· ES2 roteiro1 (zip Spring: o codigo so tem 'currency/exchange'; o Gemini injeta 'Microsservicos'). Ou seja: o resumo vale pelo VOCABULARIO DE
CATEGORIA que o codigo nao contem — e um remendo da camada 2 (vocab), nao sinal proprio do codigo. Os outros 6 erros sao os mesmos com ou sem Gemini.
**Decisao do user (aberta): qual camada cortar.** Recomendacao com numero: cortar a 3 (menor ganho das tres: +8 sub; vocab vale +57 sub/+10 unidade;
voter vale +7 bloco/+4 holdout) e trocar o PRODUTOR de `code_curation.json` pelo deterministico v2 — mesma rota (`code_curation_signal_text` +
`entry["concepts"]`), produtor diferente, 0 rotas novas; custo -8/93 na subunidade, 0 no resto. Para nao perder os 8 mantendo duas camadas: a
compilacao do vocab (camada 2) passar a ver o bundle de codigo (`vocabulary_compile` le `_entry_markdown_text_for_file_map`, que para zip devolve
vazio) — mesma chamada, mais insumo; exige Gemini para remedir -> decisao 3 do handoff.
**"% de similaridade vocab x nome do material" (pergunta do user; `c1-3/simula_similaridade_nome.py`, 93 pontuaveis, 0 chamadas):** Jaccard de tokens
do nome (title + label) x label do plano (sem LLM): limiar 0,5 -> 9 certos 0 errados 84 sem atribuicao; 0,2 -> 16/1/76. x label + aliases do vocab LLM:
0,5 -> 27/0/66; 0,3 -> 46/3/44; 0,2 -> 63/6/24. `difflib` 0,3 -> 46 certos 41 errados. O scorer do motor (mesma ideia, texto inteiro + pesos): 87 com
vocab, 30 sem. **Leitura:** faz sentido e JA E o que o scorer faz (sobreposicao de tokens material x vocab, por topico); um indice explicito nao
acrescenta informacao — o teto e o vocabulario, nao a funcao de similaridade. Nenhuma rota nova proposta.

"""
edit(T, "## CONTRIBUICAO POR CAMADA (06/09, pedido do user:", SEC + "## CONTRIBUICAO POR CAMADA (06/09, pedido do user:")

H = GEN / "docs/reports/2026-09-05b-handoff-fila-campanhas.md"
edit(H, "unidade de bloco sem evidencia lexical (CG bloco-08; 1 chamada por bloco assim).\n\n## COMECE POR",
        "unidade de bloco sem evidencia lexical (CG bloco-08; 1 chamada por bloco assim).\n"
        "**Camada 3 (resumos de codigo) medida (06/09, tracker §NO MAXIMO DUAS CAMADAS):** so a subunidade a sente: 87 -> 71 sem resumo, 79/78 com substituto\n"
        "deterministico (mesma rota, produtor diferente); bloco/unidade/cobertura/holdout iguais. Os 8 que so o Gemini acerta sao vocabulario de categoria que\n"
        "o codigo nao contem ('classificacao', 'chamadas de sistema', 'microsservicos'). Peso: 85 resumos / 205 votos / 1 vocab por curso nos 8.\n\n## COMECE POR")
edit(H, "   com `label do Moodle` (90/125 votados tem label != title; re-voto <= 90 chamadas). Sem Gemini a C1 nao tem item.\n",
        "   com `label do Moodle` (90/125 votados tem label != title; re-voto <= 90 chamadas). Sem Gemini a C1 nao tem item.\n"
        "   **3b. 'No maximo duas camadas LLM' (user 06/09):** qual cortar. Numeros: vocab +57 sub/+10 unidade · voter +7 bloco/+4 holdout · resumos +8 sub\n"
        "   (0 no resto). Recomendacao: cortar a 3 trocando o produtor de `code_curation.json` pelo deterministico v2 (`c1-3/shim_codigo.py`, -8/93 sub);\n"
        "   ou, para nao perder os 8, a compilacao do vocab ver o bundle de codigo (mesma chamada; exige Gemini para medir).\n")
edit(H, "- Apagar `.ablacao/CG-rebuild` e `CG-export-backup`.",
        "- Qual camada LLM cortar para ficar em duas (COMECE POR 3b). Apagar `.ablacao/CG-rebuild` e `CG-export-backup`.")

D = GEN / ".mex/context/decisions.md"
ENTRY = """

---

### Camada 3 (resumos de codigo por LLM) medida para a regra 'no maximo duas camadas LLM': so a subunidade a sente; substituto deterministico pela mesma rota

**Date:** 2026-09-06
**Status:** Proposed (decisao do user: qual camada cortar)
**Decision:** Medido em copias com tripwire (0 chamadas), motor puro + vocab + propagacao: sem resumos de codigo a subunidade cai 87 -> 71/93; com `code_curation.json` produzido deterministicamente a partir dos `.md` que o motor ja gera (mesmo bundle que o Gemini recebe, mesma rota `code_curation_signal_text`) 78-79/93; bloco 186, unidade 183, cobertura 53 e holdout CG 31/35 iguais nos 4 regimes.
**Reasoning:** Pedido do user: motor o mais automatico possivel, no maximo duas camadas LLM, sem rotas novas. Peso no produto (8 tutores): 1 compilacao de vocab por curso, 85 resumos (1 por arquivo, cache por hash), 205 votos. Ganho por camada: vocab +57 sub/+10 unidade; voter +7 bloco/+4 holdout/conf-err 0; resumos +8 sub e 0 no resto. Os 8 que so o Gemini acerta (SO threads x3, IA perceptron x5, ES2 roteiro1) dependem de vocabulario de categoria que o codigo nao contem ('classificacao', 'chamadas de sistema', 'microsservicos') — o resumo e um remendo da camada 2. "% de similaridade vocab x nome do material" tambem medido: e o que o scorer ja faz; Jaccard >= 0,5 acerta 27/0 mas deixa 66 sem atribuicao; label do plano sem LLM 9/0/84.
**Consequences:** Se o user cortar a camada 3: trocar o produtor de `code_curation.json` (`c1-3/shim_codigo.py` v2 como base), manter a rota; custo -8/93 na subunidade. Alternativa que mantem duas camadas sem perder os 8: compilacao do vocab ver o bundle de codigo (exige Gemini para remedir). Nenhuma rota nova.
"""
assert "Camada 3 (resumos de codigo por LLM) medida" not in D.read_text(encoding="utf-8")
D.write_text(D.read_text(encoding="utf-8").rstrip("\n") + ENTRY, encoding="utf-8")

R = GEN / "docs/reports/_harness-2026-09-04/c1-3/README.md"
R.write_text(R.read_text(encoding="utf-8").rstrip("\n") + "\n- `shim_codigo.py {sem|determ} {puro|auto|holdout|autoholdout}` -> `codigo_{sem,determ,determ2}_*.log`: camada 3 (resumos de codigo) ablada / substituida por produtor deterministico (v2 = `.md` do bundle): sub 87 -> 71 / 79 / 78, resto igual. `simula_similaridade_nome.py`: Jaccard nome x vocab (27/0/66 em 0,5 com aliases; 9/0/84 so plano).\n", encoding="utf-8")
print("docs ok")
