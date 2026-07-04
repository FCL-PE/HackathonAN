"""
openfisca_client.py
Appelle l'API publique OpenFisca-France pour calculer un impact fiscal RÉEL
(pas une estimation générée par le LLM -> fiabilité garantie pour la démo).

Doc API : https://openfisca.org/doc/openfisca-web-api/
Instance publique FR : https://api.fr.openfisca.org

⚠️ Pas testable depuis ce sandbox (domaine non accessible ici).
   À tester sur ton laptop avec ta connexion normale :
       python3 openfisca_client.py
"""

import requests

API_BASE = "https://api.fr.openfisca.org"


def calculer_impot_revenu(salaire_annuel: int, annee_naissance: int, period: str = "2026") -> dict:
    """
    Exemple minimal : calcule le revenu disponible / impôt sur le revenu
    pour une personne seule, sur la base de son salaire annuel.

    C'est un point de départ -> à adapter selon l'article qu'on choisit de
    "brancher" (ex: abattement retraités = variable différente, cf. variables
    OpenFisca liées aux pensions plutôt qu'au salaire).
    """
    payload = {
        "persons": {
            "individu_1": {
                "salaire_de_base": {period: salaire_annuel},
                "date_naissance": {"ETERNITY": f"{annee_naissance}-01-01"},
            }
        },
        "households": {
            "menage_1": {"personne_de_reference": ["individu_1"]}
        },
        "families": {
            "famille_1": {"parents": ["individu_1"]}
        },
        "foyers_fiscaux": {
            "foyer_fiscal_1": {"declarants": ["individu_1"]}
        },
    }

    # On demande à calculer le revenu disponible (variable classique OpenFisca)
    payload["persons"]["individu_1"]["revenu_disponible"] = {period: None}

    response = requests.post(f"{API_BASE}/calculate", json=payload, timeout=15)
    response.raise_for_status()
    return response.json()


def lister_variables_disponibles(recherche: str = "pension") -> list[str]:
    """
    Utile pour trouver le nom exact de la variable OpenFisca correspondant
    à un article précis (ex: chercher 'pension', 'abattement', 'retraite'...)
    avant de brancher le calcul dans la démo.
    """
    response = requests.get(f"{API_BASE}/variables", timeout=15)
    response.raise_for_status()
    variables = response.json()
    return [v for v in variables if recherche.lower() in v.lower()]


if __name__ == "__main__":
    print("Test 1 — recherche de variables liées aux pensions/retraite :")
    try:
        vars_pension = lister_variables_disponibles("pension")
        print(f"{len(vars_pension)} variables trouvées, ex: {vars_pension[:10]}")
    except Exception as e:
        print(f"Erreur (normal si pas de réseau ici) : {e}")

    print("\nTest 2 — calcul d'un revenu disponible simple :")
    try:
        result = calculer_impot_revenu(salaire_annuel=25000, annee_naissance=1985)
        print(result)
    except Exception as e:
        print(f"Erreur (normal si pas de réseau ici) : {e}")
