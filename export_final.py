from __future__ import annotations

"""
export_final.py
Génère la base finale, allégée, prête à être consommée par le frontend
ou toute autre feature (timeline, liste filtrable, etc).

Usage :
    python3 export_final.py
    (lit data/sources_filtrees.json, écrit data/base_finale.json)
"""

import json
from requetes import charge, pertinentes, timeline


def allege(source: dict) -> dict:
    """Ne garde que les champs utiles à l'affichage, retire le bruit de debug."""
    return {
        "id": source.get("id_reference") or source.get("url", "").split("/")[-1],
        "titre": source["titre"],
        "type": source["source"],
        "url": source["url"],
        "date": source.get("date"),
        "juridiction": source.get("juridiction"),
        "force_juridique": source["force_juridique"]["label"],
        "contraignant": source["force_juridique"]["contraignant"],
        # texte_complet et resume_llm seront ajoutés ici une fois le texte
        # récupéré via le MCP Légifrance -> voir README, étape suivante
        "texte_complet": None,
        "resume_llm": None,
    }


def main():
    sources = charge()
    pert = timeline(sources)  # déjà triées chronologiquement, déjà filtrées

    base_finale = [allege(s) for s in pert]

    with open("data/base_finale.json", "w", encoding="utf-8") as f:
        json.dump(base_finale, f, ensure_ascii=False, indent=2)

    print(f"{len(base_finale)} sources exportées dans data/base_finale.json")
    print("\nAperçu :")
    for s in base_finale:
        print(f"  [{s['type']:12s}] {s['date'] or 'en vigueur':12s} | {s['titre'][:50]}")


if __name__ == "__main__":
    main()
