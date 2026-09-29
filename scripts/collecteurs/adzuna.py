"""Collecteur Adzuna via l'API officielle."""
import os
import time
import requests

BASE = "https://api.adzuna.com/v1/api/jobs/fr/search"


def disponible():
    return bool(os.getenv("ADZUNA_APP_ID") and os.getenv("ADZUNA_APP_KEY"))


def rechercher(mots_cles, pages=5, par_page=50):
    app_id = os.environ["ADZUNA_APP_ID"]
    app_key = os.environ["ADZUNA_APP_KEY"]
    offres = []
    for page in range(1, pages + 1):
        r = requests.get(
            f"{BASE}/{page}",
            params={
                "app_id": app_id,
                "app_key": app_key,
                "results_per_page": par_page,
                "what": mots_cles,
                "max_days_old": 30,
                "content-type": "application/json",
            },
            headers={"Accept": "application/json"},
            timeout=30,
        )
        r.raise_for_status()
        lot = r.json().get("results", [])
        offres.extend(lot)
        if len(lot) < par_page:
            break
        time.sleep(0.25)
    return offres


def collecter(requetes):
    pages = max(1, min(int(os.getenv("ADZUNA_PAGES", "5")), 20))
    uniques = {}
    for q in requetes:
        for offre in rechercher(q, pages=pages):
            oid = str(offre.get("id", ""))
            if not oid:
                continue
            enveloppe = {"source_query": q, "payload": offre}
            uniques.setdefault(oid, enveloppe)
        time.sleep(0.35)
    return list(uniques.values())
