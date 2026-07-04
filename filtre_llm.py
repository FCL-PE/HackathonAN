from __future__ import annotations

"""
filtre_llm.py
Utilise Groq pour trancher les sources marquées "à vérifier" par ingestion.py
(celles où le titre seul ne suffit pas : jurisprudences, textes UE, doctrine...).

Setup :
    export GROQ_API_KEY="ta_clé"

Usage :
    python3 filtre_llm.py
    (lit data/sources_ingerees.json, écrit data/sources_filtrees.json)
"""

import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """Tu aides à filtrer des sources juridiques pour un outil destiné
aux élus locaux sur la loi ZAN (Zéro Artificialisation Nette) — la politique française
de limitation de l'étalement urbain et de préservation des sols.

On te donne le titre, le type et la juridiction (si dispo) d'une source. Tu dois dire
si elle est probablement pertinente pour comprendre le ZAN, sur la seule base de ces
métadonnées (tu n'as pas le texte complet).

Réponds UNIQUEMENT en JSON, sans texte avant/après :
{
  "pertinent": true ou false,
  "confiance": "haute", "moyenne" ou "faible",
  "raison": "une phrase courte expliquant pourquoi"
}

Sois honnête sur l'incertitude : si le titre est un simple numéro de dossier
(ex: "23/11043") sans contexte, la confiance doit être "faible", pas "haute".
"""


def juge_pertinence(source: dict, client: Groq) -> dict:
    contexte = (
        f"Titre : {source.get('titre')}\n"
        f"Type de source : {source.get('type')}\n"
        f"Juridiction : {source.get('juridiction') or 'N/A'}\n"
        f"Date : {source.get('date') or 'N/A'}"
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": contexte},
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    try:
        return json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        return {"pertinent": None, "confiance": "faible", "raison": "erreur de parsing LLM"}


def main():
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    with open("data/sources_ingerees.json", encoding="utf-8") as f:
        sources = json.load(f)

    a_verifier = [s for s in sources if s["pertinent_zan"] and s["raison_exclusion"]]
    print(f"{len(a_verifier)} sources à faire trancher par le LLM...\n")

    for i, s in enumerate(a_verifier, 1):
        avis = juge_pertinence(s, client)
        s["avis_llm"] = avis
        s["pertinent_zan"] = avis.get("pertinent", s["pertinent_zan"])
        statut = "GARDÉE" if avis.get("pertinent") else "ÉCARTÉE"
        print(f"[{i}/{len(a_verifier)}] {statut} ({avis.get('confiance')}) — {s['titre'][:60]}")
        print(f"    → {avis.get('raison')}\n")

    with open("data/sources_filtrees.json", "w", encoding="utf-8") as f:
        json.dump(sources, f, ensure_ascii=False, indent=2)

    gardees = sum(1 for s in sources if s["pertinent_zan"])
    print(f"\nRésultat : {gardees}/{len(sources)} sources gardées après filtre LLM.")
    print("Sauvegardé dans data/sources_filtrees.json")


if __name__ == "__main__":
    main()
