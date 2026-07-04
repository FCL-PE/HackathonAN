from __future__ import annotations

"""
synthese_genealogie.py
LE VRAI PIPELINE : prend le texte complet d'une loi/d'un décret et produit
automatiquement le même format que data/genealogie_zan.json (numero, titre,
date, categorie, resume, relations) — via le LLM, pas à la main.

corpus_zan.py était une transcription manuelle de l'email de Nicolas, utile
comme exemple/mock pour débloquer le frontend en attendant. CE script est
la vraie brique technique : automatiser ce que Nicolas a fait à la main.

Setup :
    export GROQ_API_KEY="ta_clé"   (ou via .env + python-dotenv)

Usage :
    from synthese_genealogie import extrait_fiche_genealogie
    fiche = extrait_fiche_genealogie(texte_complet_de_la_loi, numero_deja_connu="2021-1104")
"""

import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """Tu extrais une fiche structurée d'un texte de loi ou de décret français
lié au ZAN (Zéro Artificialisation Nette), pour construire une généalogie législative
destinée à des élus locaux.

Réponds UNIQUEMENT en JSON valide, sans texte avant/après, avec exactement ces champs :
{
  "titre": "nom usuel du texte (ex: 'Loi Climat et Résilience')",
  "date": "AAAA-MM-JJ si trouvable dans le texte, sinon null",
  "categorie": "fondatrice, preparatoire, sectorielle (pour une loi) ou noyau, connexe (pour un décret)",
  "resume": "1 à 2 phrases factuelles sur ce que ce texte change concrètement",
  "relations": [
    {"cible": "numéro ou nom du texte visé si mentionné explicitement",
     "type": "modifie / complète / remplace / précise / abroge",
     "detail": "précision courte, ou null"}
  ]
}

Règles strictes :
- N'invente JAMAIS une relation qui n'est pas explicitement mentionnée dans le texte fourni.
- Si tu n'es pas sûr d'une catégorie ou d'une relation, laisse le champ à null ou liste vide
  plutôt que de deviner.
- "relations" doit rester vide si le texte ne mentionne explicitement aucun autre texte.
"""


def extrait_fiche_genealogie(texte: str, numero_deja_connu: str | None = None, client: Groq | None = None) -> dict:
    if client is None:
        client = Groq(api_key=os.environ["GROQ_API_KEY"])

    contenu_utilisateur = texte
    if numero_deja_connu:
        contenu_utilisateur = (
            f"IMPORTANT : le texte ci-dessous EST la loi/le décret numéro {numero_deja_connu} "
            f"lui-même — ce n'est pas un texte qui parle DE cette loi. "
            f"Le titre que tu dois renvoyer est celui de CE texte (numéro {numero_deja_connu}), "
            f"pas celui d'une autre loi qu'il mentionne ou modifie, même si cette autre loi "
            f"est citée très souvent dans l'extrait.\n\n---\n\n{texte}"
        )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": contenu_utilisateur},
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    try:
        fiche = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        fiche = {"erreur": "parsing_llm_echoue", "brut": response.choices[0].message.content}

    if numero_deja_connu:
        fiche["numero"] = numero_deja_connu

    return fiche


if __name__ == "__main__":
    # Test avec un texte factice reprenant le style d'un article de loi,
    # pour valider le format de sortie avant de brancher sur un vrai texte.
    texte_test = """
    Loi n° 2022-217 du 21 février 2022 relative à la différenciation, la
    décentralisation, la déconcentration et portant diverses mesures de
    simplification de l'action publique locale.

    Article 194 de la loi n° 2021-1104 du 22 août 2021 est modifié afin
    d'ajuster le calendrier de territorialisation des objectifs de réduction
    de l'artificialisation des sols.
    """
    print("Clé GROQ_API_KEY présente :", "GROQ_API_KEY" in os.environ)
    if "GROQ_API_KEY" in os.environ:
        fiche = extrait_fiche_genealogie(texte_test, numero_deja_connu="2022-217")
        print(json.dumps(fiche, indent=2, ensure_ascii=False))
    else:
        print("Définis GROQ_API_KEY pour tester l'appel réel.")
