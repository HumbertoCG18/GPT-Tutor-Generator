"""AUDITORIA DE CORRECAO das relacoes termo -> topico, SEM ver placar nem gold (14/09, protocolo do astra na revisao da meta).

O astra pediu medir "relacoes corretas e incorretas" separado do efeito no motor, e "auditar relacoes sem mostrar seu efeito no
placar; nao corrigir o mapa depois dessa auditoria na mesma rodada". Este script so MONTA o insumo e depois CONSOLIDA a resposta;
quem julga e um modelo numa sessao limpa (agy), sem acesso a arquivo nenhum do projeto.

  monta <relacoes_X_14-09.json>   -> auditoria_<X>_entrada.md   (prompt congelado + relacoes numeradas com rotulo e trecho)
  consolida <X>                   -> auditoria_<X>_14-09.json   (veredito por relacao + totais por curso)

O julgamento e de LLM: e leitura, nao medicao. Serve para separar ganho de ruido na leitura dos bracos, nunca para filtrar
relacao antes do motor (isso mudaria o braco depois de ver).

0 chamadas (a chamada e feita fora, pelo agy). Uso: PYTHONUTF8=1 python -B auditoria_relacoes_14-09.py monta relacoes_A_14-09.json
"""
import collections
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
_spec = importlib.util.spec_from_file_location("extrator", HERE / "extrator_relacoes_14-09.py")
ex = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ex)
BASES = {c: b for c, b in ex.COURSES}

PROMPT = """Voce e um professor universitario de computacao auditando uma lista de RELACOES extraidas automaticamente.
Cada relacao diz: "o TERMO pertence ao TOPICO do plano de ensino". O termo foi achado no material do professor, listado sob uma
CATEGORIA (um titulo ou um rotulo com dois-pontos), e o topico foi escolhido por uma regra automatica.

Para CADA relacao, classifique:
  CORRETA      o termo e um conceito, tecnica, ferramenta ou assunto que um aluno estudaria dentro daquele topico
  INCORRETA    o termo pertence a outro assunto; a ligacao com o topico e errada
  RUIDO        o termo nao e um conceito: e frase de prosa, referencia bibliografica, link, descricao de imagem, instrucao
  INDETERMINADA  nao da para decidir so com o que esta aqui

Regras: julgue so com o que esta escrito; nao use ferramentas; nao explique; responda apenas o JSON do schema, uma entrada por id.
"""

SCHEMA = {"type": "object", "properties": {"vereditos": {"type": "array", "items": {"type": "object", "properties": {
    "id": {"type": "integer"}, "classe": {"type": "string", "enum": ["CORRETA", "INCORRETA", "RUIDO", "INDETERMINADA"]}},
    "required": ["id", "classe"]}}}, "required": ["vereditos"]}


def rotulos():
    out = {}
    for c, b in BASES.items():
        p = b / "course/.content_taxonomy.json"
        if p.exists():
            t = json.loads(p.read_text(encoding="utf-8-sig"))
            out[c] = {x["code"]: x["label"] for u in t["units"] for x in u["topics"]}
    return out


def monta(arquivo):
    rel = json.loads((HERE / arquivo).read_text(encoding="utf-8"))["relacoes"]
    rot = rotulos()
    X = Path(arquivo).stem.replace("relacoes_", "").replace("_14-09", "")
    linhas = [PROMPT, "", "RELACOES:"]
    for i, r in enumerate(rel, 1):
        linhas.append(f"[{i}] curso {r['curso']} | TOPICO {r['topic_code']} {rot[r['curso']].get(r['topic_code'], '?')} | "
                      f"CATEGORIA: {r['categoria'][:90]} | TERMO: {r['termo'][:120]}")
    (HERE / f"auditoria_{X}_entrada.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    (HERE / "auditoria_schema_14-09.json").write_text(json.dumps(SCHEMA, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"entrada: auditoria_{X}_entrada.md · {len(rel)} relacoes")


def consolida(X):
    rel = json.loads((HERE / f"relacoes_{X}_14-09.json").read_text(encoding="utf-8"))["relacoes"]
    env = json.loads((HERE / f"auditoria_{X}_resposta.json").read_text(encoding="utf-8"))
    r = env.get("response")
    d = json.loads(r) if isinstance(r, str) else r
    ver = {int(v["id"]): v["classe"] for v in d["vereditos"]}
    tot = collections.Counter()
    por = collections.defaultdict(collections.Counter)
    saida = []
    for i, rr in enumerate(rel, 1):
        cl = ver.get(i, "SEM_RESPOSTA")
        tot[cl] += 1
        por[rr["curso"]][cl] += 1
        saida.append(dict(rr, classe=cl))
    (HERE / f"auditoria_{X}_14-09.json").write_text(json.dumps({"totais": dict(tot), "por_curso": {k: dict(v) for k, v in por.items()},
                                                                "relacoes": saida}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"auditoria {X}: {len(rel)} relacoes · {dict(tot)} · tokens {(env.get('usage') or {}).get('total_tokens')} · negadas {env.get('denied_actions')}")
    for c, v in por.items():
        print(f"   {c:4} {dict(v)}")


if __name__ == "__main__":
    if sys.argv[1] == "monta":
        monta(sys.argv[2])
    else:
        consolida(sys.argv[2])
