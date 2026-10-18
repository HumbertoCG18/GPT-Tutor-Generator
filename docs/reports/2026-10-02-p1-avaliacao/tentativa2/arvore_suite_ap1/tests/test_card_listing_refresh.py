"""Regressao: _ARQUIVOS_DO_CARD.txt deve espelhar os arquivos REAIS do card
(nomes M365 no disco), nao a lista da API Moodle (que fica stale/case-errada).

Bug relatado 2026-07-01: card 'DevOps' listava 'DevOps.pdf' (nome Moodle) mas o
arquivo real era 'devops.pdf' (M365). refresh_card_listings_from_disk reconcilia.
"""
from src.builder.sources.moodle import refresh_card_listings_from_disk


def test_refresh_mirrors_actual_files_not_stale_moodle_names(tmp_path):
    card = tmp_path / "DevOps"
    card.mkdir()
    (card / "devops.pdf").write_bytes(b"%PDF-1.4")
    (card / "Kubernetes.pdf").write_bytes(b"%PDF-1.4")
    # listing velho: nomes Moodle (case errada) + instrucao obsoleta
    (card / "_ARQUIVOS_DO_CARD.txt").write_text(
        "Arquivos esperados neste card (baixe do Moodle e coloque aqui):\n\n"
        "DevOps.pdf\nKubernetes.pdf\n", encoding="utf-8")

    n = refresh_card_listings_from_disk(tmp_path)

    assert n == 1
    txt = (card / "_ARQUIVOS_DO_CARD.txt").read_text(encoding="utf-8")
    assert "devops.pdf" in txt            # nome real M365
    assert "Kubernetes.pdf" in txt
    assert "DevOps.pdf\n" not in txt       # nome Moodle stale sumiu
    assert "baixe do Moodle" not in txt    # instrucao obsoleta sumiu


def test_refresh_excludes_listing_itself_and_handles_multiple_cards(tmp_path):
    micro = tmp_path / "Microsservicos"; micro.mkdir()
    (micro / "roteiro4.zip").write_bytes(b"PK\x03\x04")
    rev = tmp_path / "Revisao"; rev.mkdir()
    (rev / "revisao_p1.pdf").write_bytes(b"%PDF-1.4")
    (rev / "revisao_p2.pdf").write_bytes(b"%PDF-1.4")

    n = refresh_card_listings_from_disk(tmp_path)

    assert n == 2
    tmicro = (micro / "_ARQUIVOS_DO_CARD.txt").read_text(encoding="utf-8")
    assert "roteiro4.zip" in tmicro
    assert "_ARQUIVOS_DO_CARD.txt" not in tmicro   # nao se auto-lista
    trev = (rev / "_ARQUIVOS_DO_CARD.txt").read_text(encoding="utf-8")
    assert "revisao_p1.pdf" in trev and "revisao_p2.pdf" in trev


def test_refresh_noop_on_missing_dir(tmp_path):
    assert refresh_card_listings_from_disk(tmp_path / "nao-existe") == 0
