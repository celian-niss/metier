"""Pipeline de collecte multisource de l'observatoire."""
from __future__ import annotations
import json
import os
import sys
from collections import Counter
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from collecteurs import france_travail, adzuna
from dedoublonner import dedoublonner
from multisource_config import REQUETES
from normaliser import normaliser, date_collecte

RACINE = Path(__file__).resolve().parent.parent
load_dotenv(RACINE / ".env")


def ecrire_jsonl(path, items):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def stats(offres, brutes, sources_actives):
    contrats = Counter(o.get("contrat") or "Non précisé" for o in offres)
    sources = Counter()
    competences = Counter()
    villes = Counter()
    for o in offres:
        for s in o.get("sources", [o.get("source_label")]):
            if s:
                sources[s] += 1
        for c in o.get("competences", []):
            competences[c] += 1
        if o.get("ville"):
            villes[o["ville"]] += 1
    return {
        "offres_uniques": len(offres),
        "offres_avant_dedoublonnage": brutes,
        "doublons_fusionnes": max(0, brutes - len(offres)),
        "sources_actives": sources_actives,
        "par_source": dict(sources.most_common()),
        "contrats": dict(contrats.most_common()),
        "competences": dict(competences.most_common(30)),
        "villes": dict(villes.most_common(30)),
    }


def main():
    aujourd_hui = date.today().isoformat()
    collecte_iso = date_collecte()
    collectees = {}
    erreurs = {}

    sources = [
        ("france_travail", france_travail),
        ("adzuna", adzuna),
    ]
    for nom, module in sources:
        if not module.disponible():
            print(f"{nom}: ignorée (identifiants absents)")
            continue
        try:
            items = module.collecter(REQUETES)
            collectees[nom] = items
            print(f"{nom}: {len(items)} annonces brutes")
        except Exception as exc:
            erreurs[nom] = str(exc)
            print(f"{nom}: ERREUR {exc}", file=sys.stderr)

    if not collectees:
        raise SystemExit("Aucune source disponible. Configure au moins France Travail ou Adzuna.")

    dossier_brut = RACINE / "data" / "multisource" / "brut" / aujourd_hui
    normalisees = []
    for source, items in collectees.items():
        ecrire_jsonl(dossier_brut / f"{source}.jsonl", items)
        for item in items:
            try:
                normalisees.append(normaliser(source, item))
            except Exception as exc:
                print(f"{source}: normalisation ignorée: {exc}", file=sys.stderr)

    uniques = dedoublonner(normalisees)
    uniques.sort(key=lambda o: (o.get("date_publication") or "", o.get("titre") or ""), reverse=True)

    payload = {
        "version": 1,
        "date": aujourd_hui,
        "collecte_utc": collecte_iso,
        "perimetre": "Marketing, communication et digital — France",
        "requetes": REQUETES,
        "stats": stats(uniques, len(normalisees), sorted(collectees)),
        "erreurs": erreurs,
        "offres": uniques,
    }

    sortie = RACINE / "data" / "multisource.json"
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{sortie}: {len(uniques)} offres uniques")


if __name__ == "__main__":
    main()
