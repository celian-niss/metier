"""Normalisation des annonces issues des différents collecteurs."""
from __future__ import annotations
import hashlib
import re
import unicodedata
from datetime import datetime, timezone

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


def _nombre(token):
    token = token.replace("\u202f", "").replace(" ", "").replace(",", ".")
    try:
        return float(token)
    except ValueError:
        return None


def normaliser_salaire_france_travail(libelle):
    """Convertit le libellé France Travail en fourchette annuelle brute approximative."""
    txt = texte_simple(libelle)
    if not txt:
        return None, None
    nums = [_nombre(x) for x in re.findall(r"\d[\d\s\u202f]*(?:[,.]\d+)?", txt)]
    nums = [x for x in nums if x is not None]
    if not nums:
        return None, None

    # Écarte les nombres descriptifs fréquents qui ne sont pas un salaire.
    values = [x for x in nums if x >= 8]
    if not values:
        return None, None
    lo = values[0]
    hi = values[1] if len(values) > 1 else lo
    if hi < lo:
        lo, hi = hi, lo

    t = cle_texte(txt)
    if "horaire" in t or "heure" in t:
        factor = 35 * 52
    elif "mensuel" in t or "mois" in t:
        factor = 12
    elif "annuel" in t or "an" in t:
        factor = 1
    else:
        # Heuristique : les montants < 100 sont généralement horaires,
        # ceux < 10 000 sont généralement mensuels.
        factor = 35 * 52 if hi < 100 else (12 if hi < 10000 else 1)

    return round(lo * factor), round(hi * factor)


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
    salaire_min, salaire_max = normaliser_salaire_france_travail(salaire_txt)
    url = texte_simple(origine.get("urlOrigine") or (o.get("contact") or {}).get("urlPostulation"))
    exp = texte_simple(o.get("experienceLibelle"))
    debutant = "debutant accepte" in cle_texte(exp) or contrat == "Alternance"
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
        "latitude": lieu.get("latitude"),
        "longitude": lieu.get("longitude"),
        "contrat": contrat,
        "experience": exp,
        "debutant": debutant,
        "teletravail": "teletravail" in cle_texte(f"{titre} {description}"),
        "salaire_texte": salaire_txt,
        "salaire_min": salaire_min,
        "salaire_max": salaire_max,
        "date_publication": (o.get("dateCreation") or "")[:10],
        "date_actualisation": (o.get("dateActualisation") or "")[:10],
        "url": url,
        "competences": detecter_competences(f"{titre} {description}"),
        "rome": texte_simple(o.get("romeCode")),
        "secteur": texte_simple(o.get("secteurActiviteLibelle")),
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
    sal_min = o.get("salary_min")
    sal_max = o.get("salary_max")
    try:
        sal_min = round(float(sal_min)) if sal_min is not None else None
    except (TypeError, ValueError):
        sal_min = None
    try:
        sal_max = round(float(sal_max)) if sal_max is not None else sal_min
    except (TypeError, ValueError):
        sal_max = sal_min
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
        "debutant": contrat in {"Alternance", "Stage"},
        "teletravail": any(x in cle_texte(f"{titre} {description}") for x in ["teletravail", "remote", "hybride"]),
        "salaire_texte": "",
        "salaire_min": sal_min,
        "salaire_max": sal_max,
        "date_publication": created[:10],
        "date_actualisation": created[:10],
        "url": texte_simple(o.get("redirect_url")),
        "competences": detecter_competences(f"{titre} {description}"),
        "rome": "",
        "secteur": texte_simple(category.get("label")),
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
