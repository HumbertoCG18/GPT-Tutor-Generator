"""Transliteracao no strip_accents: chars que NFKD nao decompoe.

Caso real (TCC aula-10): o PDF do professor veio com U+0131 (dotless i,
"Reconhec\u0131veis") — NFKD nao decompoe, o slug herdou o char e o id ficou
com "\u0131" para sempre (join funciona, mas o vocabulario nao casa "i").
O id existente NAO muda (renomear quebraria golds); o fix vale para imports
e matching futuros."""

from src.utils.helpers import slugify, strip_accents


def test_dotless_i_translitera_para_i():
    assert strip_accents("Reconhec\u0131veis") == "Reconhec1veis".replace("1", "i")
    assert slugify("Linguagens Reconhec\u0131veis e Decid\u0131veis") == (
        "linguagens-reconheciveis-e-decidiveis"
    )


def test_i_maiusculo_com_ponto_ja_resolvia_por_nfkd():
    # U+0130 (I com ponto) decompoe em NFKD; garante que segue funcionando.
    assert slugify("\u0130stanbul") == "istanbul"
