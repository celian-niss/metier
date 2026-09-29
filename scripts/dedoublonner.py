"""Déduplication des annonces normalisées, y compris entre sources."""
from difflib import SequenceMatcher
from normaliser import cle_texte


def _signature(o):
    titre = cle_texte(o.get("titre"))
    entreprise = cle_texte(o.get("entreprise"))
    ville = cle_texte(o.get("ville"))
    return titre, entreprise, ville


def _sim(a, b):
    return SequenceMatcher(None, a, b).ratio() if a and b else 0.0


def meme_offre(a, b):
    if a.get("source") == b.get("source") and a.get("id_source") == b.get("id_source"):
        return True
    ta, ea, va = _signature(a)
    tb, eb, vb = _signature(b)
    if ea and eb and ea == eb and va and vb and va == vb and _sim(ta, tb) >= 0.84:
        return True
    if ea and eb and ea == eb and _sim(ta, tb) >= 0.92:
        return True
    return False


def dedoublonner(offres):
    groupes = []
    for offre in offres:
        groupe = next((g for g in groupes if meme_offre(g[0], offre)), None)
        if groupe is None:
            groupes.append([offre])
        else:
            groupe.append(offre)

    uniques = []
    for groupe in groupes:
        primaire = max(
            groupe,
            key=lambda x: (
                bool(x.get("description")),
                bool(x.get("salaire_min") or x.get("salaire_texte")),
                len(x.get("competences") or []),
            ),
        ).copy()
        primaire["sources"] = sorted({x["source_label"] for x in groupe})
        primaire["source_ids"] = [
            {"source": x["source"], "id_source": x["id_source"], "url": x.get("url", "")}
            for x in groupe
        ]
        primaire["doublons_fusionnes"] = len(groupe) - 1
        uniques.append(primaire)
    return uniques
