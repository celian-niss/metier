"""Normalisation des annonces issues des différents collecteurs."""
from __future__ import annotations
import hashlib
import re
import unicodedata
from datetime import datetime, timezone
from urllib.parse import urlparse

from multisource_config import COMPETENCES


def texte_simple(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def cle_texte(value):
    s = unicodedata.normalize("NFKD", texte_simple(value)).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def detecter_competences(texte):
    t = cle_texte(texte)
    trouvees = []
    for nom, variantes in COMPETENCES.items():
        if any(cle_texte(v) in t for v in variantes):
            trouvees.append(nom)
    return trouvees


def id_interne(source, id_source):
    return hashlib.sha1(f"{source}:{id_source}".encode()).hexdigest()[:16]


def normaliser_contrat(value):
    t = cle_texte(value)
    if "altern" in t or "apprent" in t:
        return "Alternance"
    if "stage" in t or "intern" in t:
        return "Stage"
    if "cdi" in t or "permanent" in t:
        return "CDI"
    if "cdd" in t or "fixed term" in t:
        return "CDD"
    if "freelance" in t or "independant" in t or "independent" in t:
        return "Freelance"
    return texte_simple(value) or "Non précisé"


def normaliser_france_travail(enveloppe):
    o = enveloppe["payload"]
    lieu = o.get("lieuTravail") or {}
    entreprise = o.get("entreprise") or {}
    salaire = o.get("salaire") or {}
    origine = o.get("origineOffre") or {}
    description = texte_simple(o.get("description"))
    titre = texte_simple(o.get("intitule"))
    contrat = normaliser_contrat(o.get("typeContratLibelle") or o.get("natureContrat"))
    salaire_txt = texte_simple(salaire.get("libelle"))
    url = texte_simple(origine.get("urlOrigine") or o.get("contact", {}).get("urlPostulation"))
    lat = lieu.get("latitude")
    lon = lieu.get("longitude")
    return {
        "id": id_interne("france_travail", o.get("id")),
        "source": "france_travail",
        "source_label": "France Travail",
        "id_source": str(o.get("id") or ""),
        "requete": enveloppe.get("source_query"),
        "titre": titre,
        "entreprise": texte_simple(entreprise.get("nom")) or "Entreprise non précisée",
        "description": description,
        "ville": texte_simple(lieu.get("libelle")),
        "code_postal": texte_simple(lieu.get("commune")),
        "latitude": lat,
        "longitude": lon,
        "contrat": contrat,
        "experience": texte_simple(o.get("experienceLibelle")),
        "teletravail": "télétravail" in cle_texte(description) or "teletravail" in cle_texte(description),
        "salaire_texte": salaire_txt,
        "salaire_min": None,
        "salaire_max": None,
        "date_publication": (o.get("dateCreation") or "")[:10],
        "date_actualisation": (o.get("dateActualisation") or "")[:10],
        "url": url,
        "competences": detecter_competences(f"{titre} {description}"),
        "rome": texte_simple(o.get("romeCode")),
    }


def normaliser_adzuna(enveloppe):
    o = enveloppe["payload"]
    loc = o.get("location") or {}
    company = o.get("company") or {}
    category = o.get("category") or {}
    description = texte_simple(o.get("description"))
    titre = texte_simple(o.get("title"))
    contrat = normaliser_contrat(o.get("contract_type") or o.get("contract_time"))
    created = texte_simple(o.get("created"))
    return {
        "id": id_interne("adzuna", o.get("id")),
        "source": "adzuna",
        "source_label": "Adzuna",
        "id_source": str(o.get("id") or ""),
        "requete": enveloppe.get("source_query"),
        "titre": titre,
        "entreprise": texte_simple(company.get("display_name")) or "Entreprise non précisée",
        "description": description,
        "ville": texte_simple(loc.get("display_name")),
        "code_postal": "",
        "latitude": o.get("latitude"),
        "longitude": o.get("longitude"),
        "contrat": contrat,
        "experience": "",
        "teletravail": any(x in cle_texte(f"{titre} {description}") for x in ["teletravail", "remote", "hybride"]),
        "salaire_texte": "",
        "salaire_min": o.get("salary_min"),
        "salaire_max": o.get("salary_max"),
        "date_publication": created[:10],
        "date_actualisation": created[:10],
        "url": texte_simple(o.get("redirect_url")),
        "competences": detecter_competences(f"{titre} {description}"),
        "rome": "",
        "categorie_source": texte_simple(category.get("label")),
    }


def normaliser(source, enveloppe):
    if source == "france_travail":
        return normaliser_france_travail(enveloppe)
    if source == "adzuna":
        return normaliser_adzuna(enveloppe)
    raise ValueError(f"Source inconnue: {source}")


def date_collecte():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
