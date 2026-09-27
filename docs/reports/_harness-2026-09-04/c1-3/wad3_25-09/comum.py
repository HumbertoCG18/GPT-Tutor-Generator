"""W-AD3 (25/09): peças comuns da captura e do avaliador. Só stdlib; não importa src/ nem módulos de avaliação.

Protocolo: docs/reports/2026-09-25-regime-vocab-adendo-fase1-v2.md. Tudo aqui é testado com dados sintéticos
(test_wad3.py); nada lê gold.
"""
import builtins
import hashlib
import io
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ESQUEMA_CAPTURA = "wad3-captura-1"
ESQUEMA_CONGELAMENTO = "wad3-congelamento-1"
NOMES = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor",
         "FR": "Fundamentos-de-Redes-Tutor"}
BRACOS = ("CRU", "VOCAB_ATUAL", "VOCAB_LLM", "CTRL_MAIOR", "CTRL_ALEAT_1", "CTRL_ALEAT_2", "CTRL_ALEAT_3")
SEMENTES = {"CTRL_ALEAT_1": 1, "CTRL_ALEAT_2": 2, "CTRL_ALEAT_3": 3}
# Referência declarada pelo usuário (25/09): manual carregado só no VOCAB_ATUAL, e só nestes cursos.
MANUAL_ESPERADO = {b: {s: (b == "VOCAB_ATUAL" and s in {"CG", "ES2", "IA", "SO", "TCC"}) for s in NOMES} for b in BRACOS}
# Captura completa liberada nesta etapa: só o CRU (dentro do preflight). Mudar isto é mudança de código e de congelamento.
CAPTURA_LIBERADA = frozenset({"CRU"})
DENOMINADORES = {"bloco": 237, "unidade": 284, "sub_primaria": 251}
INVENTARIO_ESPERADO = 350
GOLD_PADROES = ("wx_gold_v2_final", "gold_units_", "material_gt_", "subunit_gt_", "coverage_gt_", "herancas_",
                "ground_truth", "regua_historica", "_gt_")
CAMPOS_REGISTRO = ("curso", "id", "chamado", "final")


class ErroIntegridade(RuntimeError):
    """Falha de integridade/protocolo: nunca capturada para seguir adiante."""


class Violacao(RuntimeError):
    """Acesso proibido detectado por uma trava."""


# ------------------------------------------------------------------------------------------- hashes e JSON
def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_arq(p, _abrir=None):
    h = hashlib.sha256()
    with (_abrir or io.open)(p, "rb") as fh:
        for bloco in iter(lambda: fh.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def canon(obj):
    """Canonização declarada: conjuntos viram listas ordenadas (estruturas sem ordem); listas mantêm a ordem."""
    if isinstance(obj, dict):
        return {str(k): canon(v) for k, v in obj.items()}
    if isinstance(obj, (set, frozenset)):
        return sorted((canon(x) for x in obj), key=lambda x: json.dumps(x, sort_keys=True, ensure_ascii=False))
    if isinstance(obj, (list, tuple)):
        return [canon(x) for x in obj]
    return obj


def sha_json(obj):
    txt = json.dumps(canon(obj), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return sha_bytes(txt.encode("utf-8"))


def _sem_duplicata(pares):
    vistos = {}
    for k, v in pares:
        if k in vistos:
            raise ErroIntegridade(f"chave JSON duplicada: {k!r}")
        vistos[k] = v
    return vistos


def carrega_json_estrito(p, _abrir=None):
    try:
        with (_abrir or io.open)(p, encoding="utf-8") as fh:
            return json.load(fh, object_pairs_hook=_sem_duplicata)
    except (ValueError, OSError) as exc:
        raise ErroIntegridade(f"JSON inválido ou ilegível em {p}: {type(exc).__name__}: {exc}") from None


def grava_atomico(p, obj, _abrir=None):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), prefix=".tmp-", suffix=".json")
    os.close(fd)
    try:
        with (_abrir or io.open)(tmp, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, ensure_ascii=False, sort_keys=True, allow_nan=False)
        os.replace(tmp, p)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def arvore(raiz, _abrir=None):
    """{caminho relativo posix: sha256} de todos os arquivos (sem __pycache__)."""
    raiz = Path(raiz)
    out = {}
    for p in sorted(raiz.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts:
            out[p.relative_to(raiz).as_posix()] = sha_arq(p, _abrir)
    return out


# ------------------------------------------------------------------------------------------- git (P0)
def git(*args, cwd):
    """(stdout, erro): erro não vazio quando o comando falha — stdout vazio de comando falho NÃO é árvore limpa."""
    try:
        r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    except OSError as exc:
        return "", f"git indisponível: {exc}"
    if r.returncode != 0:
        return r.stdout, f"git {' '.join(args)} saiu {r.returncode}: {r.stderr.strip()[:300]}"
    return r.stdout, ""


# ------------------------------------------------------------------------------------------- travas
class Travas:
    """Registro de acessos e violações do processo. Cobertura REAL (documentada, não é sandbox):
    builtins.open/io.open (inclui Path.open/read_text/read_bytes e json via open), socket.connect/connect_ex/
    create_connection/getaddrinfo, subprocess.Popen e o compilador de vocabulário (quando o módulo é carregado).
    NÃO cobre os.open, mmap, extensões C, processos já existentes nem rede fora da API Python de socket."""

    def __init__(self, papel):
        self.papel = papel
        self.permitidos = {}        # categoria -> [raiz resolvida]
        self.leitura_so = set()     # categorias somente leitura
        self.proibidos = []         # (raiz, motivo)
        self.negados_decl = []      # (caminho, motivo): acesso impedido por declaração do protocolo; não é violação
        self.negados = []           # registro dos acessos impedidos por declaração
        self.congelados = {}        # caminho resolvido -> sha esperado
        self.acessos = {}           # caminho resolvido -> {"categoria", "modo", "sha", "n"}
        self.violacoes = []
        self.permite_subprocesso = False
        self._instalado = False

    # configuração
    def permite(self, categoria, *raizes, somente_leitura=False):
        self.permitidos.setdefault(categoria, []).extend(str(Path(r).resolve()) for r in raizes)
        if somente_leitura:
            self.leitura_so.add(categoria)

    def proibe(self, raiz, motivo):
        self.proibidos.append((str(Path(raiz).resolve()), motivo))

    def nega(self, caminho, motivo):
        """Arquivo que o produto tenta ler e o protocolo nega (ex.: .env com segredos): impede a leitura sem ler o conteúdo,
        registra em `negados` e não conta como violação."""
        self.negados_decl.append((str(Path(caminho).resolve()), motivo))

    def congela(self, raiz, arvore_sha):
        base = Path(raiz).resolve()
        for rel, h in arvore_sha.items():
            self.congelados[str(base / rel)] = h

    def congela_arquivos(self, mapa):
        """{caminho absoluto: sha} de entradas externas; permitidas só pelo caminho exato, somente leitura."""
        for p, h in mapa.items():
            self.congelados[str(Path(p).resolve())] = h
        self.permite("externo", *mapa.keys(), somente_leitura=True)

    def registra(self, tipo, detalhe):
        self.violacoes.append({"tipo": tipo, "detalhe": str(detalhe)[:400], "papel": self.papel,
                               "quando": round(time.time(), 3)})

    # classificação
    @staticmethod
    def _dentro(p, raiz):
        return p == raiz or p.startswith(raiz.rstrip("\\/") + os.sep)

    def classifica(self, caminho):
        p = str(Path(caminho).resolve())
        baixo = p.replace("\\", "/").lower()
        if any(g in baixo for g in GOLD_PADROES):
            return p, "proibido", "gold"
        for raiz, motivo in self.proibidos:
            if self._dentro(p, raiz):
                return p, "proibido", motivo
        melhor = None
        for cat, raizes in self.permitidos.items():
            for raiz in raizes:
                if self._dentro(p, raiz) and (melhor is None or len(raiz) > len(melhor[1])):
                    melhor = (cat, raiz)
        return (p, melhor[0], "") if melhor else (p, "fora_da_lista", "")

    def verifica_acesso(self, caminho, modo, _abrir):
        if isinstance(caminho, int):
            return
        p, cat, motivo = self.classifica(caminho)
        escrita = any(c in modo for c in "wax+")
        for alvo, por_que in self.negados_decl:
            if p == alvo:
                self.negados.append({"caminho": p, "motivo": por_que, "escrita": escrita})
                raise PermissionError(f"acesso negado por declaração do protocolo ({por_que})")
        if cat == "proibido":
            self.registra("acesso_proibido", f"{motivo}: {p}")
            raise Violacao(f"acesso proibido ({motivo})")
        if cat == "fora_da_lista":
            self.registra("fora_da_lista", f"{'escrita' if escrita else 'leitura'}: {p}")
            raise Violacao("acesso fora da lista permitida")
        if escrita and cat in self.leitura_so:
            self.registra("escrita_em_entrada", p)
            raise Violacao("escrita em entrada somente leitura")
        reg = self.acessos.setdefault(p, {"categoria": cat, "modo": set(), "sha": None, "n": 0})
        reg["modo"].add("w" if escrita else "r")
        reg["n"] += 1
        if not escrita and reg["sha"] is None and cat != "codigo" and os.path.isfile(p):
            reg["sha"] = sha_arq(p, _abrir)
            if p in self.congelados and self.congelados[p] != reg["sha"]:
                self.registra("insumo_divergente", p)
                raise Violacao("insumo congelado com hash divergente")
            if cat in ("comum", "externo") and p not in self.congelados:
                self.registra("insumo_nao_congelado", p)
                raise Violacao("insumo comum fora do congelamento")

    # instalação
    def instala(self):
        if self._instalado:
            return self
        abrir = io.open
        travas = self

        def aberto(file, mode="r", *a, **k):
            travas.verifica_acesso(file, mode, abrir)
            return abrir(file, mode, *a, **k)

        builtins.open = io.open = aberto
        self._abrir_original = abrir

        def sem_rede(*a, **k):
            travas.registra("rede", repr(a)[:120])
            raise Violacao("rede bloqueada")

        for nome in ("connect", "connect_ex"):
            setattr(socket.socket, nome, sem_rede)
        socket.create_connection = sem_rede
        socket.getaddrinfo = sem_rede
        popen = subprocess.Popen

        class _Popen(popen):
            def __init__(self_, *a, **k):
                if not travas.permite_subprocesso:
                    travas.registra("subprocesso", repr(a)[:160])
                    raise Violacao("subprocesso bloqueado")
                super().__init__(*a, **k)

        subprocess.Popen = _Popen
        self._instalado = True
        return self

    def bloqueia_compilador(self, modulo_vocab):
        travas = self

        def sem_compilar(*a, **k):
            travas.registra("compilador", "compile_course_vocabulary")
            raise Violacao("compilador de vocabulário bloqueado")

        modulo_vocab.compile_course_vocabulary = sem_compilar

    def rehash_leituras(self):
        """Confere, ao final, que tudo o que foi lido continua igual em disco."""
        for p, reg in self.acessos.items():
            if reg["sha"] and "r" in reg["modo"] and os.path.isfile(p):
                if sha_arq(p, self._abrir_original) != reg["sha"]:
                    self.registra("insumo_alterado_durante_execucao", p)

    def resumo(self):
        return {"violacoes": list(self.violacoes), "negados": list(self.negados),
                "acessos": {p: {"categoria": r["categoria"], "modo": sorted(r["modo"]), "sha": r["sha"], "n": r["n"]}
                            for p, r in sorted(self.acessos.items())}}


def encerra(travas, *, ok, codigo_falha=2):
    """Qualquer violação registrada (mesmo capturada por camada intermediária) impede o sucesso."""
    if travas.violacoes or not ok:
        sys.stdout.flush()
        sys.exit(codigo_falha)


# ------------------------------------------------------------------------------------------- congelamento e captura
def id_congelamento(normativo):
    return sha_json({"esquema": ESQUEMA_CONGELAMENTO, **normativo})


def conteudo_sha(captura):
    return sha_json({k: v for k, v in captura.items() if k != "conteudo_sha"})


def valida_registro(r):
    """Estrutura mínima de um registro de material; devolve lista de problemas."""
    prob = []
    for c in CAMPOS_REGISTRO:
        if c not in r:
            prob.append(f"campo ausente: {c}")
    fin = r.get("final")
    if isinstance(fin, dict):
        for c in ("bloco", "unidade", "sub"):
            if c not in fin or not isinstance(fin[c], str):
                prob.append(f"final.{c} ausente ou não-string")
    elif "final" in r:
        prob.append("final não é objeto")
    if r.get("chamado"):
        p1 = r.get("p1")
        if not isinstance(p1, dict):
            prob.append("chamado sem p1")
        else:
            for c in ("unidade_fornecida", "pontuacoes", "vencedor", "conf", "ambigua", "motivos"):
                if c not in p1:
                    prob.append(f"p1.{c} ausente")
            v = p1.get("vencedor")
            if not (isinstance(v, dict) and "unidade" in v and "topico" in v):
                prob.append("p1.vencedor sem identidade (unidade, tópico)")
    return prob


def valida_captura(cap, *, congelamento, braco, modo, inventario):
    """Problemas que impedem usar/reutilizar a captura. Lista vazia = válida."""
    prob = []
    if not isinstance(cap, dict):
        return ["captura não é objeto"]
    if cap.get("esquema") != ESQUEMA_CAPTURA:
        prob.append(f"esquema incompatível: {cap.get('esquema')!r}")
    if cap.get("braco") != braco:
        prob.append(f"braço errado: {cap.get('braco')!r} != {braco!r}")
    if cap.get("modo") != modo:
        prob.append(f"modo errado: {cap.get('modo')!r} != {modo!r}")
    if cap.get("status") != "concluida":
        prob.append(f"status não concluído: {cap.get('status')!r}")
    if cap.get("congelamento_comum") != congelamento.get("id_comum"):
        prob.append("congelamento comum divergente")
    if cap.get("insumos_braco") != (congelamento.get("insumos_braco") or {}).get(braco):
        prob.append("insumos do braço divergentes")
    if cap.get("violacoes"):
        prob.append(f"violações registradas: {len(cap['violacoes'])}")
    if cap.get("conteudo_sha") != conteudo_sha(cap):
        prob.append("conteúdo alterado (hash não confere)")
    inv = cap.get("inventario")
    if inv != inventario:
        faltam = sorted(set(inventario) - set(inv or {}))
        sobram = sorted(set(inv or {}) - set(inventario))
        prob.append(f"inventário divergente (cursos ausentes {faltam}, extras {sobram})")
    if modo == "capturar":
        dec = cap.get("decisoes")
        if not isinstance(dec, dict) or set(dec) != set(inventario):
            prob.append("decisões sem os cursos do inventário")
        else:
            for sig, ids in inventario.items():
                if sorted(dec[sig]) != sorted(ids):
                    prob.append(f"{sig}: IDs das decisões != inventário")
                for eid in ids:
                    r = dec[sig].get(eid)
                    if not isinstance(r, dict):
                        prob.append(f"{sig}/{eid}: registro ausente")
                        continue
                    for x in valida_registro(r):
                        prob.append(f"{sig}/{eid}: {x}")
                    if r.get("chamado") and isinstance(r.get("p1"), dict) and isinstance(r.get("final"), dict):
                        if r["p1"].get("unidade_fornecida") != r["final"].get("unidade"):
                            prob.append(f"{sig}/{eid}: unidade da 1ª passada != final")
    return prob
