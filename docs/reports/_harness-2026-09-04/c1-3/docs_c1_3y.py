"""Registro (07/09): padronizacao da formatacao (rotulos de leitura), reprocess registrado da taxonomia nos 8 e artefatos atualizados."""
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")


def edit(p: Path, old: str, new: str) -> None:
    t = p.read_text(encoding="utf-8")
    assert t.count(old) == 1, (p.name, old[:60], t.count(old))
    p.write_text(t.replace(old, new), encoding="utf-8")


T = GEN / "docs/reports/pendencias.md"
t = T.read_text(encoding="utf-8")
anchor = "## PADRONIZACAO DA NUMERACAO — CONTRATO ESCRITO + 1 BUG CORRIGIDO"
i = t.index(anchor)
SEC = """## FORMATACAO PADRONIZADA + REPROCESS REGISTRADO DA TAXONOMIA NOS 8 (07/09; user: "padrao para melhor leitura, sem quebrar nem regredir")
**Onde o padrao entrou: na EXIBICAO, nunca na chave.** O user pediu "(numero da unidade - nome)" e "(numero unidade - numero
subunidade - nome)". Medido antes de implementar: por na CHAVE quebra tudo — titulo `01 - Metodos Formais` gera slug
`01-metodos-formais` (em vez de `unidade-01-...`), o que derruba golds de unidade, pinos, manifest e `_unit_number_from_slug`;
label `3 - 5 - Segmentacao` gera slug `5-segmentacao`. Como `code` e `label` ja vivem separados na taxonomia, o rotulo e
COMPOSICAO na hora de exibir: `src/builder/text/rotulos.py` (`rotulo_unidade`, `rotulo_topico`, `mapa_rotulos`), aplicado nas
duas colunas do FILE_MAP (`artifacts/navigation.py`). Sem `code` (IA e LR, planos que nao numeram) mostra so o nome; unidade
fora da taxonomia cai no slug. **FILE_MAP e documento: nunca e lido de volta pelo codigo** (so gerado e copiado para
`.deeptutor/knowledge/`) — conferido antes de trocar a celula.
**Resultado no FILE_MAP:** unidade `unidade-03-processamento-de-imagens-e-visao-computacional` -> `03 - Processamento de Imagens
e Visao Computacional`; subtopico `Segmentacao` -> `3.5 - Segmentacao`.
**Commits do gerador:** `3effde1` (teto de 2 digitos no code), `ba96743` (enfase markdown fora dos rotulos + caixa + percentual),
`53b1659` (rotulos de leitura + 6 assercoes de teste atualizadas). Suite 2337 em todos.
**Zero-pad no numero do titulo: TENTADO e REVERTIDO** — quebra o filtro `unit_hint` de `_glossary_aliases_for_topic` (casa o
titulo contra o "Aparece em:" do GLOSSARY, que traz o texto original) e alias e o sinal de maior peso da subunidade. Teste
vermelho pegou; o motivo esta comentado no codigo.
**REPROCESS REGISTRADO DOS 8 (`c1-3/reprocess_8_taxonomia.py`, tripwire, 0 chamadas Gemini, votos estaveis):** topicos
229 -> 228 (o FR perdeu o fantasma "e Bluetooth)" de code 802.11); **subunidade mudou 1** (CG `elemoculto`: `algoritmo-z-buffer`,
que o gold aceitava como extra, -> `algoritmos-de-remocao-de-elementos-ocultos`, o primario); **unidade 0, bloco 0, revisar 0**
em todos os cursos. Tutores: MF `1c33ca0` · SO `d0c135e` · IA `e1540df` · ES2 `5640abe` · TCC `f296ab3` · LR `3348864` ·
FR `eb347d2` · CG `3775b1a`.
**Reguas depois do reprocess, todas intactas:** bloco 197/199 conf-err 0 · unidade 183/190 · cobertura 55/57 · subunidade
193/233 (SO 15/15 · IA 39/39 · ES2 21/28 · TCC 11/11 · MF 51/58 · CG 56/82) · fila 27,6/100.
**Artefatos republicados:** Matriz de Atribuicao (dados regerados), Razao dos Blocos (regenerada), Placar (gerador, HEADs e o
padrao "ruido fraco e pior que ruido nenhum").

"""
T.write_text(t[:i] + SEC + t[i:], encoding="utf-8")

R = GEN / "docs/reports/_harness-2026-09-04/c1-3/README.md"
R.write_text(R.read_text(encoding="utf-8").rstrip("\n") + "\n- `reprocess_8_taxonomia.py` (reprocess registrado da taxonomia padronizada nos 8) · logs `reprocess_8_taxonomia.log`, `formatacao_taxonomia.log`, `anomalias_numeracao.log`, `numeracao_plano.log`, `unidade_vazia_sub_cheia.log` · `gera_tabela_cenarios.py` + `dados_cenarios.json` (matriz por cenario).\n", encoding="utf-8")

H = GEN / "docs/reports/2026-09-05b-handoff-fila-campanhas.md"
edit(H, "Tutores (06/09 noite, apos o reparo do CG):",
        "Tutores (07/09, apos o reprocess da taxonomia padronizada): **MF `1c33ca0` · SO `d0c135e` · IA `e1540df` · ES2 `5640abe` · TCC `f296ab3` · "
        "LR `3348864` · FR `eb347d2` · CG `3775b1a`** (topicos 229 -> 228, subunidade 1, unidade 0, bloco 0; reguas intactas: 197/199, 183/190, 193/233, fila 27,6). "
        "Historico — Tutores (06/09 noite, apos o reparo do CG):")
print("docs ok")
