# -*- coding: utf-8 -*-
"""
StageX-Marrakech - Source Jooble (API officielle, gratuite, clé sur demande).

Jooble est un agrégateur : il reprend des offres publiées sur d'autres sites
(sites marocains, pages carrières... et parfois Indeed). C'est la façon PROPRE
d'obtenir une partie des offres visibles ailleurs, sans scraper.

Clé : formulaire sur https://jooble.org/api/about (indiquez votre site/projet).
Jooble vous indique l'adresse à utiliser avec la clé (souvent propre au pays) :
mettez-la dans JOOBLE_HOST (ex. "ma.jooble.org" si c'est celle qu'on vous donne).
Le quota de requêtes est limité : ce script en fait une par domaine (5 au total).
"""

import os
import requests

from stagex_regles import valeur

REQUETES = {
    "Intelligence Artificielle": "stage intelligence artificielle",
    "Data Analyst": "stage data analyst",
    "Développement": "stage développeur",
    "Infrastructure Digitale": "stage réseaux systèmes",
    "Cybersécurité": "stage cybersécurité",
}


def rechercher(domaine):
    cle = os.environ.get("JOOBLE_API_KEY")
    if not cle:
        raise SystemExit("JOOBLE_API_KEY absente (voir .env).")
    hote = os.environ.get("JOOBLE_HOST", "jooble.org")
    r = requests.post(f"https://{hote}/api/{cle}",
                      json={"keywords": REQUETES[domaine], "location": "Marrakech"},
                      timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"Jooble a répondu HTTP {r.status_code} : {r.text[:200]}")
    offres = []
    for j in r.json().get("jobs", []):
        if not j.get("link"):
            continue
        offres.append({
            "titre": valeur(j.get("title")),
            "entreprise_source": valeur(j.get("company")),
            "ville": valeur(j.get("location")),
            "adresse": valeur(None),
            "description": valeur(_sans_html(j.get("snippet"))),
            "profil": valeur(None),
            "date_publication": valeur((j.get("updated") or "")[:10]),
            "url_source": j["link"],
            "url_candidature": valeur(None),
            "email_candidature": valeur(None),
            "duree": valeur(None),
            "source": "Jooble" + (f" (via {j['source']})" if j.get("source") else ""),
        })
    return offres


def _sans_html(t):
    import re
    return re.sub(r"<[^>]+>", "", t or "").replace("&nbsp;", " ").strip()
