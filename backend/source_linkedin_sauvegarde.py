# -*- coding: utf-8 -*-

from playwright.sync_api import sync_playwright
from urllib.parse import quote
import time


BASE_URL = "https://www.linkedin.com/jobs/search/"


# =========================================================
# DOMAINES STAGEX
# =========================================================

DOMAINES_RECHERCHE = [
    "stage intelligence artificielle",
    "stage data analyst",
    "stage développeur",
    "stage infrastructure informatique",
    "stage cybersécurité"
]


# =========================================================
# RECHERCHE LINKEDIN
# =========================================================

def rechercher_offres(
    mots_cles="stage",
    localisation="Marrakech, Morocco",
    max_offres=10
):

    offres = []

    url = (
        BASE_URL
        + "?keywords="
        + quote(mots_cles)
        + "&location="
        + quote(localisation)
    )

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page(
            viewport={
                "width": 1366,
                "height": 900
            }
        )

        try:

            print(
                f"\n🔎 Recherche LinkedIn : {mots_cles}"
            )

            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=30000
            )

            page.wait_for_timeout(5000)

            print(
                "📄 Page :",
                page.title()
            )

            links = page.locator("a")

            urls_vues = set()

            for i in range(
                links.count()
            ):

                href = links.nth(
                    i
                ).get_attribute(
                    "href"
                )

                titre = links.nth(
                    i
                ).inner_text().strip()

                if not href:
                    continue

                if "/jobs/view/" not in href:
                    continue

                href = href.split("?")[0]

                if href in urls_vues:
                    continue

                urls_vues.add(href)

                if not titre:
                    continue

                offres.append(
                    {
                        "titre": titre,
                        "url": href,
                        "source": "LinkedIn"
                    }
                )

                if len(offres) >= max_offres:
                    break

            print(
                f"✅ {len(offres)} offre(s) trouvée(s)"
            )

        except Exception as e:

            print(
                "❌ Erreur recherche LinkedIn :",
                e
            )

        finally:

            browser.close()

    return offres


# =========================================================
# DETAILS D'UNE OFFRE
# =========================================================

def recuperer_details_offre(url):

    resultat = {

        "titre": "",

        "entreprise": "",

        "ville": "",

        "description": "",

        "date_publication": "",

        "url": url,

        "source": "LinkedIn"
    }

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page(
            viewport={
                "width": 1366,
                "height": 900
            }
        )

        try:

            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=30000
            )

            page.wait_for_timeout(
                4000
            )

            # -------------------------------------------------
            # TITRE
            # -------------------------------------------------

            h1 = page.locator("h1")

            if h1.count() > 0:

                resultat["titre"] = (
                    h1.first
                    .inner_text()
                    .strip()
                )

            # -------------------------------------------------
            # ENTREPRISE
            # -------------------------------------------------

            selectors_entreprise = [

                ".topcard__org-name-link",

                ".topcard__flavor",

                "a.topcard__org-name-link",

                ".job-details-jobs-unified-top-card__company-name"
            ]

            for selector in selectors_entreprise:

                loc = page.locator(
                    selector
                )

                if loc.count() > 0:

                    valeur = (
                        loc.first
                        .inner_text()
                        .strip()
                    )

                    if valeur:

                        resultat[
                            "entreprise"
                        ] = valeur

                        break

            # -------------------------------------------------
            # VILLE
            # -------------------------------------------------

            selectors_lieu = [

                ".topcard__flavor--bullet",

                ".job-details-jobs-unified-top-card__primary-description-container",

                ".top-card-layout__second-subline"
            ]

            for selector in selectors_lieu:

                loc = page.locator(
                    selector
                )

                if loc.count() > 0:

                    valeur = (
                        loc.first
                        .inner_text()
                        .strip()
                    )

                    if valeur:

                        resultat[
                            "ville"
                        ] = valeur

                        break

            # -------------------------------------------------
            # DESCRIPTION
            # -------------------------------------------------

            selectors_description = [

                ".description__text",

                ".show-more-less-html__markup",

                ".jobs-description__content",

                ".jobs-box__html-content"
            ]

            for selector in selectors_description:

                loc = page.locator(
                    selector
                )

                if loc.count() > 0:

                    valeur = (
                        loc.first
                        .inner_text()
                        .strip()
                    )

                    if valeur:

                        resultat[
                            "description"
                        ] = valeur

                        break

            # -------------------------------------------------
            # FALLBACK DESCRIPTION
            # -------------------------------------------------

            if not resultat["description"]:

                resultat[
                    "description"
                ] = page.locator(
                    "body"
                ).inner_text()[:10000]

            print(
                "\n----------------------------------------"
            )

            print(
                "OFFRE"
            )

            print(
                "----------------------------------------"
            )

            print(
                "Titre :",
                resultat["titre"]
            )

            print(
                "Entreprise :",
                resultat["entreprise"]
            )

            print(
                "Ville :",
                resultat["ville"]
            )

            print(
                "URL :",
                resultat["url"]
            )

            print(
                "----------------------------------------"
            )

        except Exception as e:

            print(
                "❌ Erreur détail offre :",
                e
            )

        finally:

            browser.close()

    return resultat


# =========================================================
# COLLECTE
# =========================================================

def collecter_offres(
    mots_cles="stage",
    localisation="Marrakech, Morocco",
    max_offres=10
):

    offres_base = rechercher_offres(
        mots_cles=mots_cles,
        localisation=localisation,
        max_offres=max_offres
    )

    offres_finales = []

    for i, offre in enumerate(
        offres_base,
        start=1
    ):

        print(
            f"\n🔹 Traitement offre "
            f"{i}/{len(offres_base)}"
        )

        details = recuperer_details_offre(
            offre["url"]
        )

        if not details["titre"]:

            details["titre"] = (
                offre["titre"]
            )

        offres_finales.append(
            details
        )

        time.sleep(1)

    return offres_finales


# =========================================================
# RECHERCHE DES 5 DOMAINES
# =========================================================

def collecter_tous_domaines(
    localisation="Marrakech, Morocco",
    max_par_domaine=5
):

    toutes_les_offres = []

    urls_vues = set()

    for domaine in DOMAINES_RECHERCHE:

        print()
        print(
            "================================================"
        )

        print(
            f"🎯 DOMAINE : {domaine}"
        )

        print(
            "================================================"
        )

        offres = collecter_offres(
            mots_cles=domaine,
            localisation=localisation,
            max_offres=max_par_domaine
        )

        for offre in offres:

            url = offre.get(
                "url",
                ""
            )

            if url in urls_vues:

                continue

            urls_vues.add(
                url
            )

            offre[
                "domaine_recherche"
            ] = domaine

            toutes_les_offres.append(
                offre
            )

    print()
    print(
        "================================================"
    )

    print(
        "📊 TOTAL"
    )

    print(
        f"✅ {len(toutes_les_offres)} "
        "offre(s) récupérée(s)"
    )

    print(
        "================================================"
    )

    return toutes_les_offres


# =========================================================
# TEST DIRECT
# =========================================================

if __name__ == "__main__":

    print()
    print(
        "🚀 STAGEX - SCRAPER LINKEDIN"
    )

    print(
        "Recherche des 5 domaines..."
    )

    offres = collecter_tous_domaines(
        localisation="Marrakech, Morocco",
        max_par_domaine=3
    )

    print()
    print(
        "=============================="
    )

    print(
        "RÉSULTAT FINAL"
    )

    print(
        "=============================="
    )

    for i, offre in enumerate(
        offres,
        start=1
    ):

        print()
        print(
            f"OFFRE {i}"
        )

        print(
            "Titre :",
            offre["titre"]
        )

        print(
            "Entreprise :",
            offre["entreprise"]
        )

        print(
            "Ville :",
            offre["ville"]
        )

        print(
            "Domaine recherché :",
            offre.get(
                "domaine_recherche",
                ""
            )
        )

        print(
            "URL :",
            offre["url"]
        )

# =========================================================
# RECHERCHE DANS LES 5 DOMAINES STAGEX
# =========================================================

DOMAINES_RECHERCHE = [
    "stage intelligence artificielle",
    "stage data analyst",
    "stage développeur",
    "stage infrastructure informatique",
    "stage cybersécurité"
]
