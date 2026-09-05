"""Spike de viabilidade M365/OneDrive — DESCARTÁVEL, não é a feature final.

Confirma 3 coisas contra o tenant PUCRS antes de desenhar o importer OneDrive:
  1. Device-code OAuth funciona com client público (Azure CLI) sem registrar app.
  2. Microsoft Graph /shares resolve um link de compartilhamento do professor.
  3. Dá pra baixar os bytes reais (PDF íntegro) com o token delegado do aluno.

Login é interativo: o script imprime um código; você abre a URL e cola o código
(autentica com a conta PUCRS no navegador). Nenhum segredo é impresso.

Uso:
    python -m scripts.m365_probe "<link de Copiar link do OneDrive>"

Aceita link de arquivo OU de pasta. Pasta -> lista e baixa o 1º PDF como amostra.
"""
from __future__ import annotations

import base64
import sys
import time
import urllib.parse

import requests

# Client público "Microsoft Graph Command Line Tools": pré-autorizado pro Graph,
# device-code, Files.Read delegado. (O client do Azure CLI dá AADSTS65002 — serve
# pro ARM, não pro Graph.)
_CLIENT_ID = "14d82eec-204b-4c2f-b7e8-296a70dab67e"
_AUTHORITY = "https://login.microsoftonline.com/organizations/oauth2/v2.0"
_SCOPE = "Files.Read.All Sites.Read.All offline_access"
_GRAPH = "https://graph.microsoft.com/v1.0"


def _encode_share_url(url: str) -> str:
    b = base64.urlsafe_b64encode(url.encode("utf-8")).decode("ascii").rstrip("=")
    return "u!" + b


def _parse_viewer(url: str):
    """URL de visualizador OneDrive -> (host, server_relative_path) ou None.

    Ex.: .../personal/10070245_pucrs_br/_layouts/15/onedrive.aspx?id=%2Fpersonal%2F...
    -> ('brpucrs-my.sharepoint.com', '/personal/10070245_pucrs_br/Documents/.../metodosformais')
    """
    p = urllib.parse.urlparse(url)
    if "_layouts" not in p.path:
        return None
    q = dict(urllib.parse.parse_qsl(p.query))
    item_id = q.get("id")
    if not item_id:
        return None
    return p.netloc, urllib.parse.unquote(item_id)


def _resolve_by_path(token: str, host: str, server_rel: str) -> dict:
    """Resolve um item pelo caminho server-relative (/personal/<user>/Documents/<...>)."""
    parts = server_rel.strip("/").split("/")
    # personal site = /personal/<user>; biblioteca padrão (drive) = "Documents"
    if len(parts) < 2 or parts[0] != "personal":
        raise RuntimeError(f"Caminho não reconhecido como OneDrive pessoal: {server_rel}")
    user = parts[1]
    site = _graph(token, f"/sites/{host}:/personal/{user}")
    drive = _graph(token, f"/sites/{site['id']}/drive")
    drive_id = drive["id"]
    # drive root == ".../Documents"; o resto após "Documents" é o caminho relativo
    rest = parts[3:] if len(parts) > 3 and parts[2].lower() == "documents" else parts[2:]
    rel = "/".join(rest)
    if not rel:
        return _graph(token, f"/drives/{drive_id}/root")
    enc = urllib.parse.quote(rel)
    return _graph(token, f"/drives/{drive_id}/root:/{enc}")


def _device_login() -> str:
    r = requests.post(f"{_AUTHORITY}/devicecode",
                      data={"client_id": _CLIENT_ID, "scope": _SCOPE}, timeout=30)
    r.raise_for_status()
    d = r.json()
    print("\n=== LOGIN M365 ===")
    print(f"1) Abra: {d['verification_uri']}")
    print(f"2) Código: {d['user_code']}")
    print("3) Autentique com a conta PUCRS. Aguardando...\n")
    interval = int(d.get("interval", 5))
    deadline = time.time() + int(d.get("expires_in", 900))
    while time.time() < deadline:
        time.sleep(interval)
        t = requests.post(f"{_AUTHORITY}/token", data={
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "client_id": _CLIENT_ID, "device_code": d["device_code"]}, timeout=30)
        j = t.json()
        if "access_token" in j:
            print("OK. Autenticado.")
            return j["access_token"]
        err = j.get("error")
        if err == "authorization_pending":
            continue
        if err == "slow_down":
            interval += 5
            continue
        raise RuntimeError(f"Falha no device-code: {err} — {j.get('error_description', '')[:200]}")
    raise RuntimeError("Tempo de login esgotado.")


def _graph(token: str, path: str) -> dict:
    r = requests.get(f"{_GRAPH}{path}", headers={"Authorization": f"Bearer {token}"}, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"Graph {r.status_code} em {path}: {r.text[:300]}")
    return r.json()


def _download(token: str, item: dict) -> bytes:
    dl = item.get("@microsoft.graph.downloadUrl")
    if dl:
        return requests.get(dl, timeout=120).content       # downloadUrl é pré-assinada
    r = requests.get(f"{_GRAPH}/drives/{item['parentReference']['driveId']}/items/{item['id']}/content",
                     headers={"Authorization": f"Bearer {token}"}, timeout=120)
    r.raise_for_status()
    return r.content


def main(argv: list) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if not argv:
        print('Uso: python -m scripts.m365_probe "<link>"  |  python -m scripts.m365_probe --shared')
        return 2

    if argv[0] == "--insights":
        token = _device_login()
        flt = argv[1] if len(argv) > 1 else None   # ex.: metodosformais (filtra por path)

        def dump(endpoint, label):
            sep = "&" if "?" in endpoint else "?"
            items = _graph(token, f"{endpoint}{sep}$top=200").get("value", [])
            pdf_sample = None
            shown = 0
            print(f"\n=== {label}: {len(items)} item(ns) ===")
            for it in items:
                rv = it.get("resourceVisualization", {})
                rr = it.get("resourceReference", {})
                title, typ, web = rv.get("title", "?"), rv.get("type", "?"), rr.get("webUrl", "")
                if flt and flt.lower() not in web.lower():
                    continue
                shown += 1
                print(f"  [{typ:<10}] {title}")
                print(f"        {web[:120]}")
                if pdf_sample is None and typ == "Pdf":
                    pdf_sample = it
            if flt:
                print(f"  ({shown} batem o filtro '{flt}')")
            return pdf_sample

        s1 = dump("/me/insights/shared", "insights/shared")
        s2 = dump("/me/insights/used", "insights/used (recentes)")
        tgt = s1 or s2
        if tgt:
            iid = urllib.parse.quote(tgt["id"], safe="")
            try:
                res = _graph(token, f"/me/insights/shared/{iid}/resource"
                             if s1 else f"/me/insights/used/{iid}/resource")
                print(f"\n  resolvido PDF '{res.get('name')}' -> size={res.get('size')}")
                if "file" in res:
                    data = _download(token, res)
                    print(f"  baixado: {len(data)} bytes | PDF={data[:4] == b'%PDF'}")
                # TESTE: a partir do item resolvido, dá pra listar a pasta-pai? (enum completa)
                pref = res.get("parentReference", {})
                did, pid = pref.get("driveId"), pref.get("id")
                if did and pid:
                    try:
                        kids = _graph(token, f"/drives/{did}/items/{pid}/children").get("value", [])
                        print(f"  PASTA-PAI lista {len(kids)} filho(s) (enum completa POSSÍVEL):")
                        for k in kids[:50]:
                            print(f"     [{'DIR ' if 'folder' in k else 'file'}] {k.get('name')}")
                    except RuntimeError as e:
                        print(f"  pasta-pai NÃO lista: {str(e)[:90]} (enum completa via Graph bloqueada)")
            except RuntimeError as e:
                print(f"\n  não resolveu /resource: {str(e)[:120]}")
        return 0

    if argv[0] == "--shared":
        token = _device_login()
        items = _graph(token, "/me/drive/sharedWithMe").get("value", [])
        print(f"\n=== Compartilhado comigo: {len(items)} item(ns) ===")
        for it in items:
            ri = it.get("remoteItem", {})
            kind = "DIR " if "folder" in ri else "file"
            pref = ri.get("parentReference", {})
            did, iid, pid = pref.get("driveId"), ri.get("id"), pref.get("id")
            print(f"  [{kind}] {it.get('name')}")
            print(f"        driveId={did}")
            print(f"        itemId ={iid}  parentId={pid}")
            # Se for pasta: lista o próprio. Se arquivo: tenta listar a pasta-pai.
            target = iid if "folder" in ri else pid
            if did and target:
                try:
                    kids = _graph(token, f"/drives/{did}/items/{target}/children").get("value", [])
                    print(f"        -> pai/pasta lista {len(kids)} filho(s):")
                    for k in kids[:40]:
                        print(f"           [{'DIR ' if 'folder' in k else 'file'}] {k.get('name')}")
                except RuntimeError as e:
                    print(f"        -> não dá pra listar pai: {str(e)[:80]}")
        return 0

    share_url = argv[0]
    token = _device_login()

    viewer = _parse_viewer(share_url)
    if viewer:
        host, server_rel = viewer
        print(f"\nURL de visualizador -> resolvendo por caminho: {server_rel}")
        meta = _resolve_by_path(token, host, server_rel)
        drive_id = meta["parentReference"]["driveId"] if "parentReference" in meta else None
        children_path = f"/drives/{drive_id}/items/{meta['id']}/children" if drive_id \
            else f"/drives/{meta['id']}/root/children"
    else:
        sid = _encode_share_url(share_url)
        meta = _graph(token, f"/shares/{sid}/driveItem")
        children_path = f"/shares/{sid}/driveItem/children"

    name = meta.get("name")
    is_folder = "folder" in meta
    print(f"Resolvido: {name}  ({'pasta' if is_folder else 'arquivo'})")

    if not is_folder:
        data = _download(token, meta)
        print(f"  baixado: {len(data)} bytes | PDF={data[:4] == b'%PDF'} | {meta.get('file', {}).get('mimeType')}")
        return 0

    drive_id = meta.get("parentReference", {}).get("driveId")
    if not drive_id:
        # fallback: 1 nível só, pelo endpoint que resolveu
        children = _graph(token, children_path).get("value", [])
        for c in children[:40]:
            print(f"    [{'DIR ' if 'folder' in c else 'file'}] {c.get('name')}")
        return 0

    counts = {"files": 0, "dirs": 0}
    sample = {"item": None}

    def walk(item_id, prefix, depth):
        for c in _graph(token, f"/drives/{drive_id}/items/{item_id}/children").get("value", []):
            if "folder" in c:
                counts["dirs"] += 1
                print(f"{prefix}[DIR ] {c.get('name')}  ({c.get('folder', {}).get('childCount', '?')})")
                if depth > 0:
                    walk(c["id"], prefix + "   ", depth - 1)
            else:
                counts["files"] += 1
                print(f"{prefix}file  {c.get('name')}  ({c.get('size', 0)} b)")
                if sample["item"] is None and c.get("name", "").lower().endswith(".pdf"):
                    sample["item"] = c

    print("  árvore (até 3 níveis):")
    walk(meta["id"], "    ", 3)
    print(f"\n  TOTAL: {counts['files']} arquivo(s), {counts['dirs']} subpasta(s)")
    if sample["item"]:
        data = _download(token, sample["item"])
        print(f"  amostra '{sample['item']['name']}': {len(data)} bytes | PDF={data[:4] == b'%PDF'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
