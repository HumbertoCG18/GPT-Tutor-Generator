"""Verificação local e limitada de exposição, v2 (correções pós-revisão da etapa 3, 29/09). Read-only: git grep/log no
commit base + nomes de pastas.

v2: fonte requisitada ausente ou saída do git não interpretada = INDETERMINADO; git sem cor e sem aspas em caminho
(`-c color.*=never -c core.quotePath=false`, `grep -z --no-color`); TODOS os matches de cada linha, com intervalo e
motivo específico de omissão; linha achada pelo git sem match no regex Python = INDETERMINADO; categoria: `tests/`
antes de código e "resultado do motor" só para artefato de dados/log. Categoria é do arquivo, não prova uso.

Para cada candidato: fontes pesquisadas, padrão, termo exato que casou, arquivo/linha, categoria do arquivo e um trecho
curto, para distinguir menção incidental de uso em desenvolvimento. NÃO atribui nível (N0/N1/...) nem lê níveis:
a lista de candidatos sai só da identidade (catálogo + candidatos de 29/09, menos os ids/siglas fora da população
principal, declarados na entrada). Trecho de arquivo de resultado do motor, ou com assinatura de saída do motor ou de
segredo, é omitido. Falha de qualquer busca = INDETERMINADO (nunca "sem evidência").

Uso: python verifica_exposicao.py [entrada.json] [saida.json]
"""
import collections
import importlib.util
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
AQUI = Path(__file__).resolve().parent
REPO = next(p for p in AQUI.parents if (p / ".git").exists())
_spec = importlib.util.spec_from_file_location("pacote_v4", AQUI.parent / "correcoes/pacote_cego/gera_pacote_cego.py")
PC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(PC)   # só PADRAO_PREDICAO e PADRAO_SEGREDO

CATEGORIAS = [   # primeira que casa com o caminho; a ordem importa
    ("teste_ou_fixture", re.compile(r"^tests/")),
    ("codigo", re.compile(r"^(src|scripts)/|\.(py|js|ts)$")),
    ("resultado_do_motor", re.compile(r"(captur|placar|avaliac|gold|resumo|manifest|atribui|assignment|curation)[^/]*\.(json|jsonl|csv|log|txt)$", re.I)),
    ("dados_json_csv", re.compile(r"\.(json|jsonl|csv)$", re.I)),
    ("contexto_de_agente", re.compile(r"^\.(mex|workflow)/")),
    ("plano_ou_spec", re.compile(r"(^|/)(plans?|specs?)/|plano|spec", re.I)),
    ("relatorio_ou_handoff", re.compile(r"^docs/")),
]
NAO_DOCUMENTAL = {"codigo", "teste_ou_fixture", "resultado_do_motor", "dados_json_csv"}   # contagem, não veredito
TRECHO = 80


def git(repo, *args):
    try:
        r = subprocess.run(["git", "--no-pager", "-c", "color.ui=never", "-c", "color.grep=never", "-c",
                            "core.quotePath=false", *args], cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace")
    except OSError:
        return None, ""
    return r.returncode, r.stdout


def chave(nome):
    t = unicodedata.normalize("NFKD", str(nome or "")).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "", t.casefold())


def categoria(caminho):
    return next((nome for nome, rx in CATEGORIAS if rx.search(caminho)), "outro")


def candidatos(entrada):
    """Só identidade: disciplinas do catálogo (com semestre) e candidatos locais de 29/09, menos os fora da população."""
    cat = json.loads((REPO / entrada["catalogo"]).read_text(encoding="utf-8"))
    loc = json.loads((REPO / entrada["candidatos_locais"]).read_text(encoding="utf-8"))
    fora_ids, fora_siglas = set(entrada["fora_ids"]), set(entrada["fora_siglas"])
    out = []
    for c in sorted(cat["cursos"], key=lambda c: int(c["id"])):
        if not c["semestre"] or c["id"] in fora_ids:
            continue
        alternativas = [rf"(?<!\d){re.escape(c['id'])}(?!\d)", re.escape(c["nome"])] + \
            ([re.escape(c["codigo"])] if len(c["codigo"]) >= 4 else [])   # mesma regra da triagem de 29/09
        out.append({"id": "moodle:" + c["id"], "nome": c["nome"], "padrao": "|".join(alternativas), "origem": "catálogo 29/09"})
    for c in loc["candidatos"]:
        if c["sigla"] in fora_siglas or c.get("desenvolvimento") or c.get("tutor"):
            continue
        out.append({"id": "local:" + c["sigla"], "nome": c["nome"], "padrao": c["padrao"], "origem": c.get("origem", "")})
    return out


def trecho(linha, m):
    """(3 caracteres antes/depois, trecho curto) de um match. A vizinhança mostra "Software I" dentro de "Software II" ou
    um id dentro de um hash mesmo quando o trecho é omitido."""
    ini, fim = max(0, m.start() - TRECHO), min(len(linha), m.end() + TRECHO)
    viz = {"antes": linha[max(0, m.start() - 3):m.start()], "depois": linha[m.end():m.end() + 3]}
    return viz, ("…" if ini else "") + linha[ini:fim].strip() + ("…" if fim < len(linha) else "")


def motivo_omissao(categoria_arquivo, txt):
    if categoria_arquivo == "resultado_do_motor":
        return "arquivo de resultado do motor"
    if PC.PADRAO_PREDICAO.search(txt):
        return "assinatura de saída do motor no trecho"
    if PC.PADRAO_SEGREDO.search(txt):
        return "credencial ou segredo no trecho"
    return None


def verifica(c, repo, base, raizes, exclui, pastas_anteriores):
    falhas = []
    rc, topo = git(repo, "rev-parse", "--show-toplevel")
    if rc != 0 or Path(topo.strip()).resolve() != Path(repo).resolve():
        falhas.append(f"repositório não é a raiz do git (saiu {rc})")
    if git(repo, "cat-file", "-e", f"{base}^{{commit}}")[0] != 0:
        falhas.append("commit base indisponível")
    for r in raizes:
        if git(repo, "cat-file", "-e", f"{base}:{r}")[0] != 0:
            falhas.append(f"raiz ausente no commit base: {r}")
    try:
        rx = re.compile(c["padrao"], re.I)
    except re.error as exc:
        rx, _ = None, falhas.append(f"padrão inválido: {exc}")
    if pastas_anteriores is None:
        falhas.append("fonte de pastas anteriores ausente")
    rc_g, saida = git(repo, "grep", "-z", "-n", "-I", "-P", "-i", "--no-color", "-e", c["padrao"], base, "--", *raizes)
    if rc_g not in (0, 1):
        falhas.append(f"git grep falhou (saiu {rc_g})")
    rc_l, log = git(repo, "log", "--no-color", base, "--format=%h %s", "-i", "--perl-regexp", f"--grep={c['padrao']}")
    if rc_l != 0:
        falhas.append(f"git log falhou (saiu {rc_l})")
    ocorrencias, nao_interpretadas, sem_match = [], 0, 0
    for ln in saida.split("\n") if rc_g == 0 and rx else []:
        if not ln:
            continue
        m = re.fullmatch(rf"{re.escape(base)}:([^\0]+)\0(\d+)\0(.*)", ln, re.S)
        if not m:
            nao_interpretadas += 1
            continue
        cam, num, linha = m.group(1), int(m.group(2)), m.group(3)
        if exclui.search(cam):
            continue
        matches = list(rx.finditer(linha))
        sem_match += not matches
        cat = categoria(cam)
        for mt in matches:   # todos os matches da linha, não só o primeiro
            viz, txt = trecho(linha, mt)
            motivo = motivo_omissao(cat, txt)
            ocorrencias.append({"arquivo": cam, "linha": num, "categoria": cat, "termo": mt.group(0),
                                "intervalo": [mt.start(), mt.end()], "vizinhanca": viz,
                                "trecho": "[omitido]" if motivo else txt, "motivo_omissao": motivo})
    if nao_interpretadas:
        falhas.append(f"saída do git grep não interpretada ({nao_interpretadas} linhas)")
    if sem_match:
        falhas.append(f"linhas achadas pelo git sem match no regex Python ({sem_match}; PCRE x re)")
    por_arquivo = collections.defaultdict(list)
    for o in ocorrencias:
        por_arquivo[o["arquivo"]].append(o)
    cats = collections.Counter(categoria(a) for a in por_arquivo)
    anterior = sorted(p for p in pastas_anteriores or [] if chave(c["nome"]) and chave(p) == chave(c["nome"]))
    return {**c, "status_da_busca": "INDETERMINADO" if falhas else "ok", "falhas": falhas,
            "sinais": {"arquivos": len(por_arquivo), "ocorrencias": len(ocorrencias), "arquivos_por_categoria": dict(sorted(cats.items())),
                       "arquivos_codigo_teste_dados_ou_resultado": sum(n for k, n in cats.items() if k in NAO_DOCUMENTAL),
                       "commits": len(log.splitlines()) if rc_l == 0 else None, "download_anterior": anterior,
                       "termos": dict(collections.Counter(str(o["termo"]) for o in ocorrencias).most_common(8))},
            "commits": log.splitlines()[:10] if rc_l == 0 else [], "ocorrencias": ocorrencias}


def main():
    entrada_p = Path(sys.argv[1]) if len(sys.argv) > 1 else AQUI / "entrada_exposicao.json"
    saida_p = Path(sys.argv[2]) if len(sys.argv) > 2 else AQUI / "exposicao_local.json"
    e = json.loads(entrada_p.read_text(encoding="utf-8"))
    base_downloads = Path(e["pastas_anteriores"]).expanduser()
    pastas = [p.name for p in base_downloads.iterdir() if p.is_dir()] if base_downloads.is_dir() else None   # None = ausente
    exclui = re.compile(e["exclui_caminho"])
    res = [verifica(c, REPO, e["base"], e["raizes"], exclui, pastas) for c in candidatos(e)]
    out = {"esquema": "exposicao-local-2", "entrada": e, "fontes_pesquisadas": {
        "git": f"commit {e['base']} (git grep -z -n -I -P -i --no-color nas raízes; git log --grep; sem cor, quotePath=false)",
        "raizes": e["raizes"], "exclusoes_de_caminho": e["exclui_caminho"],
        "nomes_de_pasta": f"{e['pastas_anteriores']} ({'AUSENTE' if pastas is None else len(pastas)} pastas, só nomes)"},
        "nao_pesquisado": ["outras branches", "worktrees", "stashes", "memória de sessões", "conversas", "conteúdo das pastas locais"],
        "candidatos": res}
    saida_p.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    for r in res:
        s = r["sinais"]
        print(f"{r['id']:<16} {r['status_da_busca']:<13} arquivos={s['arquivos']:<3} nao_doc={s['arquivos_codigo_teste_dados_ou_resultado']:<3} "
              f"commits={s['commits']} pasta={bool(s['download_anterior'])} {s['arquivos_por_categoria']}")


if __name__ == "__main__":
    main()
