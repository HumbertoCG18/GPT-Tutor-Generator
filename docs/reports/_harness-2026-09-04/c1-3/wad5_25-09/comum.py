"""W-AD5 (25/09): peças comuns da captura e do avaliador. Só stdlib; não importa src/ nem módulos de avaliação.

Protocolo: docs/reports/2026-09-25-regime-vocab-adendo-fase1-v4.md. Versões anteriores preservadas em ../wad4_25-09/ e
../wad3_25-09/.
Testado só com dados sintéticos (test_wad4.py, test_defeitos_v4.py); nada lê gold.

Hashes (procedimento declarado):
- hash de ARQUIVO = sha256 dos bytes em disco (`sha_arq`);
- hash de CONTEÚDO canônico = sha256 do JSON com chaves ordenadas, separadores fixos, sem NaN/infinito e com conjuntos
  convertidos em listas ordenadas (`sha_json`); listas mantêm a ordem, porque a ordem pode ser comportamento.
Nenhum campo de hash entra no próprio cálculo (`conteudo_sha` exclui a si mesmo; resultados não entram no normativo).
"""
import builtins
import contextlib
import hashlib
import io
import json
import math
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ESQUEMA_CAPTURA = "wad5-captura-1"
ESQUEMA_CONGELAMENTO = "wad5-congelamento-1"
NOMES = {"MF": "Metodos-Formais-Tutor", "SO": "Sistemas-Operacionais-Tutor", "IA": "Inteligencia-Artifical-Tutor",
         "ES2": "Engenharia-Software-2-Tutor", "TCC": "TCC-Tutor", "CG": "Computacao-Grafica-Tutor",
         "FR": "Fundamentos-de-Redes-Tutor"}
BRACOS = ("CRU", "VOCAB_ATUAL", "VOCAB_LLM", "CTRL_MAIOR", "CTRL_ALEAT_1", "CTRL_ALEAT_2", "CTRL_ALEAT_3")
SEMENTES = {"CTRL_ALEAT_1": 1, "CTRL_ALEAT_2": 2, "CTRL_ALEAT_3": 3}
MANUAL_ESPERADO = {b: {s: (b == "VOCAB_ATUAL" and s in {"CG", "ES2", "IA", "SO", "TCC"}) for s in NOMES} for b in BRACOS}
# Gate condicional de 25/09 (revisão independente do W-AD4): captura dos sete braços; NÃO libera gold nem avaliação.
# Mudar isto é mudança de código e de congelamento.
CAPTURA_LIBERADA = frozenset({"CRU", "VOCAB_ATUAL", "VOCAB_LLM", "CTRL_MAIOR", "CTRL_ALEAT_1", "CTRL_ALEAT_2", "CTRL_ALEAT_3"})
INVENTARIO_ESPERADO = 350
DENOMINADORES = {"bloco": 237, "unidade": 284, "sub_primaria": 251}
# Denominadores e referência do CRU por curso: tabela do relatório 2026-09-24-teto-regime-cru.md §1 (documentação já
# publicada; nenhum gold lido para obtê-los). FR sem bloco nem unidade avaliados.
DENOM_POR_CURSO = {
    "MF": {"bloco": 66, "unidade": 66, "sub_primaria": 58}, "SO": {"bloco": 39, "unidade": 37, "sub_primaria": 15},
    "IA": {"bloco": 42, "unidade": 42, "sub_primaria": 39}, "ES2": {"bloco": 28, "unidade": 28, "sub_primaria": 28},
    "TCC": {"bloco": 27, "unidade": 18, "sub_primaria": 11}, "CG": {"bloco": 35, "unidade": 93, "sub_primaria": 82},
    "FR": {"bloco": 0, "unidade": 0, "sub_primaria": 18}}
REFERENCIA_CRU = {
    "MF": {"bloco": 60, "unidade": 63, "sub_primaria": 25}, "SO": {"bloco": 36, "unidade": 30, "sub_primaria": 7},
    "IA": {"bloco": 41, "unidade": 39, "sub_primaria": 4}, "ES2": {"bloco": 27, "unidade": 26, "sub_primaria": 7},
    "TCC": {"bloco": 26, "unidade": 17, "sub_primaria": 7}, "CG": {"bloco": 33, "unidade": 74, "sub_primaria": 30},
    "FR": {"bloco": 0, "unidade": 0, "sub_primaria": 6}}
GOLD_PADROES = ("wx_gold_v2_final", "gold_units_", "material_gt_", "subunit_gt_", "coverage_gt_", "herancas_",
                "ground_truth", "regua_historica", "_gt_")
# Ambiente dos processos: montado do zero. Parâmetros declarados (não secretos) + variáveis de sistema do Windows
# necessárias ao intérprete (só os NOMES são registrados). Todo o resto do terminal é descartado, inclusive credenciais.
ENV_DECLARADO = {"PYTHONHASHSEED": "0", "TUTOR_NO_VOCAB_COMPILE": "1", "TUTOR_NO_CODE_SYNTH": "1",
                 "UNIT_GENERIC_MODE": "df", "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1",
                 "PYTHONNOUSERSITE": "1"}
ENV_SISTEMA_HERDAVEL = frozenset({"SYSTEMROOT", "WINDIR", "SYSTEMDRIVE", "TEMP", "TMP", "PATH", "PATHEXT", "COMSPEC",
                                  "USERPROFILE", "HOMEDRIVE", "HOMEPATH", "APPDATA", "LOCALAPPDATA", "PROGRAMDATA",
                                  "PROGRAMFILES", "PROGRAMFILES(X86)", "PROGRAMW6432", "COMMONPROGRAMFILES",
                                  "COMMONPROGRAMFILES(X86)", "PROCESSOR_ARCHITECTURE", "NUMBER_OF_PROCESSORS", "OS"})
CATEGORIAS_LEITURA = {"codigo", "comum", "externo", "braco", "referencia", "saida", "protocolo"}


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


def blob_git(b):
    """Identificador de blob do git para bytes (sha1 de 'blob <n>\\0' + conteúdo)."""
    return hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()


def canon(obj):
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


def arvore(raiz, _abrir=None, checa=None):
    """{caminho relativo posix: sha256} de todos os arquivos (sem __pycache__). `checa(p)` roda ANTES de ler cada um."""
    raiz = Path(raiz)
    out = {}
    for p in sorted(raiz.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts:
            if checa:
                checa(p)
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


# ------------------------------------------------------------------------------------------- ambiente e código
def ambiente_controlado(base):
    """Ambiente do processo filho: variáveis de sistema herdáveis + parâmetros declarados. Nada mais."""
    env = {k: v for k, v in base.items() if k.upper() in ENV_SISTEMA_HERDAVEL}
    env.update(ENV_DECLARADO)
    return env


def verifica_ambiente(env):
    prob = []
    for k, v in ENV_DECLARADO.items():
        if env.get(k) != v:
            prob.append(f"{k} divergente do declarado")
    for k in env:
        if k.upper() not in ENV_SISTEMA_HERDAVEL and k not in ENV_DECLARADO:
            prob.append(f"variável não declarada no ambiente: {k}")
    return prob


def descritor_ambiente(env):
    """Só parâmetros não secretos: valores declarados e NOMES das variáveis de sistema herdadas."""
    return {"declarado": dict(ENV_DECLARADO), "herdados_sistema": sorted(k.upper() for k in env if k.upper() in ENV_SISTEMA_HERDAVEL)}


def verifica_codigo(esperado, arquivos, _abrir=None):
    """Compara os arquivos de código em disco com os hashes congelados."""
    prob = []
    if set(esperado) != set(arquivos):
        prob.append(f"conjunto de arquivos de código diverge: {sorted(set(esperado) ^ set(arquivos))}")
    for nome, p in arquivos.items():
        if nome in esperado:
            if not Path(p).is_file():
                prob.append(f"código ausente: {nome}")
            elif sha_arq(p, _abrir) != esperado[nome]:
                prob.append(f"código divergente do congelado: {nome}")
    return prob


def verifica_modulos(modulos, *, raiz, arvore, prefixo="src", _abrir=None):
    """Origem dos módulos carregados: dentro da raiz esperada e com o mesmo hash do fonte congelado."""
    prob, raiz = [], Path(raiz).resolve()
    for nome, mod in sorted(modulos.items()):
        if not (nome == prefixo or nome.startswith(prefixo + ".")):
            continue
        arq = getattr(mod, "__file__", None)
        if not arq:
            continue
        p = Path(arq).resolve()
        if raiz != p and raiz not in p.parents:
            prob.append(f"{nome}: carregado fora da raiz esperada ({p})")
            continue
        rel = p.relative_to(raiz).as_posix()
        if rel not in arvore:
            prob.append(f"{nome}: arquivo não congelado ({rel})")
        elif sha_arq(p, _abrir) != arvore[rel]:
            prob.append(f"{nome}: fonte divergente do congelado ({rel})")
    return prob


# ------------------------------------------------------------------------------------------- travas
class Travas:
    """Registro de acessos e violações do processo. Cobertura REAL (documentada, não é sandbox):
    builtins.open/io.open (inclui Path.open/read_text/read_bytes e json via open), socket.connect/connect_ex/
    create_connection/getaddrinfo, subprocess.Popen e o compilador de vocabulário (quando o módulo é carregado).
    NÃO cobre os.open, mmap, importações (io.open_code) nem extensões C: o código importado é conferido à parte
    (verifica_modulos). Cada abertura de leitura de entrada é conferida contra o hash; arquivo congelado ausente é
    violação mesmo antes da 1ª leitura; ao final, releitura de tudo o que foi lido e do inventário congelado inteiro."""

    def __init__(self, papel):
        self.papel = papel
        self.permitidos = {}
        self.leitura_so = set()
        self.proibidos = []
        self.negados_decl = []
        self.negados = []
        self.congelados = {}
        self.primeiro = {}
        self.acessos = {}
        self.violacoes = []
        self.comandos_permitidos = frozenset()
        self._abrir_original = io.open
        self._instalado = False
        self._integridade = set()   # caminhos já registrados como desaparecidos/divergentes (sem duplicar)

    def permite(self, categoria, *raizes, somente_leitura=False):
        self.permitidos.setdefault(categoria, []).extend(str(Path(r).resolve()) for r in raizes)
        if somente_leitura:
            self.leitura_so.add(categoria)

    def proibe(self, raiz, motivo):
        self.proibidos.append((str(Path(raiz).resolve()), motivo))

    def nega(self, caminho, motivo):
        """Arquivo que o produto tenta ler e o protocolo nega (ex.: .env): impede a leitura sem ler o conteúdo."""
        self.negados_decl.append((str(Path(caminho).resolve()), motivo))

    def congela(self, raiz, arvore_sha):
        base = Path(raiz).resolve()
        for rel, h in arvore_sha.items():
            self.congelados[str(base / rel)] = h

    def congela_arquivos(self, mapa):
        for p, h in mapa.items():
            self.congelados[str(Path(p).resolve())] = h
        self.permite("externo", *mapa.keys(), somente_leitura=True)

    def registra(self, tipo, detalhe):
        self.violacoes.append({"tipo": tipo, "detalhe": str(detalhe)[:400], "papel": self.papel,
                               "quando": round(time.time(), 3)})

    @staticmethod
    def _dentro(p, raiz):
        return p == raiz or p.startswith(raiz.rstrip("\\/") + os.sep)

    def classifica(self, caminho):
        p = str(Path(caminho).resolve())
        baixo = p.replace("\\", "/").lower()
        if any(g in baixo for g in GOLD_PADROES):
            return p, "proibido", "gold"
        for alvo, motivo in self.negados_decl:
            if p == alvo:
                return p, "negado", motivo
        for raiz, motivo in self.proibidos:
            if self._dentro(p, raiz):
                return p, "proibido", motivo
        melhor = None
        for cat, raizes in self.permitidos.items():
            for raiz in raizes:
                if self._dentro(p, raiz) and (melhor is None or len(raiz) > len(melhor[1])):
                    melhor = (cat, raiz)
        return (p, melhor[0], "") if melhor else (p, "fora_da_lista", "")

    def checa_preparo(self, caminho):
        """Antes de ler/hashear na preparação do congelamento: caminho proibido ou negado não é lido."""
        p, cat, motivo = self.classifica(caminho)
        if cat in ("proibido", "negado"):
            self.registra("preparo_proibido", f"{motivo}: {p}")
            raise Violacao(f"caminho proibido na preparação ({motivo})")
        return p

    def verifica_acesso(self, caminho, modo, _abrir):
        if isinstance(caminho, int):
            return
        p, cat, motivo = self.classifica(caminho)
        escrita = any(c in modo for c in "wax+")
        if cat == "negado":
            self.negados.append({"caminho": p, "motivo": motivo, "escrita": escrita})
            raise PermissionError(f"acesso negado por declaração do protocolo ({motivo})")
        if cat == "proibido":
            self.registra("acesso_proibido", f"{motivo}: {p}")
            raise Violacao(f"acesso proibido ({motivo})")
        if cat == "fora_da_lista":
            self.registra("fora_da_lista", f"{'escrita' if escrita else 'leitura'}: {p}")
            raise Violacao("acesso fora da lista permitida")
        if escrita and cat in self.leitura_so:
            self.registra("escrita_em_entrada", f"{cat}: {p}")
            raise Violacao("escrita em área somente leitura")
        reg = self.acessos.setdefault(p, {"categoria": cat, "modo": set(), "sha": None, "n": 0})
        reg["modo"].add("w" if escrita else "r")
        reg["n"] += 1
        if not escrita and p in self.congelados and not os.path.isfile(p):
            self._uma_vez("insumo_desaparecido", p)   # esperado no congelamento: ausência é quebra, não opcional
            raise Violacao("insumo congelado ausente ou não utilizável como arquivo")
        if escrita or cat in ("codigo", "saida", "protocolo") or not os.path.isfile(p):
            return
        atual = sha_arq(p, _abrir)                     # TODA abertura de entrada é conferida
        if reg["sha"] is None:
            reg["sha"] = atual
        if cat in ("comum", "externo") and p not in self.congelados:
            self.registra("insumo_nao_congelado", p)
            raise Violacao("insumo comum/externo fora do congelamento")
        esperado = self.congelados.get(p) or self.primeiro.setdefault(p, atual)
        if atual != esperado:
            self.registra("insumo_divergente", p)
            raise Violacao("insumo com hash divergente do congelado/da 1ª leitura")

    @contextlib.contextmanager
    def comandos(self, nomes):
        """Permissão temporária e nominal de subprocesso; fecha mesmo com exceção."""
        self.comandos_permitidos = frozenset(n.lower() for n in nomes)
        try:
            yield self
        finally:
            self.comandos_permitidos = frozenset()

    def comando_permitido(self, args):
        prim = args[0] if isinstance(args, (list, tuple)) and args else str(args).split()[0] if args else ""
        nome = Path(str(prim)).name.lower()
        return nome in self.comandos_permitidos or nome.removesuffix(".exe") in self.comandos_permitidos

    def instala(self):
        if self._instalado:
            return self
        abrir = io.open
        self._abrir_original = abrir
        travas = self

        def aberto(file, mode="r", *a, **k):
            travas.verifica_acesso(file, mode, abrir)
            return abrir(file, mode, *a, **k)

        builtins.open = io.open = aberto

        def sem_rede(*a, **k):
            travas.registra("rede", repr(a)[:120])
            raise Violacao("rede bloqueada")

        for nome in ("connect", "connect_ex"):
            setattr(socket.socket, nome, sem_rede)
        socket.create_connection = sem_rede
        socket.getaddrinfo = sem_rede
        popen = subprocess.Popen

        class _Popen(popen):
            def __init__(self_, args, *a, **k):
                if not travas.comando_permitido(args):
                    travas.registra("subprocesso", repr(args)[:160])
                    raise Violacao("subprocesso não autorizado")
                super().__init__(args, *a, **k)

        subprocess.Popen = _Popen
        self._instalado = True
        return self

    def bloqueia_compilador(self, modulo_vocab):
        travas = self

        def sem_compilar(*a, **k):
            travas.registra("compilador", "compile_course_vocabulary")
            raise Violacao("compilador de vocabulário bloqueado")

        modulo_vocab.compile_course_vocabulary = sem_compilar

    def _uma_vez(self, tipo, p):
        if p not in self._integridade:
            self._integridade.add(p)
            self.registra(tipo, p)

    def confere_congelados(self):
        """Inventário congelado INTEIRO, lido ou não: cada arquivo esperado existe como arquivo e tem o hash congelado.
        Roda no início e no fim de cada worker; pega o consumidor que só consulta exists()/is_file() ou nunca abre."""
        prob = []
        for p, h in sorted(self.congelados.items()):
            if not os.path.isfile(p):
                self._uma_vez("insumo_desaparecido", p)
                prob.append(f"insumo congelado ausente: {p}")
            elif sha_arq(p, self._abrir_original) != h:
                self._uma_vez("insumo_divergente", p)
                prob.append(f"insumo congelado divergente: {p}")
        return prob

    def rehash_leituras(self):
        """Ao final: tudo o que foi lido continua existindo e igual em disco, e o inventário congelado inteiro confere."""
        for p, reg in self.acessos.items():
            if reg["sha"] and "r" in reg["modo"]:
                if not os.path.exists(p):
                    self._uma_vez("insumo_desaparecido", p)
                elif sha_arq(p, self._abrir_original) != reg["sha"]:
                    self._uma_vez("insumo_alterado_durante_execucao", p)
        self.confere_congelados()

    def resumo(self):
        return {"violacoes": list(self.violacoes), "negados": list(self.negados),
                "acessos": {p: {"categoria": r["categoria"], "modo": sorted(r["modo"]), "sha": r["sha"], "n": r["n"]}
                            for p, r in sorted(self.acessos.items())}}


def encerra(travas, *, ok, codigo_falha=2):
    if travas.violacoes or not ok:
        sys.stdout.flush()
        sys.exit(codigo_falha)


# ------------------------------------------------------------------------------------------- congelamento
def id_congelamento(normativo):
    return sha_json({"esquema": ESQUEMA_CONGELAMENTO, **normativo})


def conteudo_sha(captura):
    return sha_json({k: v for k, v in captura.items() if k != "conteudo_sha"})


def valida_congelamento(cong):
    """Ligações: normativo → id_comum; descritor de insumos de cada braço → insumos_braco."""
    prob = []
    try:
        if id_congelamento(cong["normativo"]) != cong["id_comum"]:
            prob.append("normativo não corresponde ao id_comum")
        for b, ins in (cong.get("insumos") or {}).items():
            if sha_json(ins) != (cong.get("insumos_braco") or {}).get(b):
                prob.append(f"descritor de insumos de {b} não corresponde a insumos_braco")
    except (KeyError, TypeError, ValueError) as exc:
        prob.append(f"congelamento malformado: {type(exc).__name__}: {exc}")
    return prob


# ------------------------------------------------------------------------------------------- validação de captura
def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _lista_str(x):
    return isinstance(x, list) and all(isinstance(i, str) for i in x)


def valida_chamada(c, onde):
    prob = []
    if not isinstance(c, dict):
        return [f"{onde}: chamada não é objeto"]
    for campo in ("unidade_fornecida", "pontuacoes", "vencedor", "conf", "ambigua", "motivos"):
        if campo not in c:
            prob.append(f"{onde}: campo ausente {campo}")
    if "unidade_fornecida" in c and not isinstance(c["unidade_fornecida"], str):
        prob.append(f"{onde}: unidade_fornecida não é texto")
    pts = c.get("pontuacoes")
    if "pontuacoes" in c:
        if not isinstance(pts, list):
            prob.append(f"{onde}: pontuacoes não é lista de registros")
        else:
            vistos = set()
            for i, x in enumerate(pts):
                if not (isinstance(x, dict) and isinstance(x.get("unidade"), str) and isinstance(x.get("topico"), str)):
                    prob.append(f"{onde}: pontuacoes[{i}] sem identidade (unidade, tópico)")
                    continue
                if not _num(x.get("score")):
                    prob.append(f"{onde}: pontuacoes[{i}] score não numérico/finito")
                chave = (x["unidade"], x["topico"])
                if chave in vistos:
                    prob.append(f"{onde}: candidato duplicado {chave}")
                vistos.add(chave)
    v = c.get("vencedor")
    if "vencedor" in c and not (isinstance(v, dict) and isinstance(v.get("unidade"), str) and isinstance(v.get("topico"), str)):
        prob.append(f"{onde}: vencedor sem identidade (unidade, tópico)")
    if "conf" in c and not _num(c["conf"]):
        prob.append(f"{onde}: conf não numérica/finita")
    if "ambigua" in c and not isinstance(c["ambigua"], bool):
        prob.append(f"{onde}: ambigua não é booleano")
    if "motivos" in c and not _lista_str(c["motivos"]):
        prob.append(f"{onde}: motivos não é lista de textos")
    return prob


def valida_registro(r, sig=None, eid=None):
    """Estrutura de um registro de material (não julga se a resposta está certa)."""
    onde = f"{sig}/{eid}"
    if not isinstance(r, dict):
        return [f"{onde}: registro não é objeto"]
    prob = []
    for campo in ("curso", "id", "chamado", "motivo_nao_chamado", "p1", "chamadas_posteriores", "taxonomia_sha", "final"):
        if campo not in r:
            prob.append(f"{onde}: campo ausente {campo}")
    if sig is not None and r.get("curso") != sig:
        prob.append(f"{onde}: curso interno diferente da chave externa")
    if eid is not None and r.get("id") != eid:
        prob.append(f"{onde}: id interno diferente da chave externa")
    if "chamado" in r and not isinstance(r["chamado"], bool):
        prob.append(f"{onde}: chamado não é booleano")
    if r.get("chamado") is True:
        prob += valida_chamada(r.get("p1"), f"{onde}/p1")
        if r.get("motivo_nao_chamado") != "":
            prob.append(f"{onde}: chamado com motivo de não chamada")
    elif r.get("chamado") is False:
        if r.get("p1") is not None:
            prob.append(f"{onde}: não chamado com p1")
        if not isinstance(r.get("motivo_nao_chamado"), str) or not r.get("motivo_nao_chamado"):
            prob.append(f"{onde}: não chamado sem motivo registrado")
    posteriores = r.get("chamadas_posteriores")
    if "chamadas_posteriores" in r:
        if not isinstance(posteriores, list):
            prob.append(f"{onde}: chamadas_posteriores não é lista")
        else:
            for i, c in enumerate(posteriores):
                prob += valida_chamada(c, f"{onde}/posterior[{i}]")
    fin = r.get("final")
    if "final" in r:
        if not isinstance(fin, dict):
            prob.append(f"{onde}: final não é objeto")
        else:
            for c in ("bloco", "unidade", "sub"):
                if not isinstance(fin.get(c), str):
                    prob.append(f"{onde}: final.{c} ausente ou não-texto")
            if "conf_sub" not in fin or not (fin["conf_sub"] is None or _num(fin["conf_sub"])):
                prob.append(f"{onde}: final.conf_sub ausente ou não numérica/finita")
            for c in ("motivos_sub", "motivos_unidade"):
                if not _lista_str(fin.get(c)):
                    prob.append(f"{onde}: final.{c} ausente ou não é lista de textos")
    return prob


def _outro_braco(caminho, braco):
    c = caminho.replace("\\", "/")
    for b in BRACOS + ("_IDENTIDADE",):
        if b != braco and (f"/palcos/{b}/" in c or f"/snapshots/{b}/" in c):
            return b
    return None


def valida_captura(cap, *, congelamento, braco, modo):
    """Problemas que impedem usar/reutilizar a captura. As expectativas vêm do CONGELAMENTO, não da captura."""
    if not isinstance(cap, dict):
        return ["captura não é objeto"]
    prob = []
    norm = congelamento["normativo"]
    inv = norm["inventario"]
    esperado_ins = (congelamento.get("insumos") or {}).get(braco) or {}
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
    if cap.get("violacoes") != []:
        prob.append(f"violações registradas ou campo ausente: {cap.get('violacoes')!r:.80}")
    if not isinstance(cap.get("negados"), list):
        prob.append("registro de negados ausente")
    acessos = cap.get("acessos")
    if not isinstance(acessos, dict):
        prob.append("registro de leituras ausente")
    else:
        for p, a in acessos.items():
            if not isinstance(a, dict) or a.get("categoria") not in CATEGORIAS_LEITURA:
                prob.append(f"leitura em categoria não permitida: {p}")
            outro = _outro_braco(p, braco)
            if outro:
                prob.append(f"leitura de estado de outro braço ({outro}): {p}")
    try:
        if cap.get("conteudo_sha") != conteudo_sha(cap):
            prob.append("conteúdo alterado (hash não confere)")
    except ValueError:
        prob.append("conteúdo não serializável (valor não finito)")
    if cap.get("inventario") != inv:
        faltam = sorted(set(inv) - set(cap.get("inventario") or {}))
        sobram = sorted(set(cap.get("inventario") or {}) - set(inv))
        prob.append(f"inventário divergente (cursos ausentes {faltam}, extras {sobram})")
    por_curso = cap.get("por_curso")
    if not isinstance(por_curso, dict) or set(por_curso) != set(inv):
        prob.append("por_curso ausente ou com cursos divergentes")
        por_curso = {}
    for sig in inv:
        pc = por_curso.get(sig) or {}
        if pc.get("taxonomia_sha") != (esperado_ins.get(sig) or {}).get("taxonomia_sha"):
            prob.append(f"{sig}: taxonomia usada != snapshot congelado do braço")
        if pc.get("indice_sha") != (esperado_ins.get(sig) or {}).get("indice_sha"):
            prob.append(f"{sig}: índice de unidade usado != snapshot congelado do braço")
    ver = cap.get("verificacoes")
    if not isinstance(ver, dict):
        prob.append("verificacoes ausentes")
    else:
        esperado_manual = (norm.get("esperado") or {}).get("manual", {}).get(braco)
        if ver.get("manual_carregado") != esperado_manual:
            prob.append("manual efetivamente carregado != mapa congelado")
        if "temporais" in norm and ver.get("artefatos_temporais_sha") != norm["temporais"]:
            prob.append("artefatos temporais != referência congelada")
        if braco != "CRU" and ver.get("taxonomia_congelada_lida") != []:
            prob.append("braço não-CRU leu a taxonomia congelada (ou campo ausente)")
    dec = cap.get("decisoes")
    if modo == "carga":
        if dec != {}:
            prob.append("carga com decisões finais")
        return prob
    if not isinstance(dec, dict) or set(dec) != set(inv):
        prob.append("decisões sem os cursos do inventário")
        return prob
    for sig, ids in inv.items():
        d = dec[sig]
        if not isinstance(d, dict) or sorted(d) != sorted(ids):
            prob.append(f"{sig}: IDs das decisões != inventário")
            continue
        esperado_tax = (por_curso.get(sig) or {}).get("taxonomia_sha")
        for eid in ids:
            r = d[eid]
            prob += valida_registro(r, sig, eid)
            if isinstance(r, dict):
                if r.get("taxonomia_sha") != esperado_tax:
                    prob.append(f"{sig}/{eid}: taxonomia_sha do material != do curso")
                if r.get("chamado") is True and isinstance(r.get("p1"), dict) and isinstance(r.get("final"), dict):
                    if r["p1"].get("unidade_fornecida") != r["final"].get("unidade"):
                        prob.append(f"{sig}/{eid}: unidade da 1ª passada != final")
    return prob


def valida_historica(cap, congelamento, braco=None, modo="capturar"):
    """Validação de uma captura HISTÓRICA só com artefatos imutáveis (captura + congelamento), sem exigir o checkout."""
    return valida_congelamento(congelamento) + valida_captura(cap, congelamento=congelamento,
                                                               braco=braco or cap.get("braco"), modo=modo)
