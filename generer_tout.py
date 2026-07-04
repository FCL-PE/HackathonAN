from __future__ import annotations

"""
generer_tout.py
Pipeline automatisé de bout en bout : prend un dossier de PDF de lois/décrets,
génère automatiquement la base de fiches (résumé, catégorie, relations) via le LLM,
avec :
  - découpage + filtrage intelligent par mots-clés
  - coupe de sécurité pour respecter la limite de tokens Groq
  - pause anti rate-limit entre chaque appel
  - marqueur "a_valider" sur les champs sensibles (à relire par un humain)

Ce qui EST automatisé : les fiches factuelles (résumé, catégorie, relations).
Ce qui N'EST PAS automatisé (marqué a_valider) : échéances du mandat, argumentaires.

Setup :
    export GROQ_API_KEY="ta_clé"   (ou .env)
    Place tes PDF dans un dossier, ex: pdfs/

    Fichier de correspondance pdfs/manifest.json (indique numéro + nom pour chaque PDF) :
    [
      {"fichier": "loi_climat.pdf", "numero": "2021-1104", "nature": "loi"},
      {"fichier": "loi_aper.pdf",   "numero": "2023-175",  "nature": "loi"}
    ]

Usage :
    python3 generer_tout.py pdfs/
"""

import os
import sys
import json
import time
from dotenv import load_dotenv
from groq import Groq
from extraction import extract_chunks
from synthese_genealogie import extrait_fiche_genealogie

load_dotenv()

# Mots-clés génériques ZAN/urbanisme — filtre les chunks pertinents dans chaque PDF
MOTS_CLES = [
    "artificialis", "agrivolta", "sobriété foncière", "consommation d espace",
    "consommation d'espace", "renaturation", "friche", "étalement urbain",
    "zéro artificialisation", "enaf", "194",
]

# Limite de caractères envoyés au LLM (sécurité rate-limit : ~8000 tokens < 12000/min gratuit)
MAX_CHARS_LLM = 28000
PAUSE_ENTRE_APPELS = 65  # secondes — la limite Groq gratuite est par minute


def filtre_pertinents(chunks) -> str:
    pertinents = [c for c in chunks if any(m in c.text.lower() for m in MOTS_CLES)]
    if not pertinents:
        # aucun mot-clé trouvé : on prend le tout début du texte (souvent l'exposé des motifs)
        pertinents = chunks[:3]
    texte = " ".join(c.text for c in pertinents)
    return texte[:MAX_CHARS_LLM]


def enrichit_avec_marqueurs(fiche: dict, meta: dict) -> dict:
    """Ajoute les champs sensibles non automatisables, marqués comme à valider."""
    fiche["numero"] = meta["numero"]
    fiche["nature"] = meta.get("nature", "loi")
    fiche["_genere_par"] = "llm_auto"
    # Champs sensibles : présents mais vides + marqués à valider par un humain
    fiche["argumentaire"] = {"a_valider": True, "contenu": None}
    fiche["echeances"] = {"a_valider": True, "contenu": None}
    return fiche


def main():
    if len(sys.argv) < 2:
        print("Usage : python3 generer_tout.py <dossier_pdfs>/")
        sys.exit(1)

    dossier = sys.argv[1].rstrip("/")
    manifest_path = os.path.join(dossier, "manifest.json")

    if not os.path.exists(manifest_path):
        print(f"❌ Il manque {manifest_path}")
        print("Crée-le avec la liste de tes PDF (voir l'entête du script pour le format).")
        sys.exit(1)

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    base = []

    print(f"{len(manifest)} textes à traiter.\n")

    for i, meta in enumerate(manifest, 1):
        pdf_path = os.path.join(dossier, meta["fichier"])
        print(f"[{i}/{len(manifest)}] {meta['fichier']} (n° {meta['numero']})")

        if not os.path.exists(pdf_path):
            print(f"    ⚠️  fichier introuvable, ignoré\n")
            continue

        try:
            chunks = extract_chunks(pdf_path, max_chars=6000)
            texte = filtre_pertinents(chunks)
            print(f"    {len(texte)} caractères envoyés au LLM...")

            fiche = extrait_fiche_genealogie(texte, numero_deja_connu=meta["numero"], client=client)
            fiche = enrichit_avec_marqueurs(fiche, meta)
            base.append(fiche)
            print(f"    ✓ {fiche.get('titre', '?')} — catégorie: {fiche.get('categorie', '?')}, "
                  f"{len(fiche.get('relations', []))} relation(s)")

        except Exception as e:
            print(f"    ❌ erreur : {e}")

        # Pause anti rate-limit, sauf après le dernier
        if i < len(manifest):
            print(f"    ⏳ pause {PAUSE_ENTRE_APPELS}s (limite Groq gratuite)...\n")
            time.sleep(PAUSE_ENTRE_APPELS)

    # Sauvegarde
    os.makedirs("data", exist_ok=True)
    out = "data/base_generee.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"✓ {len(base)} fiches générées automatiquement → {out}")
    a_valider = sum(1 for f in base if f.get("argumentaire", {}).get("a_valider"))
    print(f"⚠️  {a_valider} fiches ont des champs sensibles à faire valider par un humain")
    print("   (argumentaires + échéances — à ne pas montrer comme 'validé' sans relecture)")


if __name__ == "__main__":
    main()
