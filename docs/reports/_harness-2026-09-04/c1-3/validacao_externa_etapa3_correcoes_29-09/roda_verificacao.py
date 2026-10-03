"""Verificação das correções pós-revisão da etapa 3, cada versão em processo próprio (sem reuso de módulos importados).

1. vermelho: testes finais contra o código v3/v1 (cópia temporária espelhada em c1-3/_replay_vermelho_tmp, removida);
2. verde: os mesmos testes (e os herdados) contra v4/v2;
3. regressão: suítes originais da etapa 3 e da etapa 2, sem alteração;
4. os 5 casos anteriores contra v2, v3 e v4 (subprocesso por versão);
5. grava logs/ e reprodutores_pos_correcao_etapa3.json (não sobrescreve resultados anteriores).
Sem rede: fixtures sintéticas, cliente e urlopen falsos. Uso: python roda_verificacao.py
"""
import argparse
import hashlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
C13 = AQUI.parent
E2, E3 = C13 / "validacao_externa_etapa2_29-09", C13 / "validacao_externa_etapa3_29-09"
LOGS = AQUI / "logs"
AREAS = [("correcoes/pacote_cego", "gera_pacote_cego.py", "test_pacote_cego_v4.py"),
         ("correcoes/aquisicao", "adquire.py", "test_adquire_v4.py"),
         ("exposicao", "verifica_exposicao.py", "test_verifica_exposicao_v2.py"),
         ("conferencia", "confere_fontes.py", "test_confere_fontes.py")]
VERSOES = {"v2": (E2 / "correcoes/pacote_cego/gera_pacote_cego.py", E2 / "aquisicao/adquire.py"),
           "v3": (E3 / "correcoes/pacote_cego/gera_pacote_cego.py", E3 / "correcoes/aquisicao/adquire.py"),
           "v4": (AQUI / "correcoes/pacote_cego/gera_pacote_cego.py", AQUI / "correcoes/aquisicao/adquire.py")}
# nomes canônicos AQ (Gate 1) e correspondência com os IDs anteriores (JSON do revisor; tabela do parecer)
AQ = {"partial_write": ("AQ01", "AQ-01"), "interrupt_after_write": ("AQ02", "AQ-02"), "metadata_outside_budget": ("AQ03", "AQ-05"),
      "rejected_transfer_budget": ("AQ04", "AQ-05"), "path_traversal": ("AQ05", "AQ-06"),
      "inventory_write_interruption": ("AQ06", "AQ-03"), "baixar_interrupt_after_write": ("AQ07", "AQ-02"),
      "truncated_http_body_regression": ("AQ08", "AQ-04"), "probe_respects_remaining_budget": ("novo", "AQ-05")}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def pytest(cwd, alvo, junit, log):
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", alvo, "-q", "-p", "no:cacheprovider", "-rA", f"--junitxml={junit}"],
                       cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    linhas = [ln for ln in r.stdout.splitlines() if ln.startswith(("PASSED", "FAILED", "ERROR")) or " passed" in ln or " failed" in ln]
    Path(log).write_text("\n".join(ln[:220] for ln in linhas) + "\n", encoding="utf-8", newline="\n")
    return linhas[-1] if linhas else r.stdout[-300:]


def junit(p):
    """{nome do teste (com parâmetro): 'passou'|'falhou'}."""
    out = {}
    for tc in ET.parse(p).getroot().iter("testcase"):
        falhou = tc.find("failure") is not None or tc.find("error") is not None
        out[tc.get("name")] = "falhou" if falhou else "passou"
    return out


def vermelho_e_verde():
    tmp = C13 / "_replay_vermelho_tmp"
    if tmp.exists():
        sys.exit(f"{tmp} já existe: não sobrescrevo")
    resumo = {}
    try:
        for area, codigo, _ in AREAS:
            d = tmp / area
            d.mkdir(parents=True)
            shutil.copy2(E3 / area / codigo, d / codigo)
            for t in (AQUI / area).glob("test_*.py"):
                shutil.copy2(t, d / t.name)
        for area, codigo, teste in AREAS:
            nome = Path(area).name
            resumo[nome] = {"codigo_antigo_sha256": sha(E3 / area / codigo), "codigo_novo_sha256": sha(AQUI / area / codigo),
                            "vermelho": pytest(tmp, f"{area}/{teste}", LOGS / f"junit_vermelho_{nome}.xml", LOGS / f"vermelho_final_{nome}.txt")}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    for area, _, teste in AREAS:
        nome = Path(area).name
        resumo[nome]["verde_novos"] = pytest(AQUI / area, teste, LOGS / f"junit_verde_{nome}.xml", LOGS / f"verde_novos_{nome}.txt")
        resumo[nome]["verde_pasta_inteira"] = pytest(AQUI / area, ".", LOGS / f"junit_verde_pasta_{nome}.xml", LOGS / f"verde_pasta_{nome}.txt")
    return resumo


def regressao():
    alvos = {"etapa3_pacote_cego_v3": (E3, "correcoes/pacote_cego"), "etapa3_aquisicao_v3": (E3, "correcoes/aquisicao"),
             "etapa3_exposicao_v1": (E3, "exposicao"), "etapa2_correcoes": (E2, "correcoes")}
    return {k: pytest(cwd, alvo, LOGS / f"junit_regressao_{k}.xml", LOGS / f"regressao_{k}.txt") for k, (cwd, alvo) in alvos.items()}


def contraexemplos():
    casos = []
    for area, _, _ in AREAS:
        nome = Path(area).name
        antes, depois = junit(LOGS / f"junit_vermelho_{nome}.xml"), junit(LOGS / f"junit_verde_{nome}.xml")
        for teste in sorted(depois):
            base = teste.removeprefix("test_").split("[")[0]
            ids = AQ.get(base)
            casos.append({"area": nome, "teste": teste, "v3_ou_v1": antes.get(teste, "ausente"), "v4_ou_v2": depois[teste],
                          **({"canonico": base, "id_json_revisor": ids[0], "id_parecer": ids[1]} if ids else {})})
    return casos


# ------------------------------------------------------------------ os 5 casos anteriores, uma versão por processo
def pdf_valido(texto):
    stream = b"BT /F1 12 Tf 72 700 Td (%s) Tj ET" % texto.encode("latin-1")
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
            b"<< /Length %d >>\nstream\n%s\nendstream" % (len(stream), stream), b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    out, offs = bytearray(b"%PDF-1.7\n"), []
    for i, corpo in enumerate(objs, 1):
        offs.append(len(out))
        out += b"%d 0 obj\n" % i + corpo + b"\nendobj\n"
    x = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1) + b"".join(b"%010d 00000 n \n" % o for o in offs)
    return bytes(out + b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, x))


PLANO = ("# Plano de Ensino\n\n## Nº DA UNIDADE: 01\nCONTEÚDO: Fundamentos de sistemas embarcados\n"
         "1.1. Conceitos básicos de sistemas embarcados\n1.2. Ferramentas de desenvolvimento cruzado\n\n"
         "## Nº DA UNIDADE: 02\nCONTEÚDO: Acionadores de dispositivos\n2.1. Interface entre núcleo e dispositivo\n"
         "2.2. Módulos carregáveis do núcleo\n\n## BIBLIOGRAFIA\n")   # o mesmo plano sintético dos testes


def escreve(p, b):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b if isinstance(b, bytes) else b.encode("utf-8"))


def fonte_pastas(tmp, plano=PLANO):
    raiz = tmp / "Moodle/curso"
    escreve(raiz / "Unidade 1/aula1.pdf", pdf_valido("aula 1"))
    escreve(tmp / "plano/plano.pdf", pdf_valido("plano"))
    escreve(tmp / "plano/plano.md", plano)
    return {"sigla": "SIN", "nome": "Sintético", "moodle_dir": str(raiz), "plano_arquivo": str(tmp / "plano/plano.pdf"),
            "plano_texto": str(tmp / "plano/plano.md")}


class Resposta:
    def __init__(self, dados):
        self.dados, self.headers = dados, {"content-type": "application/octet-stream"}

    def read(self, n=-1):
        return self.dados if n is None or n < 0 else self.dados[:n]

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class Cliente:
    def __init__(self, contents):
        self.contents = contents

    def get_course_contents(self, cid):
        return self.contents[cid]

    def _download_url(self, url):
        return url


def carrega(nome, caminho):
    spec = importlib.util.spec_from_file_location(nome, caminho)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def tenta(f, tmp):
    try:
        return f()
    except BaseException as exc:   # noqa: BLE001
        return {"excecao": type(exc).__name__, "mensagem": str(exc).replace(str(tmp).replace("\\", "\\\\"), "<tmp>").replace(str(tmp), "<tmp>")[:200]}


def baixa(A, versao, contents, raiz, orc_limites, urls):
    A.urllib.request.urlopen = lambda url, timeout=None: Resposta(urls[url])
    A.ORC = {**orc_limites, "cursos_baixados_max": 10}
    cli = Cliente({"curso": contents})
    if versao == "v2":
        orc = {"bytes": 0}
        return A.baixa_curso(cli, "curso", raiz, orc), orc
    orc, arquivos = ({"bytes": 0} if versao == "v3" else {"transferidos": 0, "aceitos": 0}), []
    A.baixa_curso(cli, "curso", raiz, orc, arquivos)
    return arquivos, orc


def casos_anteriores(versao):
    G, A = (carrega(f"pacote_{versao}", VERSOES[versao][0]), carrega(f"adquire_{versao}", VERSOES[versao][1]))
    out = {"versao": versao, "gerador_sha256": sha(VERSOES[versao][0]), "adquire_sha256": sha(VERSOES[versao][1])}

    def plano_com_predicao(tmp):
        fonte = fonte_pastas(tmp, PLANO + "\ncomputed_unit_slug: unidade-01\n")
        G.monta(fonte, tmp / "pacote")
        copiado = b"computed_unit_slug" in b"".join(q.read_bytes() for q in (tmp / "pacote/plano").iterdir())
        return {"auditoria": G.audita(fonte, tmp / "pacote"), "conteudo_copiado": copiado}

    def zip_com_conteudo_proibido(tmp):
        fonte = fonte_pastas(tmp)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("aula.txt", "Conteúdo")
            z.writestr("anotacoes.txt", json.dumps({"computed_subunit_slug": "t1"}))
        escreve(Path(fonte["moodle_dir"]) / "Unidade 1/material.zip", buf.getvalue())
        G.monta(fonte, tmp / "pacote")
        m = next(x for x in json.loads((tmp / "pacote/materiais.json").read_text(encoding="utf-8"))["materiais"]
                 if x["nome_original"] == "material.zip")
        copiado = buf.getvalue() in b"".join(q.read_bytes() for q in (tmp / "pacote").rglob("*") if q.is_file())
        return {"auditoria": G.audita(fonte, tmp / "pacote"), "tipo": m["tipo"], "adjudicavel": m["adjudicavel"], "bytes_copiados": copiado}

    def origem_unico_candidato_outra_secao(tmp):
        a = {"rel": "stash/Secao A/slides.pdf", "sha": "x" * 64, "nome": "slides.pdf", "tamanho": 15}
        return {"pasta_pedida": "Secao B", "retornado": G.resolve_origem({"filename": "slides.pdf", "filesize": 15}, "Secao B",
                                                                          {("slides.pdf", 15): [a]})}

    def anexo_page_fora_da_raiz(tmp):
        contents = [{"name": "Geral", "modules": [
            {"id": 1, "modname": "resource", "contents": [{"type": "file", "filename": "a.txt", "filepath": "/", "filesize": 1, "fileurl": "u/a"}]},
            {"id": 2, "modname": "page", "contents": [{"type": "file", "filename": "imagem.png", "filepath": "/", "filesize": 1, "fileurl": "u/i"}]}]}]
        arquivos, _ = baixa(A, versao, contents, tmp / "downloads/curso", {"bytes_por_arquivo_max": 100, "bytes_totais_max": 1000},
                            {"u/a": b"texto a", "u/i": b"\x89PNG\r\n\x1a\nimg"})
        return {"retornou_inventario": True, "registros": [{k: a.get(k) for k in ("arquivo", "status", "base", "caminho")} for a in arquivos]}

    def limite_confiado_ao_filesize(tmp):
        contents = [{"name": "S", "modules": [{"id": 1, "modname": "resource", "contents": [
            {"type": "file", "filename": "x.txt", "filepath": "/", "filesize": 1, "fileurl": "u/x"}]}]}]
        arquivos, orc = baixa(A, versao, contents, tmp / "c", {"bytes_por_arquivo_max": 5, "bytes_totais_max": 5}, {"u/x": b"1234567"})
        return {"limite_arquivo": 5, "limite_total": 5, "bytes_enviados": 7, "status": arquivos[0]["status"], "orcamento": orc}

    for nome, f in (("plano_com_predicao", plano_com_predicao), ("zip_real_conteudo_nao_examinado", zip_com_conteudo_proibido),
                    ("origem_unico_candidato_outra_secao", origem_unico_candidato_outra_secao),
                    ("anexo_page_fora_da_raiz", anexo_page_fora_da_raiz), ("limite_confiado_ao_filesize", limite_confiado_ao_filesize)):
        with tempfile.TemporaryDirectory() as t:
            out[nome] = tenta(lambda: f(Path(t)), t)
    return out


def dependencias():
    mods = {}
    for m in ("fitz", "pypdf", "docx", "openpyxl", "pptx", "pytest"):
        try:
            mod = importlib.import_module(m)
            mods[m] = getattr(mod, "__version__", None) or getattr(mod, "VersionBind", None) or "instalado"
        except ImportError:
            mods[m] = None
    return {"python": sys.version.split()[0], "versoes": mods,
            "reais_no_codigo": ["src.builder.extraction (rótulos do plano)", "src.builder.sources.moodle (MoodleClient, "
                                "sanitize_folder_name, looks_like_expected)", "fitz/PyMuPDF (declarado no pyproject)"],
            "so_nos_testes": ["pypdf, python-docx, openpyxl, python-pptx (instalados, não declarados no pyproject)"],
            "stubs": "nenhum stub de src/ nesta execução local; rede substituída por cliente/urlopen falsos e http.client sobre BytesIO"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--versao")
    a = ap.parse_args()
    if a.versao:   # processo filho: uma versão só
        print(json.dumps(casos_anteriores(a.versao), ensure_ascii=False, default=str))
        return
    destino = AQUI / "reprodutores_pos_correcao_etapa3.json"
    if destino.exists():
        sys.exit(f"{destino.name} já existe: não sobrescrevo")
    LOGS.mkdir(exist_ok=True)
    execucao = vermelho_e_verde()
    reg = regressao()
    anteriores = {}
    for v in VERSOES:
        r = subprocess.run([sys.executable, "-B", str(Path(__file__)), "--versao", v], capture_output=True, text=True, encoding="utf-8")
        anteriores[v] = json.loads(r.stdout) if r.returncode == 0 else {"erro": r.stderr[-400:]}
    out = {"esquema": "reprodutores-pos-correcao-etapa3-1", "metodo": __doc__.strip().splitlines()[0],
           "restricoes": {"rede": False, "gold": False, "adjudicacao": False, "motor": False, "build_replay": False,
                          "recompilacao_vocabulario": False, "P3_aplicada": False, "elegibilidade_P3_calculada": False},
           "dependencias": dependencias(), "execucao": execucao, "regressao": reg, "casos_anteriores": anteriores,
           "contraexemplos": contraexemplos(),
           "correspondencia_AQ": {k: {"id_json_revisor": v[0], "id_parecer": v[1]} for k, v in AQ.items()}}
    destino.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"execucao": execucao, "regressao": reg}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
