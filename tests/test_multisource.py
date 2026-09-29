import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from collecter import maj_historique
from dedoublonner import dedoublonner, meme_offre
from normaliser import detecter_competences, normaliser_contrat, normaliser_salaire_france_travail


def test_competences():
    found = detecter_competences("SEO, Google Analytics GA4, HubSpot et anglais")
    assert "SEO" in found
    assert "GA4" in found
    assert "CRM" in found
    assert "Anglais" in found


def test_contrats():
    assert normaliser_contrat("CDI") == "CDI"
    assert normaliser_contrat("Contrat d'apprentissage") == "Alternance"


def test_salaire_france_travail():
    assert normaliser_salaire_france_travail("Mensuel de 2500 Euros à 3000 Euros") == (30000, 36000)
    assert normaliser_salaire_france_travail("Horaire de 14.0 Euros") == (25480, 25480)
    assert normaliser_salaire_france_travail("Annuel de 35000 Euros à 42000 Euros") == (35000, 42000)


def test_dedoublonnage_cross_source():
    a = {"source":"france_travail","id_source":"1","source_label":"France Travail","titre":"Chef de projet digital","entreprise":"ACME","ville":"Lyon","description":"x","competences":[]}
    b = {"source":"adzuna","id_source":"2","source_label":"Adzuna","titre":"Chef de projet digital H/F","entreprise":"ACME","ville":"Lyon","description":"xx","competences":[]}
    assert meme_offre(a, b)
    out = dedoublonner([a, b])
    assert len(out) == 1
    assert set(out[0]["sources"]) == {"France Travail", "Adzuna"}


def test_historique_remplace_meme_jour(tmp_path):
    p = tmp_path / "historique.json"
    p.write_text(json.dumps([{"date":"2026-09-28","offres_uniques":10},{"date":"2026-09-29","offres_uniques":20}]), encoding="utf-8")
    out = maj_historique(p, {"date":"2026-09-29","offres_uniques":25})
    assert len(out) == 2
    assert out[-1]["offres_uniques"] == 25
