# -*- coding: utf-8 -*-
"""
StageX-Marrakech - Règles de filtrage (aucune donnée inventée).

Ce module ne fait AUCUN appel réseau. Il contient uniquement :
  - la détection "stage / PFE / internship"
  - la détection "Marrakech"
  - la classification dans les 5 domaines StageX
  - l'extraction de la durée SI elle est écrite dans le texte
Toute information absente reste "Non précisé".
"""

import re
import unicodedata

NON_PRECISE = "Non précisé"

DOMAINES = [
    "Intelligence Artificielle",
    "Data Analyst",
    "Développement",
    "Infrastructure Digitale",
    "Cybersécurité",
]

# Ordre de priorité en cas d'égalité : le domaine le plus spécifique gagne.
PRIORITE = [
    "Cybersécurité",
    "Intelligence Artificielle",
    "Data Analyst",
    "Infrastructure Digitale",
    "Développement",
]

# Mots-clés (comparés en minuscules, sans accents, mots entiers).
# Les listes reprennent celles du projet + quelques équivalents français
# indispensables pour les offres marocaines (marqués "FR").
MOTS_CLES = {
    "Intelligence Artificielle": [
        "artificial intelligence", "intelligence artificielle", "machine learning",
        "deep learning", "computer vision", "nlp", "natural language processing",
        "apprentissage automatique",          # FR
        "vision par ordinateur",              # FR
        "llm", "ia generative", "generative ai",
    ],
    "Data Analyst": [
        "data analyst", "data analysis", "data analytics", "data science",
        "data scientist", "business intelligence", "analytics",
        "analyste de donnees", "analyse de donnees", "data analyste",  # FR
        "power bi",
    ],
    "Développement": [
        "development", "developer", "software development", "software engineer",
        "web development", "web developer", "frontend", "front-end", "backend",
        "back-end", "full stack", "full-stack", "fullstack", "programming",
        "developpeur", "developpement", "developpeuse",  # FR
        "programmation",                                   # FR
    ],
    "Infrastructure Digitale": [
        "infrastructure", "infrastructure digitale", "it infrastructure", "systems",
        "system administration", "system administrator", "network", "networking",
        "networks", "cloud", "cloud computing", "devops", "linux", "servers",
        # FR : pas "réseau(x)" seul, sinon "réseaux sociaux" (marketing) serait classé ici
        "reseau informatique", "reseaux informatiques", "administrateur reseau",
        "administrateur reseaux", "administrateur systeme", "administration systeme",
        "systemes et reseaux", "reseaux et telecoms", "reseaux et systemes",
    ],
    "Cybersécurité": [
        "cybersecurity", "cyber security", "cybersecurite", "security",
        "information security", "network security", "ethical hacking",
        "penetration testing", "pentest",
        "securite informatique", "securite des systemes d'information",  # FR
    ],
}

# Sigles : comparés en MAJUSCULES et en mots entiers, sinon "ai" correspondrait
# au français "j'ai" et "soc" à "société".
SIGLES = {
    "Intelligence Artificielle": ["AI", "ML", "IA"],
    "Cybersécurité": ["SOC"],
}

MOTS_STAGE = [
    "intern", "interns", "internship", "internships", "stage", "stages",
    "stagiaire", "stagiaires", "trainee", "pfe", "end of studies",
    "end-of-studies", "final year project", "projet de fin d'etudes",
    "fin d'etudes",
]

MOTS_PFE = ["pfe", "end of studies", "end-of-studies", "final year project",
            "projet de fin d'etudes", "fin d'etudes"]

MOTS_MARRAKECH = ["marrakech", "marrakesh", "marrakech-safi", "marrakesh-safi"]


def normaliser(texte):
    """minuscules + suppression des accents + espaces simples."""
    if not texte:
        return ""
    texte = unicodedata.normalize("NFKD", str(texte))
    texte = "".join(c for c in texte if not unicodedata.combining(c))
    texte = texte.replace("\u2019", "'")
    return re.sub(r"\s+", " ", texte).strip().lower()


def _contient(texte_normalise, mot):
    motif = r"(?<![a-z0-9])" + re.escape(normaliser(mot)) + r"(?![a-z0-9])"
    return re.search(motif, texte_normalise) is not None


def _compte_sigle(texte_brut, sigle):
    if not texte_brut:
        return 0
    return len(re.findall(r"(?<![A-Za-z0-9])" + re.escape(sigle) + r"(?![A-Za-z0-9])", texte_brut))


def est_un_stage(*textes):
    t = normaliser(" ".join(x or "" for x in textes))
    return any(_contient(t, m) for m in MOTS_STAGE)


def type_offre(*textes):
    """'PFE' si le texte parle de PFE / fin d'études, sinon 'Stage'."""
    t = normaliser(" ".join(x or "" for x in textes))
    return "PFE" if any(_contient(t, m) for m in MOTS_PFE) else "Stage"


def est_a_marrakech(*textes):
    t = normaliser(" ".join(x or "" for x in textes))
    return any(_contient(t, m) for m in MOTS_MARRAKECH)


def scores_domaines(titre, description=""):
    """Score de chaque domaine. Un mot trouvé dans le titre compte 3 fois."""
    scores = {d: 0 for d in DOMAINES}
    for poids, brut in ((3, titre or ""), (1, description or "")):
        t = normaliser(brut)
        for domaine, mots in MOTS_CLES.items():
            for m in mots:
                if _contient(t, m):
                    scores[domaine] += poids
        for domaine, sigles in SIGLES.items():
            for s in sigles:
                scores[domaine] += poids * min(_compte_sigle(brut, s), 1)
    return scores


def classer_domaine(titre, description=""):
    """Renvoie un des 5 domaines StageX, ou None si aucun ne correspond."""
    scores = scores_domaines(titre, description)
    meilleur = max(scores.values())
    if meilleur == 0:
        return None
    for d in PRIORITE:
        if scores[d] == meilleur:
            return d
    return None


def extraire_duree(*textes):
    """Durée seulement si elle est écrite explicitement (ex. '3 mois')."""
    t = normaliser(" ".join(x or "" for x in textes))
    m = re.search(r"(\d{1,2})\s*(?:a\s*\d{1,2}\s*)?(mois|months?|semaines|weeks?)\b", t)
    if not m:
        return NON_PRECISE
    unite = {"month": "mois", "months": "mois", "week": "semaines",
             "weeks": "semaines"}.get(m.group(2), m.group(2))
    return m.group(0).replace(m.group(2), unite) if unite != m.group(2) else m.group(0)


def valeur(v):
    """Texte propre ou 'Non précisé'."""
    if v is None:
        return NON_PRECISE
    v = str(v).strip()
    if not v or v.lower() in {"null", "none", "n/a", "na", "-", "non precise", "non précisé"}:
        return NON_PRECISE
    return v


def analyser(offre):
    """
    Vérifie une offre (dict) selon les règles StageX.
    Renvoie (accepte: bool, raisons: list[str], domaine, type).
    """
    titre = offre.get("titre") or ""
    desc = " ".join(str(offre.get(k) or "") for k in ("description", "profil"))
    lieu = " ".join(str(offre.get(k) or "") for k in ("ville", "adresse"))

    raisons = []
    if not titre.strip():
        raisons.append("titre absent")
    if not (offre.get("url_source") or "").startswith("http"):
        raisons.append("url_source absente ou invalide")
    if not est_un_stage(titre, desc):
        raisons.append("pas un stage / PFE / internship")
    if not est_a_marrakech(lieu, titre, desc):
        raisons.append("Marrakech non mentionnée")
    domaine = classer_domaine(titre, desc)
    if domaine is None:
        raisons.append("aucun des 5 domaines StageX")

    return (len(raisons) == 0, raisons, domaine, type_offre(titre, desc))
