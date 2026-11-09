# -*- coding: utf-8 -*-
"""
StageX-Marrakech - Intégration RÉELLE de Claude via l'API Anthropic.

Ce que Claude fait ici (et seulement ça) :
  1. rechercher()  : cherche des offres sur le web avec l'outil serveur
                     "web_search" (+ "web_fetch" pour lire les pages autorisées).
  2. extraire()    : transforme le texte d'une offre que VOUS avez copié
                     (ex. depuis Indeed dans votre navigateur) en champs structurés.

Garde-fous anti-invention (appliqués par NOTRE code, pas par confiance en Claude) :
  - une URL proposée par Claude n'est gardée que si elle figure réellement dans
    les résultats de recherche/lecture renvoyés par l'API ;
  - un titre/une entreprise extraits ne sont gardés que s'ils apparaissent dans
    le texte source ; sinon -> "Non précisé" ou rejet ;
  - ensuite les règles de stagex_regles.py (Marrakech, stage, domaine) s'appliquent.

Prérequis : une clé API (https://platform.claude.com) dans la variable
d'environnement ANTHROPIC_API_KEY. L'abonnement claude.ai (Pro/Max) ne donne
PAS accès à l'API : c'est un compte séparé, facturé à l'usage.
"""

import json
import os
import re

from stagex_regles import NON_PRECISE, normaliser, valeur

MODELE = os.environ.get("STAGEX_CLAUDE_MODEL", "claude-sonnet-5-5")

DOMAINES_RECHERCHE = {
    "Intelligence Artificielle": "stage intelligence artificielle machine learning Marrakech",
    "Data Analyst": "stage data analyst Marrakech",
    "Développement": "stage développeur web Marrakech",
    "Infrastructure Digitale": "stage systèmes réseaux cloud devops Marrakech",
    "Cybersécurité": "stage cybersécurité Marrakech",
}

CHAMPS = ["titre", "entreprise_source", "ville", "adresse", "description", "profil",
          "date_publication", "url_source", "url_candidature", "email_candidature",
          "duree"]

CONSIGNES = """Tu aides le site StageX-Marrakech à recenser des offres de STAGE réelles.
Règles absolues :
- N'invente jamais rien. Chaque offre doit provenir d'une page que tu as réellement
  trouvée avec l'outil de recherche ou lue avec l'outil de lecture.
- Ne garde que : stage / PFE / internship, situé à Marrakech (ou région Marrakech-Safi),
  dans l'un de ces domaines : Intelligence Artificielle, Data Analyst, Développement,
  Infrastructure Digitale, Cybersécurité.
- url_source = l'URL exacte de la page de l'offre (pas une page de liste générique).
- Si une information n'est pas écrite sur la page, mets null.
- La description doit être un court résumé fidèle (3 phrases max), pas une copie.
Réponds en terminant par un bloc :
<json>[{"titre":..., "entreprise_source":..., "ville":..., "adresse":..., "description":...,
"profil":..., "date_publication":..., "url_source":..., "url_candidature":...,
"email_candidature":..., "duree":...}]</json>
Si tu ne trouves aucune offre conforme, renvoie <json>[]</json>."""


def _client():
    try:
        import anthropic
    except ImportError:
        raise SystemExit("Le paquet 'anthropic' n'est pas installé : pip install anthropic")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY absente. Voir le fichier .env (étape 3 du guide).")
    return anthropic.Anthropic()


def _lire_json(texte):
    m = re.findall(r"<json>(.*?)</json>", texte, flags=re.S)
    if not m:
        return []
    try:
        data = json.loads(m[-1].strip())
        return data if isinstance(data, list) else [data]
    except json.JSONDecodeError:
        return []


def _urls_vues(blocs):
    """Toutes les URL réellement renvoyées par web_search / web_fetch."""
    urls = set()
    for b in blocs:
        t = getattr(b, "type", "")
        contenu = getattr(b, "content", None)
        if t == "web_search_tool_result" and isinstance(contenu, list):
            for r in contenu:
                u = getattr(r, "url", None)
                if u:
                    urls.add(u.rstrip("/"))
        elif t == "web_fetch_tool_result" and contenu is not None:
            u = getattr(contenu, "url", None)
            if u:
                urls.add(u.rstrip("/"))
    return urls


def rechercher(domaine, requete=None, max_recherches=5):
    """Lance une recherche Claude pour un domaine. Renvoie (offres, stats)."""
    client = _client()
    requete = requete or DOMAINES_RECHERCHE[domaine]
    messages = [{"role": "user", "content":
                 f"Trouve des offres de stage réelles et actuelles pour : « {requete} ». "
                 f"Domaine StageX visé : {domaine}. Cherche notamment sur les sites d'emploi "
                 f"marocains (rekrute.com, emploi.ma, marocannonces), LinkedIn, Indeed, "
                 f"et les pages carrières des entreprises de Marrakech."}]
    outils = [
        {"type": "web_search_20250305", "name": "web_search", "max_uses": max_recherches},
        {"type": "web_fetch_20250910", "name": "web_fetch", "max_uses": 8,
         "max_content_tokens": 8000},
    ]

    tous_blocs = []
    for _ in range(5):  # gestion de "pause_turn" (recherches longues)
        rep = client.messages.create(model=MODELE, max_tokens=8000, system=CONSIGNES,
                                     messages=messages, tools=outils)
        tous_blocs.extend(rep.content)
        if rep.stop_reason != "pause_turn":
            break
        messages.append({"role": "assistant", "content": rep.content})

    texte_final = "".join(getattr(b, "text", "") for b in tous_blocs if getattr(b, "type", "") == "text")
    urls_reelles = _urls_vues(tous_blocs)
    proposees = _lire_json(texte_final)

    gardees, ecartees = [], []
    for o in proposees:
        url = (o.get("url_source") or "").rstrip("/")
        if url and url in urls_reelles:
            o = {k: valeur(o.get(k)) for k in CHAMPS}
            o["url_source"] = url
            gardees.append(o)
        else:
            ecartees.append(o.get("url_source"))

    stats = {"recherches": rep.usage.server_tool_use.web_search_requests if getattr(rep.usage, "server_tool_use", None) else 0,
             "proposees": len(proposees), "url_confirmees": len(gardees),
             "url_non_confirmees": ecartees}
    return gardees, stats


CONSIGNES_EXTRACTION = """Tu extrais les informations d'une offre de stage à partir du texte fourni.
N'utilise QUE le texte fourni. Si une information n'y figure pas, mets null.
Ne reformule pas le titre ni le nom de l'entreprise : recopie-les tels qu'écrits.
La description : résumé fidèle de 3 phrases max. Le profil : résumé des compétences demandées.
Réponds uniquement par <json>{"titre":..., "entreprise_source":..., "ville":..., "adresse":...,
"description":..., "profil":..., "date_publication":..., "url_candidature":...,
"email_candidature":..., "duree":...}</json>"""


def _present(valeur_extraite, texte_source):
    v = normaliser(valeur_extraite)
    if not v or v == normaliser(NON_PRECISE):
        return False
    mots = [m for m in v.split() if len(m) > 2] or [v]
    src = normaliser(texte_source)
    return sum(1 for m in mots if m in src) >= max(1, int(len(mots) * 0.7))


def extraire(texte_offre, url_source):
    """Structure le texte d'une offre copiée à la main. Renvoie un dict ou None."""
    client = _client()
    rep = client.messages.create(
        model=MODELE, max_tokens=2000, system=CONSIGNES_EXTRACTION,
        messages=[{"role": "user", "content": f"URL : {url_source}\n\nTexte de l'offre :\n{texte_offre}"}])
    texte = "".join(getattr(b, "text", "") for b in rep.content)
    data = _lire_json(texte)
    if not data:
        return None
    o = {k: valeur(data[0].get(k)) for k in CHAMPS}
    o["url_source"] = url_source

    # Garde-fous : titre, entreprise, ville, email, url_candidature doivent être dans le texte.
    if not _present(o["titre"], texte_offre):
        return None
    for champ in ("entreprise_source", "ville", "email_candidature", "url_candidature", "date_publication"):
        if o[champ] != NON_PRECISE and not _present(o[champ], texte_offre):
            o[champ] = NON_PRECISE
    return o
