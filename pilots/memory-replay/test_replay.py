"""Testes do replay offline de memória (issue #45). Só stdlib.

Rodar: python -m unittest discover -s pilots/memory-replay -p "test_*.py"
"""

import ast
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import replay as rp  # noqa: E402

SCRIPT = HERE / "replay.py"
EXAMPLE = HERE / "example.json"


def base():
    return {
        "version": 1,
        "task": "revisar plano de estudos",
        "project": "alfa",
        "candidates": [
            {"id": "m1", "project": "alfa", "text": "nota um", "protected": False},
            {"id": "m2", "project": "alfa", "text": "nota dois", "protected": False},
            {"id": "m3", "project": "alfa", "text": "nota três", "protected": True},
            {"id": "m4", "project": "alfa", "text": "nota dois", "protected": False},
            {"id": "x1", "project": "beta", "text": "nota de outro projeto", "protected": False},
        ],
        "required_ids": ["m1", "m3"],
        "simulated_decisions": [],
    }


def decide(data, **decisions):
    data["simulated_decisions"] = [{"id": k, "decision": v} for k, v in decisions.items()]
    return data


def cli(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, cwd=cwd, timeout=60
    )


class BaselineTest(unittest.TestCase):
    def test_baseline_por_projeto_e_dedup_com_proveniencia(self):
        report = rp.replay(base())
        b = report["baseline"]
        self.assertEqual(b["selected_ids"], ["m1", "m2", "m3"])
        self.assertEqual(b["provenance"], {"m1": ["m1"], "m2": ["m2", "m4"], "m3": ["m3"]})
        self.assertEqual(b["protected_ids"], ["m3"])
        self.assertEqual(report["excluded_other_project"], ["x1"])
        self.assertEqual(report["candidates_total"], 5)

    def test_sem_decisoes_simulado_igual_ao_baseline(self):
        report = rp.replay(base())
        self.assertEqual(report["simulated"]["selected_ids"], report["baseline"]["selected_ids"])
        self.assertEqual(report["simulated"]["preserved"]["missing"], ["m1", "m2", "m3"])
        self.assertEqual(report["simulated"]["dropped_ids"], [])

    def test_duplicata_protegida_protege_o_grupo(self):
        data = base()
        data["candidates"][3]["protected"] = True  # m4, alias de m2
        report = rp.replay(decide(data, m2="drop"))
        self.assertEqual(report["baseline"]["protected_ids"], ["m2", "m3"])
        self.assertIn("m2", report["simulated"]["selected_ids"])
        self.assertEqual(report["simulated"]["preserved"]["protected"], ["m2"])

    def test_dedup_e_exata_sem_normalizacao(self):
        data = base()
        data["candidates"] = [
            {"id": "a", "project": "alfa", "text": "café", "protected": False},
            {"id": "b", "project": "alfa", "text": "café", "protected": False},
            {"id": "c", "project": "alfa", "text": "café ", "protected": False},
        ]
        data["required_ids"] = []
        self.assertEqual(rp.replay(data)["baseline"]["selected_ids"], ["a", "b", "c"])

    def test_duplicata_de_outro_projeto_nao_vaza_na_proveniencia(self):
        data = base()
        data["candidates"][4]["text"] = "nota um"  # x1 (beta) com texto de m1
        report = rp.replay(data)
        self.assertEqual(report["baseline"]["provenance"]["m1"], ["m1"])
        self.assertEqual(report["excluded_other_project"], ["x1"])

    def test_deterministico_e_nao_muta_entrada(self):
        data = decide(base(), m2="drop")
        snapshot = copy.deepcopy(data)
        self.assertEqual(rp.replay(data), rp.replay(data))
        self.assertEqual(data, snapshot)


class SimulatedTest(unittest.TestCase):
    def test_drop_explicito_exclui_so_no_ramo_simulado(self):
        report = rp.replay(decide(base(), m2="drop"))
        self.assertEqual(report["baseline"]["selected_ids"], ["m1", "m2", "m3"])
        self.assertEqual(report["simulated"]["selected_ids"], ["m1", "m3"])
        self.assertEqual(report["simulated"]["dropped_ids"], ["m2"])

    def test_fail_open_preserva(self):
        casos = [
            ("keep", "keep"),
            ("uncertain", "uncertain"),
            ("error", "error"),
            ("DROP", "invalid"),
            (" drop", "invalid"),
            ("", "invalid"),
            (None, "invalid"),
            (1, "invalid"),
            (True, "invalid"),
            (["drop"], "invalid"),
            ({"value": "drop"}, "invalid"),
        ]
        for decisao, motivo in casos:
            with self.subTest(decisao=decisao):
                sim = rp.replay(decide(base(), m2=decisao))["simulated"]
                self.assertIn("m2", sim["selected_ids"])
                self.assertEqual(sim["preserved"][motivo], ["m2"])
                self.assertEqual(sim["dropped_ids"], [])

    def test_entrada_sem_campo_decision_preserva_como_invalida(self):
        data = base()
        data["simulated_decisions"] = [{"id": "m2"}]
        sim = rp.replay(data)["simulated"]
        self.assertEqual(sim["preserved"]["invalid"], ["m2"])
        self.assertIn("m2", sim["selected_ids"])

    def test_drop_em_protegido_e_ignorado_e_reportado(self):
        sim = rp.replay(decide(base(), m3="drop"))["simulated"]
        self.assertIn("m3", sim["selected_ids"])
        self.assertEqual(sim["preserved"]["protected"], ["m3"])

    def test_decisao_sobre_alias_ou_outro_projeto_nao_exclui(self):
        sim = rp.replay(decide(base(), m4="drop", x1="drop"))["simulated"]
        self.assertEqual(sim["selected_ids"], ["m1", "m2", "m3"])
        self.assertEqual(sim["not_applicable_decisions"], ["m4", "x1"])
        self.assertEqual(sim["dropped_ids"], [])


class EvaluationTest(unittest.TestCase):
    def test_rotulos_nao_influenciam_selecao(self):
        selecoes = []
        for rotulos in ("ausente", [], ["m2"], ["m1", "m3"], ["m4"]):
            data = decide(base(), m2="drop", m1="uncertain")
            if rotulos == "ausente":
                del data["required_ids"]
            else:
                data["required_ids"] = rotulos
            report = rp.replay(data)
            selecoes.append((report["baseline"]["selected_ids"], report["simulated"]["selected_ids"]))
        self.assertEqual(len({json.dumps(s) for s in selecoes}), 1)

    def test_perda_detectada(self):
        data = decide(base(), m2="drop")
        data["required_ids"] = ["m1", "m2"]
        report = rp.replay(data)
        self.assertEqual(report["baseline"]["evaluation"]["lost_ids"], [])
        self.assertEqual(report["baseline"]["evaluation"]["recall"], 1.0)
        ev = report["simulated"]["evaluation"]
        self.assertEqual(ev["lost_ids"], ["m2"])
        self.assertEqual(ev["recall"], 0.5)
        self.assertEqual(ev["recall_status"], "measured")
        self.assertEqual(ev["required_total"], 2)

    def test_required_alias_retido_via_proveniencia_e_perdido_com_o_grupo(self):
        data = base()
        data["required_ids"] = ["m4"]
        self.assertEqual(rp.replay(data)["baseline"]["evaluation"]["recall"], 1.0)
        ev = rp.replay(decide(data, m2="drop"))["simulated"]["evaluation"]
        self.assertEqual(ev["lost_ids"], ["m4"])
        self.assertEqual(ev["recall"], 0.0)

    def test_required_de_outro_projeto_conta_como_perdido_nos_dois_ramos(self):
        data = base()
        data["required_ids"] = ["m1", "x1"]
        report = rp.replay(data)
        self.assertEqual(report["baseline"]["evaluation"]["lost_ids"], ["x1"])
        self.assertEqual(report["simulated"]["evaluation"]["lost_ids"], ["x1"])

    def test_sem_rotulos_recall_indefinido(self):
        data = base()
        del data["required_ids"]
        for ramo in ("baseline", "simulated"):
            ev = rp.replay(data)[ramo]["evaluation"]
            self.assertIsNone(ev["recall"])
            self.assertIsNone(ev["lost_ids"])
            self.assertEqual(ev["labels"], "absent")
            self.assertEqual(ev["recall_status"], "undefined_no_labels")

    def test_nenhum_required_recall_indefinido(self):
        data = base()
        data["required_ids"] = []
        ev = rp.replay(data)["simulated"]["evaluation"]
        self.assertIsNone(ev["recall"])
        self.assertEqual(ev["labels"], "present")
        self.assertEqual(ev["recall_status"], "undefined_no_required")


class SizeTest(unittest.TestCase):
    def test_unicode_caracteres_e_bytes_utf8(self):
        data = base()
        data["candidates"] = [
            {"id": "ü1", "project": "alfa", "text": "ação 🚀", "protected": False},
            {"id": "k2", "project": "alfa", "text": "日本", "protected": False},
        ]
        data["required_ids"] = ["ü1"]
        report = rp.replay(decide(data, k2="drop"))
        self.assertEqual(report["baseline"]["chars"], 8)
        self.assertEqual(report["baseline"]["utf8_bytes"], 17)
        self.assertEqual(report["simulated"]["chars"], 6)
        self.assertEqual(report["simulated"]["utf8_bytes"], 11)
        self.assertEqual(report["delta"], {"chars": -2, "utf8_bytes": -6, "tokens": None})
        self.assertEqual(report["simulated"]["evaluation"]["recall"], 1.0)

    def test_duplicata_conta_uma_vez(self):
        b = rp.replay(base())["baseline"]
        self.assertEqual(b["chars"], len("nota um") + len("nota dois") + len("nota três"))

    def test_tokens_nao_medidos_por_padrao(self):
        report = rp.replay(base())
        self.assertIsNone(report["baseline"]["tokens"])
        self.assertIsNone(report["simulated"]["tokens"])
        self.assertEqual(
            report["measurement"], {"tokens": "not_measured", "cost": "not_measured", "llm_calls": 0}
        )
        self.assertFalse(any("token" in k for k in report["baseline"] if k != "tokens"))

    def test_tokens_continuam_nulos_mesmo_com_drop(self):
        report = rp.replay(decide(base(), m2="drop"))
        self.assertLess(report["delta"]["chars"], 0)
        self.assertIsNone(report["baseline"]["tokens"])
        self.assertIsNone(report["simulated"]["tokens"])
        self.assertIsNone(report["delta"]["tokens"])
        self.assertEqual(report["measurement"]["tokens"], "not_measured")

    def test_replay_nao_aceita_contador_de_tokens(self):
        for kwargs in ({"count_tokens": len}, {"tokens_label": "x"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(TypeError):
                rp.replay(base(), **kwargs)

    def test_texto_com_surrogate_isolado_e_rejeitado(self):
        data = base()
        data["candidates"][0]["text"] = "quebrado \ud800"
        with self.assertRaises(rp.ReplayError):
            rp.replay(data)


class InvalidInputTest(unittest.TestCase):
    def assertInvalid(self, mutate):
        data = base()
        mutate(data)
        with self.assertRaises(rp.ReplayError):
            rp.replay(data)

    def test_raiz_nao_objeto(self):
        for raiz in ([], "x", None, 1):
            with self.subTest(raiz=raiz), self.assertRaises(rp.ReplayError):
                rp.replay(raiz)

    def test_ids_repetidos_ou_desconhecidos(self):
        casos = {
            "candidato repetido": lambda d: d["candidates"].append(dict(d["candidates"][0])),
            "candidato repetido entre projetos": lambda d: d["candidates"][4].update(id="m1"),
            "required desconhecido": lambda d: d.update(required_ids=["zz"]),
            "required repetido": lambda d: d.update(required_ids=["m1", "m1"]),
            "decisao desconhecida": lambda d: decide(d, zz="drop"),
            "decisao repetida": lambda d: d.update(
                simulated_decisions=[{"id": "m2", "decision": "keep"}, {"id": "m2", "decision": "drop"}]
            ),
        }
        for nome, mutate in casos.items():
            with self.subTest(nome):
                self.assertInvalid(mutate)

    def test_tipos_errados(self):
        casos = {
            "version bool": lambda d: d.update(version=True),
            "version float": lambda d: d.update(version=1.0),
            "version string": lambda d: d.update(version="1"),
            "version desconhecida": lambda d: d.update(version=2),
            "version ausente": lambda d: d.pop("version"),
            "task ausente": lambda d: d.pop("task"),
            "task vazia": lambda d: d.update(task=""),
            "project numero": lambda d: d.update(project=7),
            "candidates objeto": lambda d: d.update(candidates={}),
            "candidato nao objeto": lambda d: d["candidates"].append("m9"),
            "candidato sem text": lambda d: d["candidates"][0].pop("text"),
            "id numero": lambda d: d["candidates"][0].update(id=1),
            "id vazio": lambda d: d["candidates"][0].update(id=""),
            "text numero": lambda d: d["candidates"][0].update(text=42),
            "text vazio": lambda d: d["candidates"][0].update(text=""),
            "protected numero": lambda d: d["candidates"][0].update(protected=1),
            "protected string": lambda d: d["candidates"][0].update(protected="true"),
            "protected null": lambda d: d["candidates"][0].update(protected=None),
            "required string": lambda d: d.update(required_ids="m1"),
            "required null": lambda d: d.update(required_ids=None),
            "required item numero": lambda d: d.update(required_ids=[1]),
            "required item bool": lambda d: d.update(required_ids=[True]),
            "decisions objeto": lambda d: d.update(simulated_decisions={"m2": "drop"}),
            "decisions ausente": lambda d: d.pop("simulated_decisions"),
            "decisao nao objeto": lambda d: d.update(simulated_decisions=["m2"]),
            "decisao sem id": lambda d: d.update(simulated_decisions=[{"decision": "drop"}]),
            "decisao id numero": lambda d: d.update(simulated_decisions=[{"id": 2, "decision": "drop"}]),
            "decisao chave extra": lambda d: d.update(simulated_decisions=[{"id": "m2", "decison": "drop"}]),
            "chave extra na raiz": lambda d: d.update(requried_ids=["m1"]),
            "chave extra no candidato": lambda d: d["candidates"][0].update(score=0.9),
        }
        for nome, mutate in casos.items():
            with self.subTest(nome):
                self.assertInvalid(mutate)

    def test_protegido_de_projeto_errado_gera_erro(self):
        with self.assertRaises(rp.ReplayError) as ctx:
            data = base()
            data["candidates"][4]["protected"] = True
            rp.replay(data)
        self.assertIn("x1", str(ctx.exception))

    def test_json_malformado_chave_duplicada_e_nan(self):
        casos = {
            "truncado": '{"version": 1,',
            "vazio": "",
            "chave duplicada": '{"version": 1, "version": 1}',
            "chave duplicada aninhada": '{"candidates": [{"id": "a", "id": "b"}]}',
            "nan": '{"version": NaN}',
            "infinito": '{"version": Infinity}',
        }
        for nome, texto in casos.items():
            with self.subTest(nome), self.assertRaises(rp.ReplayError):
                rp.parse(texto)

    def test_parse_valido_roundtrip(self):
        self.assertEqual(rp.parse(json.dumps(base())), base())


class CliTest(unittest.TestCase):
    def test_exemplo_imprime_relatorio_json_sem_escrever(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = cli(str(EXAMPLE), cwd=tmp)
            self.assertEqual(list(Path(tmp).iterdir()), [])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stderr, b"")
        report = json.loads(proc.stdout.decode("ascii"))
        sim = report["simulated"]
        self.assertEqual(report["baseline"]["provenance"]["s1"], ["s1", "s4"])
        self.assertEqual(report["excluded_other_project"], ["o1"])
        self.assertEqual(sim["dropped_ids"], ["s2", "s6"])
        self.assertEqual(sim["preserved"]["protected"], ["s3"])
        self.assertEqual(sim["preserved"]["keep"], ["s1"])
        self.assertEqual(sim["preserved"]["uncertain"], ["s5"])
        self.assertEqual(sim["preserved"]["error"], ["s8"])
        self.assertEqual(sim["preserved"]["missing"], ["s7"])
        self.assertEqual(sim["evaluation"]["lost_ids"], ["s2"])
        self.assertAlmostEqual(sim["evaluation"]["recall"], 2 / 3)
        self.assertEqual(report["baseline"]["evaluation"]["recall"], 1.0)
        self.assertEqual(report["measurement"]["tokens"], "not_measured")
        self.assertEqual(report["measurement"]["llm_calls"], 0)
        self.assertLess(report["delta"]["utf8_bytes"], 0)

    def test_exemplo_e_sintetico_e_marcado(self):
        data = rp.load(str(EXAMPLE))
        self.assertTrue(all("fictíci" in c["text"] for c in data["candidates"]))

    def test_entrada_invalida_sai_2_sem_stdout(self):
        with tempfile.TemporaryDirectory() as tmp:
            casos = {
                "malformado.json": '{"version": 1,',
                "id_repetido.json": json.dumps(
                    dict(base(), candidates=[base()["candidates"][0]] * 2)
                ),
                "nao_utf8.json": None,
            }
            for nome, texto in casos.items():
                alvo = Path(tmp) / nome
                alvo.write_bytes(b"\xff\xfe\x00{" if texto is None else texto.encode("utf-8"))
                with self.subTest(nome):
                    proc = cli(str(alvo))
                    self.assertEqual(proc.returncode, 2)
                    self.assertEqual(proc.stdout, b"")
                    self.assertIn(b"erro", proc.stderr)
                    self.assertNotIn(b"Traceback", proc.stderr)

    def test_arquivo_inexistente_sai_2(self):
        proc = cli(str(HERE / "nao-existe.json"))
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, b"")
        self.assertNotIn(b"Traceback", proc.stderr)

    def test_bom_utf8_aceito_e_unicode_na_saida_ascii(self):
        data = base()
        data["candidates"][0]["id"] = "mé🚀"
        data["required_ids"] = ["mé🚀"]
        with tempfile.TemporaryDirectory() as tmp:
            alvo = Path(tmp) / "bom.json"
            alvo.write_bytes(b"\xef\xbb\xbf" + json.dumps(data, ensure_ascii=False).encode("utf-8"))
            proc = cli(str(alvo))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        report = json.loads(proc.stdout.decode("ascii"))
        self.assertEqual(report["baseline"]["selected_ids"][0], "mé🚀")

    def test_flag_tiktoken_recusada_como_argumento_desconhecido(self):
        proc = cli(str(EXAMPLE), "--tiktoken")
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, b"")
        self.assertIn(b"unrecognized arguments", proc.stderr)
        self.assertNotIn(b"Traceback", proc.stderr)

    def test_help_nao_oferece_medicao_de_tokens(self):
        proc = cli("--help")
        self.assertEqual(proc.returncode, 0)
        self.assertNotIn(b"token", proc.stdout.lower())


class OfflineContractTest(unittest.TestCase):
    def test_imports_limitados_a_stdlib_sem_rede_ou_banco(self):
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        nomes = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                nomes.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                nomes.add((node.module or "").split(".")[0])
        self.assertLessEqual(nomes, {"argparse", "json", "sys"})
        self.assertNotIn("tiktoken", SCRIPT.read_text(encoding="utf-8").lower())

    def test_sem_abertura_de_arquivo_para_escrita(self):
        fonte = SCRIPT.read_text(encoding="utf-8")
        self.assertEqual(fonte.count("open("), 1)
        self.assertNotIn("write", fonte.replace("sys.stderr", ""))


if __name__ == "__main__":
    unittest.main()
