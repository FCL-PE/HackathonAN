from __future__ import annotations

"""
injecter_dans_app.py
Prend la base générée (data/base_generee.json) et l'injecte dans app.html,
en remplaçant les données DATA existantes.

Fusionne aussi avec les échéances/argumentaires validés à la main s'ils existent.

Usage :
    python3 injecter_dans_app.py
"""

import json
import os


def charge(path, defaut):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return defaut


def main():
    # Base générée automatiquement par le LLM
    base = charge("data/base_generee.json", [])
    if not base:
        print("❌ data/base_generee.json est vide ou absent. Lance d'abord generer_tout.py")
        return

    # Nettoie les champs internes avant injection dans l'app
    for f in base:
        f.pop("_genere_par", None)
        # simplifie les champs sensibles pour l'app (juste le contenu s'il est validé)
        if isinstance(f.get("argumentaire"), dict):
            f["argumentaire"] = f["argumentaire"].get("contenu")
        if isinstance(f.get("echeances"), dict):
            f["echeances"] = f["echeances"].get("contenu")

    data_js = json.dumps(base, ensure_ascii=False)

    # Injecte dans app.html en remplaçant le tableau DATA existant
    with open("app.html", encoding="utf-8") as f:
        html = f.read()

    import re
    # remplace: const DATA = [...];  (le premier gros tableau)
    nouveau = re.sub(
        r"const DATA = \[.*?\];",
        f"const DATA = {data_js};",
        html,
        count=1,
        flags=re.DOTALL,
    )

    if nouveau == html:
        print("⚠️  Le motif 'const DATA = [...]' n'a pas été trouvé dans app.html")
        return

    with open("app.html", "w", encoding="utf-8") as f:
        f.write(nouveau)

    print(f"✓ {len(base)} fiches injectées dans app.html")
    print("  Ouvre app.html dans ton navigateur pour vérifier.")


if __name__ == "__main__":
    main()
