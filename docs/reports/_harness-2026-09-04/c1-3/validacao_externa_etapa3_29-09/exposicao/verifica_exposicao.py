"""Verificação local e limitada de exposição (etapa 3, 29/09). Read-only: git grep/log no commit base + nomes de pastas.

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
_spec = importlib.util.spec_from_file_location("pacote_v3", AQUI.parent / "correcoes/pacote_cego/gera_pacote_cego.py")
PC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(PC)   # só PADRAO_PREDICAO e PADRAO_SEGREDO

CATEGORIAS = [   # primeira que casa com o caminho; a ordem importa
    ("codigo", re.compile(r"^(src|scripts)/|\.(py|js|ts)$")),
    ("teste_ou_fixture", re.compile(r"^tests/")),
    ("resultado_do_motor", re.compile(r"captur|placar|avaliac|gold|resumo|manifest|atribui|assignment|curation", re.I)),
    ("dados_json_csv", re.compile(r"\.(json|jsonl|csv)$", re.I)),
    ("contexto_de_agente", re.compile(r"^\.(mex|workflow)/")),
    ("plano_ou_spec", re.compile(r"(^|/)(plans?|specs?)/|plano|spec", re.I)),
    ("relatorio_ou_handoff", re.compile(r"^docs/")),
]
NAO_DOCUMENTAL = {"codigo", "teste_ou_fixture", "resultado_do_motor", "dados_json_csv"}   # contagem, não veredito
TRECHO = 80


def git(repo, *args):
    try:
        r = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace")
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


def trecho(linha, rx):
    """(termo, 3 caracteres antes/depois, trecho curto). A vizinhança mostra "Software I" dentro de "Software II" ou um id
    dentro de um hash mesmo quando o trecho é omitido."""
    m = rx.search(linha)
    if not m:
        return None, None, None
    ini, fim = max(0, m.start() - TRECHO), min(len(linha), m.end() + TRECHO)
    viz = {"antes": linha[max(0, m.start() - 3):m.start()], "depois": linha[m.end():m.end() + 3]}
    return m.group(0), viz, ("…" if ini else "") + linha[ini:fim].strip() + ("…" if fim < len(linha) else "")


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
    rc_g, saida = git(repo, "grep", "-n", "-I", "-P", "-i", "-e", c["padrao"], base, "--", *raizes)
    if rc_g not in (0, 1):
        falhas.append(f"git grep falhou (saiu {rc_g})")
    rc_l, log = git(repo, "log", base, "--format=%h %s", "-i", "--perl-regexp", f"--grep={c['padrao']}")
    if rc_l != 0:
        falhas.append(f"git log falhou (saiu {rc_l})")
    ocorrencias = []
    for ln in saida.splitlines() if rc_g == 0 and rx else []:
        m = re.match(rf"^{re.escape(base)}:(.+?):(\d+):(.*)$", ln)
        if not m or exclui.search(m.group(1)):
            continue
        cam, num, linha = m.group(1), int(m.group(2)), m.group(3)
        termo, viz, txt = trecho(linha, rx)
        cat = categoria(cam)
        if cat == "resultado_do_motor" or (txt and (PC.PADRAO_PREDICAO.search(txt) or PC.PADRAO_SEGREDO.search(txt))):
            txt = "[trecho omitido: resultado do motor, saída de classificação ou segredo]"
        ocorrencias.append({"arquivo": cam, "linha": num, "categoria": cat, "termo": termo, "vizinhanca": viz, "trecho": txt})
    por_arquivo = collections.defaultdict(list)
    for o in ocorrencias:
        por_arquivo[o["arquivo"]].append(o)
    cats = collections.Counter(categoria(a) for a in por_arquivo)
    anterior = sorted(p for p in pastas_anteriores if chave(c["nome"]) and chave(p) == chave(c["nome"]))
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
    pastas = [p.name for p in base_downloads.iterdir() if p.is_dir()] if base_downloads.is_dir() else []
    exclui = re.compile(e["exclui_caminho"])
    res = [verifica(c, REPO, e["base"], e["raizes"], exclui, pastas) for c in candidatos(e)]
    out = {"esquema": "exposicao-local-1", "entrada": e, "fontes_pesquisadas": {
        "git": f"commit {e['base']} (git grep -n -I -P -i nas raízes; git log --grep)", "raizes": e["raizes"],
        "exclusoes_de_caminho": e["exclui_caminho"], "nomes_de_pasta": f"{e['pastas_anteriores']} ({len(pastas)} pastas, só nomes)"},
        "nao_pesquisado": ["outras branches", "worktrees", "stashes", "memória de sessões", "conversas", "conteúdo das pastas locais"],
        "candidatos": res}
    saida_p.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    for r in res:
        s = r["sinais"]
        print(f"{r['id']:<16} {r['status_da_busca']:<13} arquivos={s['arquivos']:<3} nao_doc={s['arquivos_codigo_teste_dados_ou_resultado']:<3} "
              f"commits={s['commits']} pasta={bool(s['download_anterior'])} {s['arquivos_por_categoria']}")


if __name__ == "__main__":
    main()
