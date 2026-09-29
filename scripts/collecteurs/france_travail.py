"""Collecteur officiel France Travail."""
import os
import re
import time
import requests

TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=/partenaire"
SEARCH_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"


def disponible():
    return bool(os.getenv("FT_CLIENT_ID") and os.getenv("FT_CLIENT_SECRET"))


def obtenir_token():
    cid = os.environ["FT_CLIENT_ID"]
    secret = os.environ["FT_CLIENT_SECRET"]
    r = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": cid,
            "client_secret": secret,
            "scope": "api_offresdemploiv2 o2dsoffre",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def rechercher(token, mots_cles, maximum=1150):
    offres, debut, total = [], 0, None
    while debut < maximum:
        fin = min(debut + 149, maximum - 1)
        r = requests.get(
            SEARCH_URL,
            params={"motsCles": mots_cles, "range": f"{debut}-{fin}"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        if r.status_code == 204:
            break
        if r.status_code not in (200, 206):
            raise RuntimeError(f"France Travail {r.status_code}: {r.text[:300]}")
        m = re.search(r"/(\d+)", r.headers.get("Content-Range", ""))
        if m:
            total = int(m.group(1))
        lot = r.json().get("resultats", [])
        offres.extend(lot)
        if len(lot) < 150 or (total is not None and len(offres) >= total):
            break
        debut += 150
        time.sleep(0.25)
    return offres


def collecter(requetes):
    token = obtenir_token()
    uniques = {}
    for q in requetes:
        for offre in rechercher(token, q):
            oid = str(offre.get("id", ""))
            if not oid:
                continue
            enveloppe = {"source_query": q, "payload": offre}
            uniques.setdefault(oid, enveloppe)
        time.sleep(0.35)
    return list(uniques.values())
