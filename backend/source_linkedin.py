# =========================================================
# STAGEX MARRAKECH
# SOURCE LINKEDIN - PUBLIC JOBS SCRAPER
# =========================================================

from playwright.sync_api import sync_playwright
from urllib.parse import quote
import time


BASE_URL = "https://www.linkedin.com/jobs/search/"


def rechercher_offres(
    mots_cles="stage",
    localisation="Marrakech, Morocco",
    max_offres=30
):
    """
    Recherche des offres publiques sur LinkedIn
    via la page de recherche Jobs.
    """

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
            print("🔎 Ouverture de LinkedIn...")
            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=30000
            )

            page.wait_for_timeout(5000)

            print("📄 Page :", page.title())

            # -------------------------------------------------
            # Récupération des liens vers les offres
            # -------------------------------------------------

            links = page.locator("a")

            urls_vues = set()

            for i in range(links.count()):

                href = links.nth(i).get_attribute("href")
                titre = links.nth(i).inner_text().strip()

                if not href:
                    continue

                if "/jobs/view/" not in href:
                    continue

                # Nettoyage URL
                href = href.split("?")[0]

                if href in urls_vues:
                    continue

                urls_vues.add(href)

                if not titre:
                    continue

                offres.append({
                    "titre": titre,
                    "url": href,
                    "source": "LinkedIn"
                })

                if len(offres) >= max_offres:
                    break

            print(
                f"✅ {len(offres)} offres trouvées dans la recherche."
            )

        except Exception as e:

            print("❌ Erreur recherche LinkedIn :", e)

        finally:
            browser.close()

    return offres


def recuperer_details_offre(url):

    """
    Ouvre une offre LinkedIn publique
    et récupère les informations disponibles.
    """

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

            page.wait_for_timeout(4000)

            # -------------------------------------------------
            # TITRE
            # -------------------------------------------------

            h1 = page.locator("h1")

            if h1.count() > 0:
                resultat["titre"] = (
                    h1.first.inner_text().strip()
                )

            # -------------------------------------------------
            # Texte général
            # -------------------------------------------------

            texte = page.locator("body").inner_text()

            # -------------------------------------------------
            # ENTREPRISE
            # -------------------------------------------------

            selectors_entreprise = [
                ".topcard__org-name-link",
                ".topcard__flavor",
                "a.topcard__org-name-link"
            ]

            for selector in selectors_entreprise:

                loc = page.locator(selector)

                if loc.count() > 0:

                    valeur = loc.first.inner_text().strip()

                    if valeur:
                        resultat["entreprise"] = valeur
                        break

            # -------------------------------------------------
            # LOCALISATION
            # -------------------------------------------------

            selectors_lieu = [
                ".topcard__flavor--bullet",
                ".job-details-jobs-unified-top-card__primary-description-container"
            ]

            for selector in selectors_lieu:

                loc = page.locator(selector)

                if loc.count() > 0:

                    valeur = loc.first.inner_text().strip()

                    if valeur:
                        resultat["ville"] = valeur
                        break

            # -------------------------------------------------
            # DESCRIPTION
            # -------------------------------------------------

            selectors_description = [
                ".description__text",
                ".show-more-less-html__markup",
                ".jobs-description__content"
            ]

            for selector in selectors_description:

                loc = page.locator(selector)

                if loc.count() > 0:

                    valeur = loc.first.inner_text().strip()

                    if valeur:
                        resultat["description"] = valeur
                        break

            # -------------------------------------------------
            # Fallback
            # -------------------------------------------------

            if not resultat["description"]:
                resultat["description"] = texte[:10000]

            print("\n----------------------------------------")
            print("OFFRE")
            print("----------------------------------------")
            print("Titre :", resultat["titre"])
            print("Entreprise :", resultat["entreprise"])
            print("Ville :", resultat["ville"])
            print("URL :", resultat["url"])
            print("----------------------------------------")

        except Exception as e:

            print("❌ Erreur détail offre :", e)

        finally:
            browser.close()

    return resultat


def collecter_offres(
    mots_cles="stage",
    localisation="Marrakech, Morocco",
    max_offres=10
):

    """
    Pipeline complet :
    recherche → récupération des détails.
    """

    offres_base = rechercher_offres(
        mots_cles=mots_cles,
        localisation=localisation,
        max_offres=max_offres
    )

    offres_finales = []

    for i, offre in enumerate(offres_base, start=1):

        print(
            f"\n🔹 Traitement offre {i}/{len(offres_base)}"
        )

        details = recuperer_details_offre(
            offre["url"]
        )

        # Si le titre détaillé n'est pas trouvé,
        # on garde celui de la recherche.
        if not details["titre"]:
            details["titre"] = offre["titre"]

        offres_finales.append(details)

        time.sleep(1)

    return offres_finales


# =========================================================
# TEST DIRECT
# =========================================================

if __name__ == "__main__":

    print("\n🚀 STAGEX - TEST SCRAPER LINKEDIN\n")

    offres = collecter_offres(
        mots_cles="stage",
        localisation="Marrakech, Morocco",
        max_offres=5
    )

    print("\n\n==============================")
    print("RÉSULTAT FINAL")
    print("==============================")

    for i, offre in enumerate(offres, start=1):

        print(f"\nOFFRE {i}")
        print("Titre :", offre["titre"])
        print("Entreprise :", offre["entreprise"])
        print("Ville :", offre["ville"])
        print("Source :", offre["source"])
        print("URL :", offre["url"])

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


def collecter_tous_domaines(
    localisation="Marrakech, Morocco",
    max_par_domaine=5
):

    toutes_les_offres = []
    urls_vues = set()

    for domaine in DOMAINES_RECHERCHE:

        print()
        print("=" * 55)
        print(f"🔎 Domaine : {domaine}")
        print("=" * 55)

        offres = collecter_offres(
            mots_cles=domaine,
            localisation=localisation,
            max_offres=max_par_domaine
        )

        for offre in offres:

            url = offre.get("url", "")

            if not url:
                continue

            if url in urls_vues:
                continue

            urls_vues.add(url)

            offre["domaine_recherche"] = domaine

            toutes_les_offres.append(offre)

    return toutes_les_offres