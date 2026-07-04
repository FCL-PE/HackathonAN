# Méthodologie technique

## Vue d'ensemble

Le projet a deux volets, l'un manuel (pour débloquer la démo tout de suite),
l'autre automatisé (la vraie brique technique du défi) :

| | Base manuelle (démo) | Pipeline automatisé |
|---|---|---|
| Généalogie des textes | `corpus_zan.py` → `data/genealogie_zan.json` | `synthese_genealogie.py` + `generer_tout.py` |
| Sources juridiques | — | `ingestion.py` + `filtre_llm.py` → `requetes.py` / `export_final.py` |

## 1. Généalogie des textes ZAN

`corpus_zan.py` est la transcription structurée d'un corpus de référence transmis
par le porteur du défi (Nicolas Thouvenin) : 15 lois, 11 décrets, 5 textes
infra-réglementaires et 2 propositions en cours, chacun avec une catégorie
(fondatrice/préparatoire/sectorielle pour une loi, noyau/connexe pour un décret)
et des relations explicites vers les autres textes (`modifie`, `corrige`,
`précise`, `remplace`...). C'est la base actuellement chargée dans `app.html`.

`synthese_genealogie.py` automatise ce que ce corpus a fait à la main : à partir
du texte intégral d'une loi ou d'un décret, un LLM (Groq, `llama-3.3-70b-versatile`)
extrait la même fiche structurée (titre, date, catégorie, résumé, relations),
avec une consigne stricte de ne jamais inventer une relation non mentionnée
explicitement dans le texte. `generer_tout.py` orchestre ce script sur un
dossier de PDF (filtrage par mots-clés ZAN, découpage pour respecter les
limites de tokens, pause anti rate-limit), puis `injecter_dans_app.py` bascule
la base générée dans `app.html` à la place de la base manuelle.

Champs marqués `a_valider` : les échéances de mandat et les argumentaires ne
sont **pas** générés automatiquement (trop sensibles pour être publiés sans
relecture humaine) — voir `argumentaires.json` / `echeances_mandat.json`,
actuellement remplis à la main pour la loi Climat et Résilience (2021-1104) à
titre de démonstration du format.

## 2. Sources juridiques (codes, jurisprudence, droit UE)

`ingestion.py` prend des exports de type `zan1.json`/`zan2.json` (sources
juridiques liées au ZAN : codes, jurisprudence, BOFiP, CNIL, droit UE), les
déduplique, les classe par **force juridique** (contraignant vs. interprétatif/
doctrine) et applique une première heuristique transparente pour écarter le
bruit évident (ex. Code du vin, CNIL 1994 sur un panel INSEE — présents dans le
corpus brut mais sans lien avec l'urbanisme). Les sources ambiguës (jurisprudence
identifiée par un simple numéro de dossier, droit UE générique) sont marquées
« à vérifier » plutôt qu'incluses ou exclues d'office.

`filtre_llm.py` tranche ces cas ambigus via un LLM, avec un niveau de confiance
explicite (haute/moyenne/faible) — le prompt demande explicitement au modèle
d'assumer une confiance faible plutôt que de trancher à l'aveugle sur un simple
numéro de dossier. `requetes.py` et `export_final.py` exposent ensuite cette
base filtrée (timeline, filtre par type de source, par force juridique, par
niveau de confiance) pour l'intégrer à l'application.

## 3. Explorations complémentaires (non branchées dans la démo)

- `openfisca_client.py` : appel à l'API publique OpenFisca-France pour calculer
  un impact chiffré réel (ex. impact fiscal d'une mesure) plutôt qu'une
  estimation générée par un LLM — piste explorée pour fiabiliser les chiffres
  d'impact, pas encore reliée à une fiche précise du corpus ZAN.

## Limites connues

- La base actuellement affichée dans `app.html` est la transcription manuelle
  (`corpus_zan.py`), pas encore la sortie du pipeline automatisé — les deux
  produisent le même format, la bascule est un `injecter_dans_app.py` près.
- `synthese.py`, `synthese_genealogie.py`, `filtre_llm.py` et
  `openfisca_client.py` nécessitent un accès réseau (API Groq / OpenFisca) non
  disponible dans tous les environnements de développement — testés localement
  avec une clé `GROQ_API_KEY`.
