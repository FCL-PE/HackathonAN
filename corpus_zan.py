from __future__ import annotations

"""
corpus_zan.py
Base de données structurée de la généalogie législative du ZAN,
construite à partir du corpus fourni par Nicolas Thouvenin (email du jour).

Contrairement à data/base_finale.json (issu du pipeline zan1/zan2.json,
pauvre en dates et sans relations), cette base contient :
- des dates précises
- une catégorisation (fondatrice / préparatoire / sectorielle pour les lois ;
  noyau / connexe pour les décrets)
- les relations explicites entre textes (qui modifie/complète/remplace qui)

Usage :
    python3 corpus_zan.py
    (génère data/genealogie_zan.json)
"""

import json

LOIS = [
    # --- Lois qui constituent directement le régime du ZAN ---
    {"numero": "2021-1104", "titre": "Loi Climat et Résilience", "date": "2021-08-22",
     "categorie": "fondatrice",
     "resume": "Loi fondatrice du ZAN : objectif zéro artificialisation nette en 2050, "
               "réduction de moitié de la consommation d'espaces 2021-2031, définit "
               "artificialisation/renaturation, impose la territorialisation (SRADDET, SCoT, PLU).",
     "relations": []},
    {"numero": "2022-217", "titre": "Loi 3DS", "date": "2022-02-21",
     "categorie": "fondatrice",
     "resume": "Premiers ajustements du calendrier et des modalités de territorialisation.",
     "relations": [{"cible": "2021-1104", "type": "modifie", "detail": "article 194"}]},
    {"numero": "2023-175", "titre": "Loi APER (énergies renouvelables)", "date": "2023-03-10",
     "categorie": "fondatrice",
     "resume": "Articule le ZAN avec le photovoltaïque, l'agrivoltaïsme et les projets solaires "
               "sur espaces agricoles/naturels/forestiers.",
     "relations": [{"cible": "2021-1104", "type": "précise", "detail": None}]},
    {"numero": "2023-630", "titre": "Loi ZAN 2", "date": "2023-07-20",
     "categorie": "fondatrice",
     "resume": "Principale loi corrective : garantie communale d'un hectare, mutualisation, "
               "traitement séparé des grands projets, conférence régionale de gouvernance.",
     "relations": [{"cible": "2021-1104", "type": "corrige", "detail": None}]},
    {"numero": "2025-1129", "titre": "Loi de simplification de l'urbanisme et du logement", "date": "2025-11-26",
     "categorie": "fondatrice",
     "resume": "Modifie à nouveau l'article 194, simplifie l'intégration des objectifs "
               "de sobriété foncière dans les documents d'urbanisme.",
     "relations": [{"cible": "2021-1104", "type": "modifie", "detail": "article 194"}]},

    # --- Lois qui ont préparé le ZAN ---
    {"numero": "2000-1208", "titre": "Loi SRU", "date": "2000-12-13", "categorie": "preparatoire",
     "resume": "Introduit l'objectif d'utilisation économe des espaces, renforce SCoT et PLU.",
     "relations": []},
    {"numero": "2009-967", "titre": "Loi Grenelle I", "date": "2009-08-03", "categorie": "preparatoire",
     "resume": "Affirme la nécessité de lutter contre l'étalement urbain.", "relations": []},
    {"numero": "2010-788", "titre": "Loi Grenelle II", "date": "2010-07-12", "categorie": "preparatoire",
     "resume": "Impose aux SCoT/PLU des objectifs chiffrés de limitation de la consommation d'espace.",
     "relations": []},
    {"numero": "2010-874", "titre": "Loi de modernisation de l'agriculture et de la pêche", "date": "2010-07-27",
     "categorie": "preparatoire",
     "resume": "Crée l'Observatoire national de la consommation des espaces agricoles, "
               "ancêtre des CDPENAF.", "relations": []},
    {"numero": "2014-366", "titre": "Loi ALUR", "date": "2014-03-24", "categorie": "preparatoire",
     "resume": "Renforce la lutte contre l'étalement urbain, lutte contre le pastillage en zones agricoles.",
     "relations": []},
    {"numero": "2014-1170", "titre": "Loi d'avenir pour l'agriculture", "date": "2014-10-13",
     "categorie": "preparatoire",
     "resume": "Crée les CDPENAF (préservation des espaces naturels, agricoles, forestiers).",
     "relations": []},
    {"numero": "2015-991", "titre": "Loi NOTRe", "date": "2015-08-07", "categorie": "preparatoire",
     "resume": "Crée le SRADDET, futur support régional de territorialisation du ZAN.",
     "relations": []},
    {"numero": "2016-1087", "titre": "Loi Biodiversité", "date": "2016-08-08", "categorie": "preparatoire",
     "resume": "Renforce éviter/réduire/compenser, fondement environnemental du ZAN (ne le crée pas).",
     "relations": []},
    {"numero": "2018-1021", "titre": "Loi ELAN", "date": "2018-11-23", "categorie": "preparatoire",
     "resume": "Favorise le renouvellement urbain : friches, projets partenariaux d'aménagement.",
     "relations": []},

    # --- Lois sectorielles qui interagissent avec le ZAN ---
    {"numero": "2023-973", "titre": "Loi Industrie verte", "date": "2023-10-23", "categorie": "sectorielle",
     "resume": "Articule réindustrialisation et sobriété foncière (friches, foncier industriel).",
     "relations": []},
    {"numero": "2025-541", "titre": "Loi transformation des bureaux en logements", "date": "2025-06-16",
     "categorie": "sectorielle",
     "resume": "Facilite le recyclage du bâti existant sans extension urbaine.", "relations": []},
    {"numero": "2026-403", "titre": "Loi de simplification de la vie économique", "date": "2026-05-26",
     "categorie": "sectorielle",
     "resume": "Requalification des zones commerciales sans artificialisation supplémentaire.",
     "relations": [{"cible": "2022-217", "type": "prolonge", "detail": "expérimentations issues de la loi 3DS"}]},
]

DECRETS = [
    {"numero": "2022-762", "titre": "Territorialisation dans les SRADDET", "date": "2022-04-29",
     "categorie": "noyau",
     "resume": "Premier décret de territorialisation : déclinaison territoriale des objectifs.",
     "relations": [{"cible": "2023-1097", "type": "ajusté_par", "detail": None}]},
    {"numero": "2022-763", "titre": "Nomenclature de l'artificialisation des sols", "date": "2022-04-29",
     "categorie": "noyau",
     "resume": "Première nomenclature : surfaces artificialisées vs non artificialisées.",
     "relations": [{"cible": "2023-1096", "type": "remplacé_par", "detail": None}]},
    {"numero": "2023-1096", "titre": "Évaluation et suivi de l'artificialisation des sols", "date": "2023-11-27",
     "categorie": "noyau",
     "resume": "Remplace la nomenclature 2022, crée l'Observatoire national de l'artificialisation, "
               "organise le rapport triennal des communes/EPCI.",
     "relations": [{"cible": "2022-763", "type": "remplace", "detail": None}]},
    {"numero": "2023-1097", "titre": "Territorialisation révisée", "date": "2023-11-27",
     "categorie": "noyau",
     "resume": "Assouplit et complète le décret de 2022 : critères de territorialisation, "
               "communes littorales/montagne, articulation régions/SCoT/bloc communal.",
     "relations": [{"cible": "2022-762", "type": "assouplit_complete", "detail": None},
                   {"cible": "2023-630", "type": "tient_compte_de", "detail": "loi ZAN 2"}]},
    {"numero": "2023-1098", "titre": "Commission régionale de conciliation", "date": "2023-11-27",
     "categorie": "noyau",
     "resume": "Organise la commission saisie en cas de contestation d'un projet d'envergure "
               "nationale/européenne (3 représentants région, 3 État, 1 magistrat président).",
     "relations": []},
    {"numero": "2023-1408", "titre": "Photovoltaïque et calcul de consommation d'espace", "date": "2023-12-29",
     "categorie": "noyau",
     "resume": "Conditions pour qu'une installation photovoltaïque ne soit pas comptée "
               "comme consommation d'ENAF (réversibilité, couvert végétal).",
     "relations": []},
    {"numero": "2022-1309", "titre": "Observatoires de l'habitat et du foncier", "date": "2022-10-12",
     "categorie": "connexe",
     "resume": "Suivi des marchés fonciers, friches, locaux vacants, potentiel de densification.",
     "relations": []},
    {"numero": "2022-1312", "titre": "Autorisation d'exploitation commerciale et artificialisation",
     "date": "2022-10-13", "categorie": "connexe",
     "resume": "Interdiction de principe d'autoriser un projet commercial artificialisant, "
               "conditions de dérogation.", "relations": []},
    {"numero": "2023-1259", "titre": "Définition de la friche", "date": "2023-12-26", "categorie": "connexe",
     "resume": "Critères d'identification d'une friche — levier opérationnel clé du ZAN.",
     "relations": []},
    {"numero": "2024-318", "titre": "Agrivoltaïsme", "date": "2024-04-08", "categorie": "connexe",
     "resume": "Conditions d'implantation d'installations photovoltaïques sur terrains agricoles.",
     "relations": [{"cible": "2023-1408", "type": "à_articuler_avec", "detail": None}]},
    {"numero": "2024-452", "titre": "Certificat de projet dans les friches (expérimental)",
     "date": "2024-05-21", "categorie": "connexe",
     "resume": "Guichet expérimental (juin 2024 - mai 2027) pour connaître en amont régimes "
               "juridiques et délais applicables à un projet en friche.", "relations": []},
]

TEXTES_INFRA = [
    {"type": "arrete", "titre": "Caractéristiques techniques photovoltaïque", "date": "2023-12-29"},
    {"type": "arrete", "titre": "Indemnisation président commission régionale de conciliation",
     "date": "2024-02-13"},
    {"type": "arrete", "titre": "Liste des projets d'envergure nationale/européenne", "date": "2024-05-31"},
    {"type": "arrete", "titre": "Règles agrivoltaïsme complémentaires", "date": "2024-07-05"},
    {"type": "circulaire", "titre": "Accompagnement des préfets pour la mise en œuvre territoriale",
     "date": "2024-01-31"},
]

EN_COURS = [
    {"titre": "Proposition de loi TRACE", "statut": "adoptée par le Sénat, transmise à l'AN",
     "date": "2025-03-18"},
    {"titre": "Proposition de loi transition foncière", "statut": "déposée à l'Assemblée nationale",
     "date": "2025-06-04"},
]


def construit_base() -> dict:
    return {
        "lois": LOIS,
        "decrets": DECRETS,
        "textes_infra": TEXTES_INFRA,
        "en_cours": EN_COURS,
    }


if __name__ == "__main__":
    base = construit_base()
    with open("data/genealogie_zan.json", "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=2)

    print(f"{len(LOIS)} lois, {len(DECRETS)} décrets, {len(TEXTES_INFRA)} textes infra, "
          f"{len(EN_COURS)} en cours -> data/genealogie_zan.json")

    print("\n--- Timeline complète (lois + décrets) ---")
    tous = [{**l, "nature": "loi"} for l in LOIS] + [{**d, "nature": "décret"} for d in DECRETS]
    for t in sorted(tous, key=lambda x: x["date"]):
        print(f"  {t['date']} | {t['nature']:6s} | {t['categorie']:12s} | {t['titre']}")
