from __future__ import annotations

"""
requetes.py
Fonctions pour interroger data/sources_filtrees.json (ou sources_ingerees.json
si le filtre LLM n'a pas encore tourné).

Usage :
    from requetes import charge, timeline, par_force_juridique, par_type, stats
    sources = charge()
    for s in timeline(sources):
        print(s["date"], s["titre"])
"""

import json
import os


def charge(path: str | None = None) -> list[dict]:
    """Charge la base la plus à jour disponible."""
    if path is None:
        path = "data/sources_filtrees.json" if os.path.exists("data/sources_filtrees.json") \
            else "data/sources_ingerees.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def pertinentes(sources: list[dict]) -> list[dict]:
    """Ne garde que les sources jugées pertinentes (après filtre heuristique + LLM)."""
    return [s for s in sources if s.get("pertinent_zan")]


def timeline(sources: list[dict], seulement_pertinentes: bool = True) -> list[dict]:
    """Trie chronologiquement. Les sources sans date (codes en vigueur) en tête."""
    base = pertinentes(sources) if seulement_pertinentes else sources
    return sorted(base, key=lambda s: s.get("date") or "0000-00-00")


def par_type(sources: list[dict], type_source: str) -> list[dict]:
    """Filtre par type : 'codes', 'jurisprudence', 'loda', 'eurlex', 'bofip', 'cnil'..."""
    return [s for s in sources if s.get("source") == type_source]


def par_force_juridique(sources: list[dict], contraignant: bool) -> list[dict]:
    """True = lois/décrets opposables. False = jurisprudence/doctrine/avis."""
    return [s for s in sources if s.get("force_juridique", {}).get("contraignant") == contraignant]


def par_niveau_confiance(sources: list[dict], niveau: str) -> list[dict]:
    """Filtre sur la confiance du LLM ('haute', 'moyenne', 'faible') — n'existe
    que sur les sources passées par filtre_llm.py (champ avis_llm)."""
    return [s for s in sources if s.get("avis_llm", {}).get("confiance") == niveau]


def stats(sources: list[dict]) -> dict:
    pert = pertinentes(sources)
    return {
        "total_sources": len(sources),
        "pertinentes": len(pert),
        "exclues": len(sources) - len(pert),
        "contraignantes": len(par_force_juridique(pert, True)),
        "interpretation_doctrine": len(par_force_juridique(pert, False)),
        "par_type": {
            t: len(par_type(pert, t))
            for t in sorted(set(s.get("source") for s in pert))
        },
    }


if __name__ == "__main__":
    sources = charge()
    print("=== Statistiques de la base ===")
    print(json.dumps(stats(sources), indent=2, ensure_ascii=False))

    print("\n=== Timeline (5 premières) ===")
    for s in timeline(sources)[:5]:
        date_aff = s.get("date") or "en vigueur"
        print(f"  {date_aff} | {s['titre'][:60]}")
