"""
ingestion.py
Ingère les fichiers JSON de sources juridiques (type zan1.json / zan2.json),
nettoie, déduplique, classe par force juridique, trie chronologiquement.

Usage:
    python3 ingestion.py data/zan1.json data/zan2.json
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field, asdict
from datetime import date


# Classification de la force juridique par type de source.
# Ordre = du plus contraignant au moins contraignant.
FORCE_JURIDIQUE = {
    "codes": {"niveau": 1, "label": "Loi / règlement en vigueur", "contraignant": True},
    "loda": {"niveau": 1, "label": "Décret / arrêté (JORF)", "contraignant": True},
    "eurlex": {"niveau": 2, "label": "Droit européen", "contraignant": True},
    "jurisprudence": {"niveau": 3, "label": "Décision de justice (fait jurisprudence)", "contraignant": False},
    "arianeweb": {"niveau": 3, "label": "Décision de justice administrative", "contraignant": False},
    "judilibre": {"niveau": 3, "label": "Décision de la Cour de cassation", "contraignant": False},
    "bofip": {"niveau": 4, "label": "Doctrine fiscale administrative", "contraignant": False},
    "cnil": {"niveau": 4, "label": "Délibération CNIL (avis)", "contraignant": False},
}

# Mots-clés qui signent une source vraiment liée à l'urbanisme / ZAN.
# Sert à séparer le signal du bruit dans les gros fichiers non curés.
MOTS_CLES_ZAN = [
    "urbanisme", "urbain", "commune", "collectivités", "rénovation urbaine",
    "revitalisation rurale", "zone", "sol", "artificialisation",
]


@dataclass
class Source:
    source: str
    id_reference: str
    titre: str
    type: str
    url: str
    date: str | None = None
    juridiction: str | None = None
    force_juridique: dict = field(default_factory=dict)
    pertinent_zan: bool = True
    raison_exclusion: str | None = None


def charger_fichier(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("sources", [])


def deduplique(sources_brutes: list[dict]) -> list[dict]:
    """Déduplique sur (source, id_reference, url) — plusieurs fichiers peuvent se recouper."""
    vus = set()
    uniques = []
    for s in sources_brutes:
        cle = (s.get("source"), s.get("id_reference"), s.get("url"))
        if cle not in vus:
            vus.add(cle)
            uniques.append(s)
    return uniques


def evalue_pertinence(s: dict) -> tuple[bool, str | None]:
    """
    Heuristique simple pour flaguer le bruit hors-sujet (ex: code du vin,
    charcuterie, CNIL 1994 sur un panel INSEE...) repéré dans zan1.json.
    Un vrai filtrage se ferait via le LLM ou une recherche mieux ciblée,
    ceci est un premier filtre rapide et transparent.
    """
    texte = f"{s.get('titre', '')} {s.get('source', '')}".lower()

    # Sources de type "codes" dont le titre ne mentionne aucun terme urbanisme/foncier
    # sont suspectes (ex: Code général des impôts sur la taxe foncière peut être
    # légitime, mais Code du vin / charcuterie ne le sont clairement pas)
    hors_sujet_evident = ["code du vin", "charcuterie", "panel européen", "mutualité"]
    for terme in hors_sujet_evident:
        if terme in texte:
            return False, f"terme hors-sujet détecté : '{terme}'"

    # Codes structurellement toujours pertinents pour l'urbanisme/ZAN,
    # même sans mot-clé explicite dans le titre générique du code
    codes_pertinents = [
        "code de l'urbanisme", "code des communes",
        "code général des collectivités territoriales",
        "code rural et de la pêche maritime",  # zones agricoles/naturelles = coeur du ZAN
    ]
    if any(s.get("titre", "").lower().startswith(c) for c in codes_pertinents):
        return True, None

    # Codes structurellement hors-sujet pour le ZAN : fiscalité générale, santé,
    # commerce, civil... sauf si un mot-clé ZAN apparaît (déjà testé au-dessus)
    codes_hors_sujet = [
        "code général des impôts", "code civil", "code de commerce",
        "code de la santé publique", "code de la mutualité",
    ]
    if any(c in texte for c in codes_hors_sujet):
        return False, "code générique sans lien direct avec l'urbanisme/ZAN"

    # Jurisprudence / arianeweb / judilibre : le titre seul (numéro de dossier,
    # juridiction) ne permet jamais de juger du fond -> à vérifier avec le texte
    if s.get("type") in ("jurisprudence", "arianeweb", "judilibre"):
        return True, "à vérifier : titre non explicite (numéro de dossier), fond à confirmer avec le texte complet"

    # Droit européen (eurlex) : souvent des textes-cadres généraux, pertinence
    # au cas par cas -> à vérifier plutôt qu'à inclure ou exclure d'office
    if s.get("source") == "eurlex":
        return True, "à vérifier : texte UE générique, lien avec le ZAN à confirmer"

    # BOFiP / CNIL hors mots-clés déjà testés : doctrine technique, à vérifier
    if s.get("source") in ("bofip", "cnil"):
        return True, "à vérifier : doctrine administrative, lien avec le ZAN à confirmer"

    return True, "pertinence non confirmée automatiquement"


def enrichit(sources: list[dict]) -> list[Source]:
    enrichies = []
    for s in sources:
        pertinent, raison = evalue_pertinence(s)
        force = FORCE_JURIDIQUE.get(s.get("source", ""), {
            "niveau": 5, "label": "Non classé", "contraignant": None
        })
        enrichies.append(Source(
            source=s.get("source", ""),
            id_reference=s.get("id_reference", ""),
            titre=s.get("titre") or f"({s.get('source')} — titre non fourni)",
            type=s.get("type", ""),
            url=s.get("url", ""),
            date=s.get("date"),
            juridiction=s.get("juridiction"),
            force_juridique=force,
            pertinent_zan=pertinent,
            raison_exclusion=raison,
        ))
    return enrichies


def trie_chronologique(sources: list[Source]) -> list[Source]:
    """Trie par date croissante ; les sources sans date (codes en vigueur) vont en tête."""
    return sorted(sources, key=lambda s: s.date or "0000-00-00")


def rapport(sources: list[Source]) -> None:
    total = len(sources)
    pertinentes = [s for s in sources if s.pertinent_zan and not s.raison_exclusion]
    a_verifier = [s for s in sources if s.pertinent_zan and s.raison_exclusion]
    exclues = [s for s in sources if not s.pertinent_zan]

    print(f"=== Rapport d'ingestion ===")
    print(f"Total sources uniques      : {total}")
    print(f"Clairement pertinentes ZAN : {len(pertinentes)}")
    print(f"À vérifier manuellement    : {len(a_verifier)}")
    print(f"Exclues (hors-sujet)       : {len(exclues)}")
    print()

    if exclues:
        print("--- Exclues (bruit détecté) ---")
        for s in exclues:
            print(f"  - {s.titre[:70]} [{s.raison_exclusion}]")
        print()

    print("--- Timeline des sources pertinentes ---")
    for s in trie_chronologique(pertinentes + a_verifier):
        date_aff = s.date or "en vigueur"
        badge = "⚠️ contraignant" if s.force_juridique.get("contraignant") else "interprétation/doctrine"
        print(f"  {date_aff} | {s.force_juridique['label']:40s} | {s.titre[:60]}")


def sauvegarde(sources: list[Source], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump([asdict(s) for s in sources], f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 ingestion.py fichier1.json [fichier2.json ...]")
        sys.exit(1)

    toutes_sources_brutes = []
    for path in sys.argv[1:]:
        toutes_sources_brutes += charger_fichier(path)

    uniques = deduplique(toutes_sources_brutes)
    enrichies = enrichit(uniques)

    rapport(enrichies)

    sauvegarde(enrichies, "data/sources_ingerees.json")
    print(f"\n{len(enrichies)} sources sauvegardées dans data/sources_ingerees.json")
