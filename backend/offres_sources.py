import requests
import sqlite3
import os
import re
from html import unescape
import xml.etree.ElementTree as ET
from urllib.parse import quote


# =========================================================
# CONFIGURATION
# =========================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "stagex.db")


# =========================================================
# DOMAINES STAGEX
# =========================================================

DOMAINES_CIBLES = {

    "Intelligence Artificielle": [
        "intelligence artificielle",
        "artificial intelligence",
        "machine learning",
        "deep learning",
        "computer vision",
        "nlp",
        "natural language processing",
        "tensorflow",
        "pytorch"
    ],

    "Data Analyst": [
        "data analyst",
        "data analysis",
        "data analytics",
        "data science",
        "data scientist",
        "business intelligence",
        "power bi",
        "tableau",
        "sql",
        "pandas"
    ],

    "Développement": [
        "developer",
        "development",
        "software development",
        "software engineer",
        "web development",
        "web developer",
        "frontend",
        "front-end",
        "backend",
        "back-end",
        "full stack",
        "full-stack",
        "programming",
        "python",
        "javascript",
        "java",
        "php"
    ],

    "Infrastructure Digitale": [
        "infrastructure",
        "it infrastructure",
        "system administration",
        "system administrator",
        "network",
        "networking",
        "cloud",
        "cloud computing",
        "devops",
        "linux",
        "server",
        "servers"
    ],

    "Cybersécurité": [
        "cybersecurity",
        "cyber security",
        "cybersécurité",
        "information security",
        "network security",
        "ethical hacking",
        "penetration testing",
        "pentest",
        "soc"
    ]
}


# =========================================================
# MOTS STAGE
# =========================================================

MOTS_STAGE = [
    "stage",
    "stagiaire",
    "intern",
    "internship",
    "trainee",
    "pfe",
    "end of studies",
    "end-of-studies",
    "final year project"
]


# =========================================================
# NETTOYAGE HTML
# =========================================================

def nettoyer_html(texte):

    if not texte:
        return ""

    texte = re.sub(
        r"<[^>]+>",
        " ",
        texte
    )

    texte = unescape(texte)

    texte = re.sub(
        r"\s+",
        " ",
        texte
    )

    return texte.strip()


# =========================================================
# DETECTION DOMAINE
# =========================================================

def detecter_domaine(offre):

    texte = " ".join([
        str(offre.get("titre") or ""),
        str(offre.get("description") or ""),
        str(offre.get("domaine") or "")
    ]).lower()

    for domaine, mots in DOMAINES_CIBLES.items():

        for mot in mots:

            if mot.lower() in texte:

                return domaine

    return None


# =========================================================
# VERIFIER STAGE
# =========================================================

def est_stage(offre):

    texte = " ".join([
        str(offre.get("titre") or ""),
        str(offre.get("description") or ""),
        str(offre.get("type") or ""),
        str(offre.get("domaine") or "")
    ]).lower()

    return any(
        mot in texte
        for mot in MOTS_STAGE
    )


# =========================================================
# VERIFIER MARRAKECH
# =========================================================

def est_marrakech(offre):

    texte = " ".join([
        str(offre.get("ville") or ""),
        str(offre.get("adresse") or ""),
        str(offre.get("description") or "")
    ]).lower()

    mots = [
        "marrakech",
        "marrakesh"
    ]

    return any(
        mot in texte
        for mot in mots
    )


# =========================================================
# FILTRE STAGEX
# =========================================================

def offre_valide(offre):

    if not est_marrakech(offre):
        return False

    if not est_stage(offre):
        return False

    domaine = detecter_domaine(offre)

    if domaine is None:
        return False

    offre["domaine"] = domaine

    return True


# =========================================================
# INSERTION SQLITE
# =========================================================

def inserer_offre(offre):

    conn = sqlite3.connect(DB_PATH)

    existe = conn.execute(
        """
        SELECT id
        FROM offres
        WHERE url_source = ?
        """,
        (offre["url_source"],)
    ).fetchone()

    if existe:

        conn.close()

        return False

    conn.execute(
        """
        INSERT INTO offres (
            titre,
            entreprise_source,
            ville,
            adresse,
            latitude,
            longitude,
            description,
            profil,
            date_publication,
            url_source,
            url_candidature,
            email_candidature,
            source,
            type,
            duree,
            domaine
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            offre.get("titre"),
            offre.get("entreprise_source"),
            offre.get("ville"),
            offre.get("adresse"),
            offre.get("latitude"),
            offre.get("longitude"),
            offre.get("description"),
            offre.get("profil"),
            offre.get("date_publication"),
            offre.get("url_source"),
            offre.get("url_candidature"),
            offre.get("email_candidature"),
            offre.get("source"),
            offre.get("type"),
            offre.get("duree"),
            offre.get("domaine")
        )
    )

    conn.commit()
    conn.close()

    return True


# =========================================================
# REMOTIVE
# =========================================================

def fetch_remotive():

    url = "https://remotive.com/api/remote-jobs"

    response = requests.get(
        url,
        timeout=20,
        headers={
            "User-Agent": "StageX-Marrakech/1.0"
        }
    )

    response.raise_for_status()

    data = response.json()

    offres = []

    for job in data.get("jobs", []):

        titre = job.get("title")

        if not titre:
            continue

        offre = {

            "titre": titre,

            "entreprise_source":
                job.get("company_name"),

            "ville":
                job.get(
                    "candidate_required_location"
                ),

            "adresse": "",

            "latitude": None,

            "longitude": None,

            "description":
                nettoyer_html(
                    job.get("description")
                ),

            "profil": "",

            "date_publication":
                job.get("publication_date"),

            "url_source":
                job.get("url"),

            "url_candidature":
                job.get("url"),

            "email_candidature": "",

            "source": "Remotive",

            "type":
                job.get("job_type"),

            "duree": "",

            "domaine":
                job.get("category")
        }

        if offre_valide(offre):

            offres.append(offre)

    return offres


# =========================================================
# INDEED RSS
# =========================================================

def fetch_indeed_rss():

    offres = []

    recherches = [
        "stage intelligence artificielle",
        "stage data analyst",
        "stage developpeur",
        "stage cybersécurité",
        "stage infrastructure"
    ]

    print("\nRecherche Indeed...")

    for recherche in recherches:

        url = (
            "https://ma.indeed.com/rss?"
            f"q={quote(recherche)}"
            "&l=Marrakech"
        )

        print(
            f"  → {recherche}"
        )

        try:

            response = requests.get(
                url,
                timeout=20,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 "
                        "(Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 "
                        "(KHTML, like Gecko) "
                        "Chrome/154.0 Safari/537.36"
                    )
                }
            )

            print(
                f"    HTTP {response.status_code}"
            )

            if response.status_code != 200:

                continue

            root = ET.fromstring(
                response.content
            )

            items = root.findall(
                ".//item"
            )

            print(
                f"    {len(items)} résultats reçus"
            )

            for item in items:

                def get_text(tag):

                    element = item.find(tag)

                    if element is None:
                        return ""

                    return (
                        element.text or ""
                    ).strip()

                titre = get_text("title")

                lien = get_text("link")

                description = nettoyer_html(
                    get_text("description")
                )

                date_publication = get_text(
                    "pubDate"
                )

                if not titre or not lien:

                    continue

                offre = {

                    "titre":
                        titre,

                    "entreprise_source":
                        "Non précisée",

                    "ville":
                        "Marrakech",

                    "adresse":
                        "",

                    "latitude":
                        None,

                    "longitude":
                        None,

                    "description":
                        description,

                    "profil":
                        "",

                    "date_publication":
                        date_publication,

                    "url_source":
                        lien,

                    "url_candidature":
                        lien,

                    "email_candidature":
                        "",

                    "source":
                        "Indeed",

                    "type":
                        "Stage",

                    "duree":
                        "",

                    "domaine":
                        ""
                }

                if offre_valide(offre):

                    offres.append(offre)

        except ET.ParseError:

            print(
                "    ✗ Réponse non XML"
            )

        except Exception as erreur:

            print(
                f"    ✗ Erreur : {erreur}"
            )

    return offres


# =========================================================
# IMPORT D'UNE SOURCE
# =========================================================

def importer_source(nom_source, offres):

    nouvelles = 0

    for offre in offres:

        if inserer_offre(offre):

            nouvelles += 1

    print(
        f"\n{nom_source} :"
    )

    print(
        f"  Offres valides : {len(offres)}"
    )

    print(
        f"  Nouvelles offres : {nouvelles}"
    )

    return nouvelles


# =========================================================
# IMPORT GLOBAL
# =========================================================

def importer_toutes_sources():

    print("=" * 65)

    print(
        "STAGEX - IMPORT DES OFFRES"
    )

    print("=" * 65)

    total_nouvelles = 0

    # =====================================================
    # REMOTIVE
    # =====================================================

    print(
        "\n[1/2] REMOTIVE"
    )

    try:

        offres_remotive = fetch_remotive()

        total_nouvelles += importer_source(
            "Remotive",
            offres_remotive
        )

    except Exception as erreur:

        print(
            "✗ Remotive :",
            erreur
        )

    # =====================================================
    # INDEED
    # =====================================================

    print(
        "\n[2/2] INDEED"
    )

    try:

        offres_indeed = fetch_indeed_rss()

        total_nouvelles += importer_source(
            "Indeed",
            offres_indeed
        )

    except Exception as erreur:

        print(
            "✗ Indeed :",
            erreur
        )

    # =====================================================
    # RESULTAT
    # =====================================================

    print("\n" + "=" * 65)

    print(
        f"✓ TOTAL nouvelles offres : {total_nouvelles}"
    )

    print(
        "\nFiltres StageX :"
    )

    print(
        "  ✓ Marrakech"
    )

    print(
        "  ✓ Stage / PFE / Internship"
    )

    print(
        "  ✓ Intelligence Artificielle"
    )

    print(
        "  ✓ Data Analyst"
    )

    print(
        "  ✓ Développement"
    )

    print(
        "  ✓ Infrastructure Digitale"
    )

    print(
        "  ✓ Cybersécurité"
    )

    print("=" * 65)


# =========================================================
# EXECUTION
# =========================================================

if __name__ == "__main__":

    importer_toutes_sources()
