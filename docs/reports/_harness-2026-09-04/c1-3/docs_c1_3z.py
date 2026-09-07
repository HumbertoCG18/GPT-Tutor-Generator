"""Registro final (07/09): filtro da descricao de imagem no scorer, reprocess registrado nos 8 e estado das reguas."""
from pathlib import Path

GEN = Path(r"C:\Users\Humberto\Documents\GitHub\GPT-Tutor-Generator")


def edit(p: Path, old: str, new: str) -> None:
    t = p.read_text(encoding="utf-8")
    assert t.count(old) == 1, (p.name, old[:60], t.count(old))
    p.write_text(t.replace(old, new), encoding="utf-8")


# 1) tracker
T = GEN / "docs/reports/pendencias.md"
t = T.read_text(encoding="utf-8")
anchor = "## PISO DE FORCA NA 1a PASSADA — SEM EFEITO, NAO ENTRA"
i = t.index(anchor)
SEC = """## DESCRICAO DE IMAGEM FORA DO SCORER — ENTROU (07/09; decisao do user; gerador `44ed407`)
**Regra:** `entry_signals.texto_para_score` remove os blocos `<!-- IMAGE_DESCRIPTION -->` dentro de
`collect_entry_unit_signals` — o ponto UNICO por onde passam o scorer de unidade (`file_map:486`), o de subunidade
(`file_map:196`) e a propagacao por headings (`resolver_apply:281`). **O markdown entregue ao aluno nao muda**: a descricao
serve para ele entender a figura (confirmado pelo user).
**Raiz (medida antes):** a caption generica do Datalab, em ingles, entra no vocabulario propagado do CURSO — os aliases
nascem dos materiais confiantes — e desvia a subunidade de materiais que NEM TEM imagem. Os dois casos do CG
(`morfologiamatematicapptx`, `aula-gravada`) tinham texto identico com e sem descricao: o efeito era de segunda ordem.
**Medido pela rota real antes de commitar (`mede_filtro_descricao.log`, 6 cursos com gold, tripwire, 0 chamadas):**
materiais 100% certos 245 -> 247/288 · subunidade 193 -> 195/233 · erro confiante 19 -> 18 · fila 91 -> 89; bloco e unidade
inalterados. Suite 2337 + teste novo em `test_stopwords_consolidation.py`.
**Reprocess registrado dos 8 (`reprocess_8_taxonomia.py`, 0 chamadas Gemini, votos estaveis):** subunidade mudou 3, todas no
CG e todas para o gold — `morfologiamatematicapptx` e `aula-gravada` para `segmentacao`, `intro` de `origens` para
`conceitos` (extra aceito do gold); bloco 0, unidade 0; SO e TCC perderam 1 item da fila cada.
**Tutores:** MF `3584f89` · SO `c44640d` · IA `3b7ffbd` · ES2 `3cde146` · TCC `a7a26cd` · LR `ae5fead` · FR `7468cd8` ·
CG `c56b6cb`.
**Reguas no produto depois:** bloco **197/199** conf-err 0 · unidade **183/190** · cobertura 55/57 · subunidade **195/233**
(SO 15/15 · IA 39/39 · ES2 21/28 · TCC 11/11 · MF 51/58 · **CG 58/82**) · fila **27,0/100** (era 27,6).
**Ressalva mantida:** pela regua da secao do professor o CG ia de 14 para 13/30 na medicao de ablacao. A divergencia entre as
duas reguas neste ponto fica registrada; o user decidiu pelo ganho medido no gold, com o efeito real (3 mudancas, 3 certas)
confirmando a direcao.

"""
T.write_text(t[:i] + SEC + t[i:], encoding="utf-8")

# 2) .mex/text-chain
M = GEN / ".mex/context/text-chain.md"
edit(M, """**Medido (`c1-3/ablate_descricoes.py`): remover as descrições MELHORA a atribuição** — produto 245 → 247/288 materiais 100% certos,
subunidade 193 → 195/233, erros confiantes 19 → 18, fila 91 → 89. A descrição genérica em inglês é ruído para o scorer.
Conclusão de arquitetura: a descrição serve ao **aluno**, não ao scorer — o motor deve pontuar o texto sem esses blocos,
mantendo-os no markdown entregue.""",
     """**Resolvido em 07/09 (`entry_signals.texto_para_score`, gerador `44ed407`):** o motor pontua o texto SEM os blocos
`<!-- IMAGE_DESCRIPTION -->`, e o markdown entregue ao aluno continua com eles. O filtro fica em `collect_entry_unit_signals`,
ponto único por onde passam o scorer de unidade, o de subunidade e a propagação por headings.
Medido pela rota real: produto 245 → 247/288 materiais 100% certos, subunidade 193 → 195/233, erros confiantes 19 → 18,
fila 91 → 89; bloco e unidade inalterados. O efeito era de **segunda ordem**: a caption em inglês entrava no vocabulário
propagado do curso e desviava materiais que nem têm imagem — os dois casos do CG tinham texto idêntico com e sem descrição.""")

# 3) .mex/audit
A = GEN / ".mex/context/audit-2026-09-07.md"
edit(A, "## Como não repetir a redescoberta",
     """## Hipóteses refutadas por medição em 07/09 (não reabrir sem dado novo)

- **Regra pai × filho na subunidade** (texto cobre vários filhos → sobe para o pai): 8 configurações simuladas, nenhuma com
  saldo positivo; melhor caso ganha 3 e perde 5. Curso-dependente: MF perde sempre, CG ganha às vezes.
- **Piso de força para a 1ª passada bloquear a 2ª**: sem efeito nenhum. Subunidade 193/233 idêntica em cinco pisos, e com
  piso 3,0 no CG nem as razões mudam. O portão não é o gargalo; o vocabulário é.
- **"A seção nomeia um tópico, logo a unidade é a dona dele"** como decisão: erra 5 em 5 onde há gold. A seção do Moodle não
  é uma partição das unidades (no SO, "Sincronização e Comunicação" abrange três).
- **Zero-pad no número do título da unidade**: quebra o filtro `unit_hint` do glossário, e apelido é o sinal de maior peso da
  subunidade.
- **Número na chave** (título `01 - Nome`, label `3 - 5 - Nome`): geraria slugs `01-metodos-formais` e `5-segmentacao`,
  derrubando golds, pinos e manifest. O padrão de leitura vive em `text/rotulos.py`, na exibição.

## Como não repetir a redescoberta""")
print("docs ok")
