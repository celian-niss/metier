import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from resumer import REGEX_OUTILS, qualite_donnees, salaire_min_max


def test_salaires_france_travail():
    assert salaire_min_max("Annuel de 32000.0 Euros à 38000.0 Euros") == (32000, 38000)
    assert salaire_min_max("Mensuel de 2500.0 Euros à 3000.0 Euros") == (30000, 36000)
    assert salaire_min_max("Horaire de 14.0 Euros") == (22498, 22498)


def test_ia_generative_ne_detecte_pas_le_mot_ia_isole():
    rx = REGEX_OUTILS["IA générative"]
    assert rx.search("Maîtrise de ChatGPT et de l'intelligence artificielle")
    assert not rx.search("Le poste est basé à Paris et rattaché au service média")


def test_qualite_donnees():
    offres = [
        {
            "intitule": "Chargé marketing digital", "entreprise": "ACME", "dep": "63",
            "smin": 30000, "lat": 45.7, "formation": "Bac+5",
            "competences": ["SEO"], "teletravail": True, "date": "2026-09-28", "vu_le": "2026-09-29"
        },
        {
            "intitule": "Chargé marketing digital", "entreprise": "ACME", "dep": "63",
            "smin": None, "lat": None, "formation": None,
            "competences": [], "teletravail": False, "date": "2026-08-01", "vu_le": "2026-09-29"
        },
    ]
    q = qualite_donnees(offres)
    assert q["salaire_pct"] == 50
    assert q["position_pct"] == 50
    assert q["formation_pct"] == 50
    assert q["competences_pct"] == 50
    assert q["entreprise_pct"] == 100
    assert q["fraiches_7j_pct"] == 50
    assert q["doublons_probables"] == 1
