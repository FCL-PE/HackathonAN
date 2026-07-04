# ParlementClair — pipeline autonome (brouillon Amine)

Pipeline indépendant, à fusionner/adapter avec le repo de Cérine une fois sur place.

## Setup (à faire sur ta machine, avec ta clé Groq)

```bash
pip install pymupdf groq --break-system-packages
export GROQ_API_KEY="ta_clé_ici"
```

## Fichiers

- `extraction.py` — découpe un PDF en chunks, en gardant la trace des pages (testé ✅, fonctionne)
- `synthese.py` — envoie chaque chunk à Groq, retourne un JSON structuré
  (points_cles / pour / contre / impacts_chiffres) + la source (page).
  **Pas testable ici (pas d'accès réseau à api.groq.com dans ce sandbox) — à tester
  avec ta clé sur place.**

## Test rapide une fois la clé configurée

```bash
python3 synthese.py          # test avec un texte factice, valide juste le format JSON
python3 extraction.py rapport.pdf   # extraction sur un vrai PDF
```

## Pipeline complet (à écrire ensemble sur place une fois le texte choisi)

```python
from extraction import extract_chunks
from synthese import summarize_chunk, merge_summaries

chunks = extract_chunks("rapport.pdf")
summaries = [summarize_chunk(c) for c in chunks]
final = merge_summaries(summaries)
```

## Points à trancher avec Cérine / en conférence

- Le vrai texte source à traiter pour la démo (loi de finances ? rapport sociétal ?)
- Format réel des données `an-dossiers-legislatifs` / `premier-ministre-jorf`
  (API ? dump JSON ? PDF direct ?) — à confirmer à la conférence "Initiation aux
  données et aux outils"
- Choix définitif du modèle Groq (llama-3.3-70b-versatile par défaut ici, à ajuster
  selon vitesse/qualité observée en live)
