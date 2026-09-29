import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from dedoublonner import dedoublonner, meme_offre
from normaliser import detecter_competences, normaliser_contrat


def test_competences():
    found = detecter_competences("SEO, Google Analytics GA4, HubSpot et anglais")
    assert "SEO" in found
    assert "GA4" in found
    assert "CRM" in found
    assert "Anglais" in found


def test_contrats():
    assert normaliser_contrat("CDI") == "CDI"
    assert normaliser_contrat("Contrat d'apprentissage") == "Alternance"


def test_dedoublonnage_cross_source():
    a = {"source":"france_travail","id_source":"1","source_label":"France Travail","titre":"Chef de projet digital","entreprise":"ACME","ville":"Lyon","description":"x","competences":[]}
    b = {"source":"adzuna","id_source":"2","source_label":"Adzuna","titre":"Chef de projet digital H/F","entreprise":"ACME","ville":"Lyon","description":"xx","competences":[]}
    assert meme_offre(a, b)
    out = dedoublonner([a, b])
    assert len(out) == 1
    assert set(out[0]["sources"]) == {"France Travail", "Adzuna"}
