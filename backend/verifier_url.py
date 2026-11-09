# -*- coding: utf-8 -*-
"""
StageX-Marrakech - Contrôle d'un lien d'offre.

Une seule requête GET, User-Agent honnête, aucun contournement :
si le site refuse (403/429...), on NE réessaie PAS autrement ;
l'offre passe alors en vérification humaine.
"""

import re
import requests

from stagex_regles import normaliser, est_a_marrakech, est_un_stage

UA = "StageX-Marrakech/1.0 (projet etudiant; verification de liens d'offres)"

OK = "ok"                # page lue, titre + Marrakech + stage retrouvés
PARTIEL = "partiel"      # page lue mais contenu non confirmé (souvent JavaScript)
BLOQUE = "bloque"        # le site refuse les robots : vérification humaine
MORT = "mort"            # 404 / 410 : offre retirée
ERREUR = "erreur"


def _texte_html(html):
    html = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    return re.sub(r"<[^>]+>", " ", html)


def controler(url, titre=""):
    """Renvoie (statut, detail)."""
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=20, allow_redirects=True)
    except requests.RequestException as e:
        return ERREUR, f"connexion impossible ({type(e).__name__})"

    if r.status_code in (404, 410):
        return MORT, f"HTTP {r.status_code}"
    if r.status_code in (401, 403, 429, 999):
        return BLOQUE, f"HTTP {r.status_code} (le site refuse les accès automatiques)"
    if r.status_code != 200:
        return ERREUR, f"HTTP {r.status_code}"

    page = normaliser(_texte_html(r.text))
    mots_titre = [m for m in normaliser(titre).split() if len(m) > 3]
    trouves = sum(1 for m in mots_titre if m in page)
    titre_ok = not mots_titre or trouves >= max(1, len(mots_titre) // 2)

    if titre_ok and est_a_marrakech(page) and est_un_stage(page):
        return OK, f"HTTP 200, titre retrouvé ({trouves}/{len(mots_titre)} mots), Marrakech et stage présents"
    return PARTIEL, f"HTTP 200 mais contenu non confirmé ({trouves}/{len(mots_titre)} mots du titre)"
