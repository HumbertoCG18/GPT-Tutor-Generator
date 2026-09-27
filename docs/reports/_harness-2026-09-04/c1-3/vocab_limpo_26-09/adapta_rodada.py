"""Gera o harness da rodada limpa a partir do harness congelado da Fase 1 (wad5_25-09), com trocas EXATAS e contadas:
nomes dos braços, fonte do sidecar do VOCAB_LIMPO (recompilação congelada, nunca tutores vivos), mapa de manuais
(nenhum), caminhos de saída e proibições da rodada. Nenhuma lógica de métrica, controle, sorteio, reconstrução,
instrumentação ou validação muda. Uso único; recusa sobrescrever."""
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
W5 = AQUI.parent / "wad5_25-09"
NOVOS = {"CRU": "CRU_LIMPO", "VOCAB_LLM": "VOCAB_LIMPO", "CTRL_MAIOR": "CTRL_MAIOR_LIMPO",
         "CTRL_ALEAT_1": "CTRL_ALEAT_LIMPO_1", "CTRL_ALEAT_2": "CTRL_ALEAT_LIMPO_2", "CTRL_ALEAT_3": "CTRL_ALEAT_LIMPO_3"}


def carrega(nome):
    b = (W5 / nome).read_bytes()
    crlf = b"\r\n" in b
    return b.decode("utf-8").replace("\r\n", "\n"), crlf


def grava(nome, texto, crlf):
    p = AQUI / nome
    if p.exists():
        sys.exit(f"{nome} já existe: não sobrescrevo")
    p.write_bytes((texto.replace("\n", "\r\n") if crlf else texto).encode("utf-8"))


def troca(texto, pares, nome):
    for a, b, n in pares:
        c = texto.count(a)
        if c != n:
            sys.exit(f"{nome}: esperado {n}x, achei {c}x: {a[:80]!r}")
        texto = texto.replace(a, b)
    return texto


def literais(texto, desde=None, exceto=()):
    """Troca literais de braço ("CRU" etc.) a partir da linha que contém `desde`, pulando linhas com trechos de `exceto`."""
    linhas = texto.split("\n")
    ativo = desde is None
    for i, ln in enumerate(linhas):
        if not ativo and desde in ln:
            ativo = True
        if ativo and not any(x in ln for x in exceto):
            for velho, novo in NOVOS.items():
                ln = ln.replace(f'"{velho}"', f'"{novo}"').replace(f"'{velho}'", f"'{novo}'")
            linhas[i] = ln
    return "\n".join(linhas)


# ------------------------------------------------------------------------------------------- comum.py
t, crlf = carrega("comum.py")
t = troca(t, [
    ('"""W-AD5 (25/09): peças comuns da captura e do avaliador.', '"""Rodada VOCAB_LIMPO (26/09): peças comuns da captura e do avaliador.', 1),
    ("Protocolo: docs/reports/2026-09-25-regime-vocab-adendo-fase1-v4.md. Versões anteriores preservadas em ../wad4_25-09/ e\n../wad3_25-09/.",
     "Protocolo: docs/reports/2026-09-26-regime-vocab-recompilacao-limpa.md. Cópia do comum.py congelado da Fase 1\n"
     "(../wad5_25-09/, 04a535b6…) com SÓ nomes de braços, mapa de manuais, liberação e esquemas trocados.", 1),
    ('ESQUEMA_CAPTURA = "wad5-captura-1"', 'ESQUEMA_CAPTURA = "vl-captura-1"', 1),
    ('ESQUEMA_CONGELAMENTO = "wad5-congelamento-1"', 'ESQUEMA_CONGELAMENTO = "vl-congelamento-1"', 1),
    ('BRACOS = ("CRU", "VOCAB_ATUAL", "VOCAB_LLM", "CTRL_MAIOR", "CTRL_ALEAT_1", "CTRL_ALEAT_2", "CTRL_ALEAT_3")',
     'BRACOS = ("CRU_LIMPO", "VOCAB_LIMPO", "CTRL_MAIOR_LIMPO", "CTRL_ALEAT_LIMPO_1", "CTRL_ALEAT_LIMPO_2", "CTRL_ALEAT_LIMPO_3")', 1),
    ('SEMENTES = {"CTRL_ALEAT_1": 1, "CTRL_ALEAT_2": 2, "CTRL_ALEAT_3": 3}',
     'SEMENTES = {"CTRL_ALEAT_LIMPO_1": 1, "CTRL_ALEAT_LIMPO_2": 2, "CTRL_ALEAT_LIMPO_3": 3}', 1),
    ('MANUAL_ESPERADO = {b: {s: (b == "VOCAB_ATUAL" and s in {"CG", "ES2", "IA", "SO", "TCC"}) for s in NOMES} for b in BRACOS}',
     'MANUAL_ESPERADO = {b: {s: False for s in NOMES} for b in BRACOS}   # rodada limpa: nenhum manual em nenhum braço', 1),
    ('# Gate condicional de 25/09 (revisão independente do W-AD4): captura dos sete braços; NÃO libera gold nem avaliação.\n',
     '# Gate 1 de 26/09 (rodada limpa): captura dos seis braços da rodada; NÃO libera gold nem avaliação.\n', 1),
    ('CAPTURA_LIBERADA = frozenset({"CRU", "VOCAB_ATUAL", "VOCAB_LLM", "CTRL_MAIOR", "CTRL_ALEAT_1", "CTRL_ALEAT_2", "CTRL_ALEAT_3"})',
     'CAPTURA_LIBERADA = frozenset({"CRU_LIMPO", "VOCAB_LIMPO", "CTRL_MAIOR_LIMPO", "CTRL_ALEAT_LIMPO_1", "CTRL_ALEAT_LIMPO_2",\n'
     '                              "CTRL_ALEAT_LIMPO_3"})', 1),
    ('        if braco != "CRU" and ver.get("taxonomia_congelada_lida") != []:',
     '        if braco != "CRU_LIMPO" and ver.get("taxonomia_congelada_lida") != []:', 1),
], "comum.py")
grava("comum.py", t, crlf)

# ------------------------------------------------------------------------------------------- captura.py
t, crlf = carrega("captura.py")
t = troca(t, [
    ('"""W-AD5 (25/09): regime VOCAB, Fase 1 — harness v5 (preflights SEM GOLD e captura isolada por braço).',
     '"""Rodada VOCAB_LIMPO (26/09): regime VOCAB — harness da rodada limpa (preflight SEM GOLD e captura isolada por braço).', 1),
    ("Protocolo normativo: docs/reports/2026-09-25-regime-vocab-adendo-fase1-v4.md (bloco NORMATIVO). v4 revisada preservada\n"
     "em ../wad4_25-09/ (congelamento b3254509…); v5 = v4 + os dois ajustes da revisão independente + liberação da captura.",
     "Protocolo normativo: docs/reports/2026-09-26-regime-vocab-recompilacao-limpa.md (bloco NORMATIVO). Cópia do captura.py\n"
     "congelado da Fase 1 (../wad5_25-09/) com SÓ: nomes dos braços, fonte do sidecar do VOCAB_LIMPO (recompilação congelada;\n"
     "tutores vivos não são lidos), nenhum manual, caminhos de saída e proibições da rodada (resultados da Fase 1 por ID).", 1),
    ('BASE = DATA / ".frzero/wad5_25-09"', 'BASE = DATA / ".frzero/vocab_limpo_26-09/captura"', 1),
    ('ADENDO = DATA / "docs/reports/2026-09-25-regime-vocab-adendo-fase1-v4.md"',
     'ADENDO = DATA / "docs/reports/2026-09-26-regime-vocab-recompilacao-limpa.md"\n'
     'VL = DATA / ".frzero/vocab_limpo_26-09"          # recompilação limpa congelada (sidecars, compilação, sanidade)\n'
     'VL_SIDECARS, VL_SANIDADE, VL_COMP, VL_CONG = VL / "sidecars", VL / "sanidade.json", VL / "compilacao.json", VL / "congelamento_recompilacao.json"\n'
     'PROIBIDOS_RODADA = {C13 / "wad5_avaliacao_26-09": "resultados da avaliação da Fase 1 (por ID)",\n'
     '                    DATA / ".frzero/wad5_avaliacao_26-09": "espelho da régua da Fase 1",\n'
     '                    DATA / "docs/reports/pendencias.md": "tracker (contém IDs das perdas da Fase 1)"}', 1),
    ('OUT_JSON, OUT_MD = HERE / "preflight_v5.json", HERE / "preflight_v5.md"',
     'OUT_JSON, OUT_MD = HERE / "preflight_vl.json", HERE / "preflight_vl.md"', 1),
    ('OUT_CAP_JSON, OUT_CAP_MD = HERE / "manifesto_capturas_v5.json", HERE / "capturas_v5.md"',
     'OUT_CAP_JSON, OUT_CAP_MD = HERE / "manifesto_capturas_vl.json", HERE / "capturas_vl.md"', 1),
    ('ORDEM_CAPTURA = ("VOCAB_ATUAL", "VOCAB_LLM", "CTRL_MAIOR", "CTRL_ALEAT_1", "CTRL_ALEAT_2", "CTRL_ALEAT_3")',
     'ORDEM_CAPTURA = ("VOCAB_LIMPO", "CTRL_MAIOR_LIMPO", "CTRL_ALEAT_LIMPO_1", "CTRL_ALEAT_LIMPO_2", "CTRL_ALEAT_LIMPO_3")', 1),
    ('          "test_ajustes_v5.py": HERE / "test_ajustes_v5.py", **HELPERS}',
     '          "test_ajustes_v5.py": HERE / "test_ajustes_v5.py", "test_rodada_limpa.py": HERE / "test_rodada_limpa.py", **HELPERS}', 1),
    # proibições da rodada nas duas configurações de travas
    ('    t.nega(DATA / ".env", "arquivo .env da raiz (pode conter segredos e configuração)")\n    return t',
     '    t.nega(DATA / ".env", "arquivo .env da raiz (pode conter segredos e configuração)")\n'
     '    for alvo, motivo in PROIBIDOS_RODADA.items():\n        t.proibe(alvo, motivo)\n    return t', 2),
    ('    t.permite("referencia", CAP_WAB, *[DATA / p for p in REGUA_MANIFESTOS.values()], somente_leitura=True)',
     '    t.permite("referencia", CAP_WAB, *[DATA / p for p in REGUA_MANIFESTOS.values()], VL_SIDECARS, VL_SANIDADE, VL_COMP,\n'
     '              VL_CONG, somente_leitura=True)', 1),
    # P1: fonte do VOCAB_LIMPO = sidecars da recompilação congelada; nenhum manual
    ('        # P1 proveniência (única leitura dos tutores vivos) e palcos\n'
     '        R["P1_proveniencia"] = proveniencia()\n'
     '        vivos = {}\n'
     '        for sig in K.NOMES:\n'
     '            tutor = ORIG / K.NOMES[sig] / "course"\n'
     '            vivos[sig] = {arq: (read(tutor / arq) if (tutor / arq).is_file() else None) for arq in (LLM, MANUAL)}\n'
     '        travas.permitidos.pop("preparo")\n'
     '        for nome in TUTORES:\n'
     '            travas.proibe(ORIG / nome, "tutor vivo depois do preparo")\n'
     '        manual_real = {b: {s: (b == "VOCAB_ATUAL" and vivos[s][MANUAL] is not None) for s in K.NOMES} for b in K.BRACOS}\n'
     '        ok["P1 inventário de manuais = referência declarada"] = manual_real == K.MANUAL_ESPERADO\n'
     '        exige(ok["P1 inventário de manuais = referência declarada"], f"mudança de insumo: manuais {manual_real[\'VOCAB_ATUAL\']}")\n'
     '        for sig in K.NOMES:\n'
     '            grava_palco("CRU", sig, abrir=abrir)\n'
     '            grava_palco("VOCAB_ATUAL", sig, vivos[sig][LLM], vivos[sig][MANUAL], abrir=abrir)\n'
     '            grava_palco("VOCAB_LLM", sig, vivos[sig][LLM], abrir=abrir)\n',
     '        # P1 fonte do VOCAB_LIMPO: sidecars da recompilação limpa congelada (tutores vivos NÃO são lidos)\n'
     '        travas.permitidos.pop("preparo")\n'
     '        for nome in TUTORES:\n'
     '            travas.proibe(ORIG / nome, "tutor vivo (rodada limpa não lê tutores vivos)")\n'
     '        san, comp, vlc = read(VL_SANIDADE), read(VL_COMP), read(VL_CONG)\n'
     '        exige(san["aprovado"] is True and comp["completa"] is True and san["id_recompilacao"] == comp["id_recompilacao"]\n'
     '              == vlc["id_recompilacao"], "recompilação limpa incompleta, reprovada ou de outro congelamento")\n'
     '        limpo = {}\n'
     '        for sig in K.NOMES:\n'
     '            p = VL_SIDECARS / K.NOMES[sig] / LLM\n'
     '            exige(K.sha_arq(p, abrir) == san["sidecars"][sig]["sha256"], f"{sig}: sidecar VOCAB_LIMPO != congelado")\n'
     '            limpo[sig] = read(p)\n'
     '        R["P1_vocab_limpo"] = {"id_recompilacao": vlc["id_recompilacao"], "sidecars": san["sidecars"]}\n'
     '        for sig in K.NOMES:\n'
     '            grava_palco("CRU_LIMPO", sig, abrir=abrir)\n'
     '            grava_palco("VOCAB_LIMPO", sig, limpo[sig], abrir=abrir)\n'
     '        manual_real = {b: {s: (PALCOS / b / K.NOMES[s] / "course" / MANUAL).exists() for s in K.NOMES} for b in K.BRACOS}\n'
     '        ok["P1 nenhum manual em nenhum palco (mapa declarado)"] = manual_real == K.MANUAL_ESPERADO\n'
     '        exige(ok["P1 nenhum manual em nenhum palco (mapa declarado)"], "manual presente em algum palco")\n', 1),
    ('            "referencias": {"wab_captura_bracos_24-09.json": K.sha_arq(CAP_WAB, abrir)},',
     '            "referencias": {"wab_captura_bracos_24-09.json": K.sha_arq(CAP_WAB, abrir)},\n'
     '            "vocab_limpo": {"id_recompilacao": vlc["id_recompilacao"], "sidecars": san["sidecars"],\n'
     '                            "compilacao_sha256": K.sha_arq(VL_COMP, abrir), "sanidade_sha256": K.sha_arq(VL_SANIDADE, abrir),\n'
     '                            "congelamento_recompilacao_sha256": K.sha_arq(VL_CONG, abrir)},', 1),
    # P2
    ('            sem[sig] = reconstroi(M, root, PALCOS / "CRU" / K.NOMES[sig])',
     '            sem[sig] = reconstroi(M, root, PALCOS / "CRU_LIMPO" / K.NOMES[sig])', 1),
    ('            snaps = {"CRU": congelada[sig]}\n            for b in ("VOCAB_ATUAL", "VOCAB_LLM"):',
     '            snaps = {"CRU_LIMPO": congelada[sig]}\n            for b in ("VOCAB_LIMPO",):', 1),
    ('                if b == "VOCAB_LLM":\n                    rel_llm[sig] = rel',
     '                if b == "VOCAB_LIMPO":\n                    rel_llm[sig] = rel', 1),
    ('        ok["P2 delta não vazio nos braços históricos"] = all(not e[b]["delta_vazio"] for e in R["P2"].values()\n'
     '                                                            for b in ("VOCAB_ATUAL", "VOCAB_LLM"))',
     '        ok["P2 delta não vazio no VOCAB_LIMPO"] = all(not e[b]["delta_vazio"] for e in R["P2"].values()\n'
     '                                                     for b in ("VOCAB_LIMPO",))', 1),
    ('for e in R["P2"].values() for b in ("VOCAB_ATUAL", "VOCAB_LLM"))',
     'for e in R["P2"].values() for b in ("VOCAB_LIMPO",))', 1),
    ('        for b in ("CRU", "VOCAB_ATUAL", "VOCAB_LLM"):\n            fecha_insumos(cong, b)',
     '        for b in ("CRU_LIMPO", "VOCAB_LIMPO"):\n            fecha_insumos(cong, b)', 1),
    # P4, P3, P5, execução e captura
    ('        cru, origem = roda_worker("CRU", "capturar", cong, travas)',
     '        cru, origem = roda_worker("CRU_LIMPO", "capturar", cong, travas)', 1),
    ('            vocab = read(SNAP / "VOCAB_LLM" / sig / "taxonomia.json")',
     '            vocab = read(SNAP / "VOCAB_LIMPO" / sig / "taxonomia.json")', 1),
    ('"indice_igual": idx_id == idx["VOCAB_LLM"][sig]}}', '"indice_igual": idx_id == idx["VOCAB_LIMPO"][sig]}}', 1),
    ('            grava_palco("CTRL_MAIOR", sig, sidecar_de(atrib, tax), abrir=abrir)\n'
     '            com = reconstroi(M, root, PALCOS / "CTRL_MAIOR" / K.NOMES[sig])\n'
     '            grava_snapshot("CTRL_MAIOR", sig, com, indice_unidade(M, root, PALCOS / "CTRL_MAIOR" / K.NOMES[sig], com), abrir)\n'
     '            rec["CTRL_MAIOR"] = {"definicao": info, "verificacao": verifica_controle(atrib, tax, com)}',
     '            grava_palco("CTRL_MAIOR_LIMPO", sig, sidecar_de(atrib, tax), abrir=abrir)\n'
     '            com = reconstroi(M, root, PALCOS / "CTRL_MAIOR_LIMPO" / K.NOMES[sig])\n'
     '            grava_snapshot("CTRL_MAIOR_LIMPO", sig, com, indice_unidade(M, root, PALCOS / "CTRL_MAIOR_LIMPO" / K.NOMES[sig], com), abrir)\n'
     '            rec["CTRL_MAIOR_LIMPO"] = {"definicao": info, "verificacao": verifica_controle(atrib, tax, com)}', 1),
    ('        ok["P3 C: identidade == VOCAB_LLM (taxonomia ordenada e índice)"]', '        ok["P3 C: identidade == VOCAB_LIMPO (taxonomia ordenada e índice)"]', 1),
    ('        ok["P3 CTRL_MAIOR: pares, estrutura e remoções"] = all(r["CTRL_MAIOR"]["verificacao"]["aprovado"] for r in R["P3"].values())',
     '        ok["P3 CTRL_MAIOR_LIMPO: pares, estrutura e remoções"] = all(r["CTRL_MAIOR_LIMPO"]["verificacao"]["aprovado"] for r in R["P3"].values())', 1),
    ('        for b in ("CTRL_MAIOR", *K.SEMENTES):', '        for b in ("CTRL_MAIOR_LIMPO", *K.SEMENTES):', 1),
    ('ok["P5 braços não-CRU não leem a taxonomia congelada"] = all(not P5[b]["taxonomia_congelada_lida"] for b in K.BRACOS if b != "CRU")',
     'ok["P5 braços não-CRU não leem a taxonomia congelada"] = all(not P5[b]["taxonomia_congelada_lida"] for b in K.BRACOS if b != "CRU_LIMPO")', 1),
    ('        if braco != "CRU":\n', '        if braco != "CRU_LIMPO":\n', 1),
    ('        for b in ("CRU", *ORDEM_CAPTURA):   # o CRU é o do preflight v5 (mesmo congelamento), revalidado',
     '        for b in ("CRU_LIMPO", *ORDEM_CAPTURA):   # o CRU_LIMPO é o do preflight desta rodada (mesmo congelamento), revalidado', 1),
    ('        print("preflight_v5.json já existe: preservar evidência (usar nova versão)", flush=True)',
     '        print("preflight_vl.json já existe: preservar evidência (usar nova versão)", flush=True)', 1),
    ('        print("manifesto_capturas_v5.json já existe: preservar evidência", flush=True)',
     '        print("manifesto_capturas_vl.json já existe: preservar evidência", flush=True)', 1),
    ('        ok["preflight v5 aprovado com este congelamento"]', '        ok["preflight da rodada aprovado com este congelamento"]', 1),
    ('        ok["CAPTURA_LIBERADA = os sete braços"]', '        ok["CAPTURA_LIBERADA = os seis braços da rodada"]', 1),
    ('        ok["sete capturas completas, validador completo sem problemas"]', '        ok["seis capturas completas, validador completo sem problemas"]', 1),
    ('    R, ok = {"escopo": "captura dos seis braços não-CRU e validação das sete capturas; sem gold"}, {}',
     '    R, ok = {"escopo": "captura dos cinco braços não-CRU da rodada limpa e validação das seis capturas; sem gold"}, {}', 1),
    ('    L = ["# W-AD5 — captura dos sete braços, sem gold (25/09)",', '    L = ["# Rodada VOCAB_LIMPO — captura dos seis braços, sem gold (26/09)",', 1),
    # relatório do preflight
    ('    L = ["# W-AD5 — preflight v5 sem gold (25/09)",', '    L = ["# Rodada VOCAB_LIMPO — preflight sem gold (26/09)",', 1),
    ('        L += ["", "## P2 por curso", "", "| curso | A | B ATUAL só ordem | B LLM só ordem | +LLM | +ATUAL |", "|---|---|---|---|---:|---:|"]\n'
     '        for s, e in R["P2"].items():\n'
     '            L.append(f"| {s} | {e[\'A_igual\']} | {e[\'VOCAB_ATUAL\'][\'B_diagnostico\'][\'somente_ordem_de_aliases\']} | "\n'
     '                     f"{e[\'VOCAB_LLM\'][\'B_diagnostico\'][\'somente_ordem_de_aliases\']} | {e[\'VOCAB_LLM\'][\'aliases_add\']} | {e[\'VOCAB_ATUAL\'][\'aliases_add\']} |")',
     '        L += ["", "## P2 por curso", "", "| curso | A | B LIMPO só ordem | +LIMPO | -LIMPO |", "|---|---|---|---:|---:|"]\n'
     '        for s, e in R["P2"].items():\n'
     '            L.append(f"| {s} | {e[\'A_igual\']} | {e[\'VOCAB_LIMPO\'][\'B_diagnostico\'][\'somente_ordem_de_aliases\']} | "\n'
     '                     f"{e[\'VOCAB_LIMPO\'][\'aliases_add\']} | {e[\'VOCAB_LIMPO\'][\'aliases_rem\']} |")', 1),
    ("f\"{r['CTRL_MAIOR']['verificacao']['aprovado']} |", "f\"{r['CTRL_MAIOR_LIMPO']['verificacao']['aprovado']} |", 1),
    ('        L += ["", "## P4", "", f"- CRU ({p[\'origem\']}):', '        L += ["", "## P4", "", f"- CRU_LIMPO ({p[\'origem\']}):', 1),
], "captura.py")
grava("captura.py", t, crlf)

# ------------------------------------------------------------------------------------------- avaliador.py (adaptador)
t, crlf = carrega("avaliador.py")
t = troca(t, [
    ('"""W-AD4 (25/09): avaliador SEPARADO da Fase 1 do regime VOCAB.',
     '"""Rodada VOCAB_LIMPO (26/09): adaptador do avaliador congelado da Fase 1 (../wad5_25-09/avaliador.py, aeac2996…) com SÓ\n'
     'os nomes dos braços trocados em `veredictos` e `avalia`. Métricas, régua, denominadores e contrato idênticos.\n\n'
     'Original: avaliador SEPARADO da Fase 1 do regime VOCAB.', 1),
], "avaliador.py")
t = literais(t, desde="def veredictos(")
t = troca(t, [('"C_meta_VOCAB_LLM"', '"C_meta_VOCAB_LIMPO"', 1)], "avaliador.py")
grava("avaliador.py", t, crlf)

# ------------------------------------------------------------------------------------------- testes herdados (só nomes)
ROTULOS_DE_LADO = ('g["escada"]["CRU"]', 's["CRU"]["final"]', '["gold_id"] == "r3"')   # rótulos internos da geração
for nome in ("test_wad4.py", "test_defeitos_v4.py", "test_ajustes_v5.py"):
    t, crlf = carrega(nome)
    if nome == "test_wad4.py":
        t = troca(t, [('    assert K.CAPTURA_LIBERADA == frozenset({"CRU", "VOCAB_ATUAL", "VOCAB_LLM", "CTRL_MAIOR", "CTRL_ALEAT_1",\n'
                       '                                            "CTRL_ALEAT_2", "CTRL_ALEAT_3"}) == frozenset(K.BRACOS)',
                       '    assert K.CAPTURA_LIBERADA == frozenset({"CRU_LIMPO", "VOCAB_LIMPO", "CTRL_MAIOR_LIMPO", "CTRL_ALEAT_LIMPO_1",\n'
                       '                                            "CTRL_ALEAT_LIMPO_2", "CTRL_ALEAT_LIMPO_3"}) == frozenset(K.BRACOS)', 1),
                      ("\"faltam ['CTRL_ALEAT_3']\"", "\"faltam ['CTRL_ALEAT_LIMPO_3']\"", 1),
                      # na Fase 1 o exemplo de braço fora da lista era "VOCAB_LIMPO", que agora é braço real da rodada
                      ('def test_captura_liberada_exatamente_os_sete_bracos_e_braco_fora_da_lista_rejeitado(',
                       'def test_captura_liberada_exatamente_os_seis_bracos_da_rodada_e_braco_fora_da_lista_rejeitado(', 1),
                      ('    cong["insumos_braco"]["VOCAB_LIMPO"] = "x"   # braço que o protocolo não prevê',
                       '    cong["insumos_braco"]["VOCAB_ATUAL"] = "x"   # braço que a rodada não prevê', 1),
                      ('        CP.roda_worker("VOCAB_LIMPO", "capturar", cong, K.Travas("teste"))',
                       '        CP.roda_worker("VOCAB_ATUAL", "capturar", cong, K.Travas("teste"))', 1)], nome)
    t = t.replace("capturar_CRU_", "capturar_CRU_LIMPO_")
    t = literais(t, exceto=ROTULOS_DE_LADO)
    grava(nome, t, crlf)
print("rodada adaptada: comum.py, captura.py, avaliador.py, test_wad4.py, test_defeitos_v4.py, test_ajustes_v5.py")
