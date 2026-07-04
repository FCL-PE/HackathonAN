"""
synthese.py
Appelle Groq pour transformer un chunk de texte en synthèse structurée JSON,
avec traçabilité vers la page source.

Setup:
    export GROQ_API_KEY="ta_clé"   (jamais en dur dans le code)

Usage:
    from synthese import summarize_chunk
    result = summarize_chunk(chunk)
"""

from __future__ import annotations

import os
import json
from dotenv import load_dotenv
from groq import Groq
from extraction import Chunk

load_dotenv()

# Modèle Groq à choisir sur place selon dispo/latence (llama-3.3-70b-versatile
# est un bon défaut rapide+précis, à confirmer avec les orga du hackathon)
MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """Tu es un assistant qui vulgarise des textes législatifs français pour des citoyens.
Tu dois répondre UNIQUEMENT en JSON valide, sans texte avant/après, sans balises markdown.

Format de sortie strict :
{
  "points_cles": ["point 1 en une phrase simple", "point 2", ...],
  "pour": ["argument favorable 1", ...],
  "contre": ["argument défavorable 1", ...],
  "impacts_chiffres": [
    {"description": "ce que ça change concrètement", "montant": "chiffre si présent, sinon null"}
  ],
  "resume_une_phrase": "le texte résumé en une seule phrase simple"
}

Règles :
- Si une catégorie est absente du texte, renvoie une liste vide, n'invente rien.
- Reste factuel, n'ajoute pas d'opinion personnelle.
- Langage simple, accessible à quelqu'un sans formation juridique.
"""


def summarize_chunk(chunk: Chunk, client: Groq | None = None) -> dict:
    """Envoie un chunk à Groq et retourne la synthèse structurée + traçabilité source."""
    if client is None:
        client = Groq(api_key=os.environ["GROQ_API_KEY"])

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": chunk.text},
        ],
        temperature=0.2,  # peu de créativité, on veut de la fidélité au texte
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        # Filet de sécurité : le LLM a mal formaté -> on ne plante pas la démo
        parsed = {"error": "parse_failed", "raw": raw}

    # Traçabilité : on rattache la source précise à chaque synthèse
    parsed["_source"] = {
        "chunk_id": chunk.id,
        "page_start": chunk.page_start,
        "page_end": chunk.page_end,
    }
    return parsed


def merge_summaries(summaries: list[dict]) -> dict:
    """
    Étape map-reduce : fusionne les synthèses de tous les chunks d'un même document
    en une synthèse globale cohérente (à affiner avec un 2e appel LLM si besoin
    pour dé-dupliquer/reformuler, cf. la stratégie discutée : chunk par chunk
    PUIS un passage de synthèse globale).
    """
    merged = {"points_cles": [], "pour": [], "contre": [], "impacts_chiffres": [], "sources": []}
    for s in summaries:
        if "error" in s:
            continue
        merged["points_cles"] += s.get("points_cles", [])
        merged["pour"] += s.get("pour", [])
        merged["contre"] += s.get("contre", [])
        merged["impacts_chiffres"] += s.get("impacts_chiffres", [])
        merged["sources"].append(s["_source"])
    return merged


if __name__ == "__main__":
    # Test rapide avec un texte factice (pas besoin de PDF pour valider le format)
    fake_chunk = Chunk(
        id=0,
        text="Article 1 : Le montant de l'allocation est porté à 150 euros par mois "
             "pour les foyers dont le revenu fiscal est inférieur à 20 000 euros. "
             "Cette mesure entre en vigueur le 1er janvier prochain.",
        page_start=1,
        page_end=1,
    )
    print("Clé GROQ_API_KEY présente :", "GROQ_API_KEY" in os.environ)
    if "GROQ_API_KEY" in os.environ:
        result = summarize_chunk(fake_chunk)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("Définis GROQ_API_KEY pour tester l'appel réel.")
