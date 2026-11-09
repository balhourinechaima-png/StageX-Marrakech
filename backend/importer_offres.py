# -*- coding: utf-8 -*-
"""
StageX-Marrakech - Outil d'import des offres (ligne de commande).

Commandes :

  python backend\importer_offres.py test-regles
  python backend\importer_offres.py manuel
  python backend\importer_offres.py claude
  python backend\importer_offres.py claude --domaine "Cybersécurité"
  python backend\importer_offres.py jooble
  python backend\\importer_offres.py linkedin --max-offres 10
  python backend\importer_offres.py liste
  python backend\importer_offres.py valider
  python backend\importer_offres.py publier-auto
  python backend\importer_offres.py reverifier

Flux LinkedIn :

LinkedIn public Jobs
        ↓
source_linkedin.py
        ↓
règles StageX
        ↓
file d'attente candidates
        ↓
valider
        ↓
table offres
        ↓
site StageX-Marrakech
"""

import argparse
import glob
import json
import os
import sys
import webbrowser
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import stagex_db as db
import verifier_url
from stagex_regles import (
    DOMAINES,
    NON_PRECISE,
    analyser,
    extraire_duree,
    valeur
)

RACINE = db.RACINE
DOSSIER_MANUEL = os.path.join(
    RACINE,
    "data",
    "offres_manuelles"
)


# =========================================================
# ENVIRONNEMENT
# =========================================================

def charger_env():
    """
    Lit le fichier .env à la racine du projet.
    """

    chemin = os.path.join(
        RACINE,
        ".env"
    )

    if not os.path.exists(chemin):
        return

    with open(
        chemin,
        encoding="utf-8"
    ) as f:

        for ligne in f:

            ligne = ligne.strip()

            if (
                ligne
                and not ligne.startswith("#")
                and "=" in ligne
            ):

                k, v = ligne.split(
                    "=",
                    1
                )

                os.environ.setdefault(
                    k.strip(),
                    v.strip().strip('"').strip("'")
                )


# =========================================================
# SOURCE
# =========================================================

def nom_source(url):

    hote = urlparse(url).netloc.lower()

    sources = (
        ("indeed", "Indeed"),
        ("rekrute", "ReKrute"),
        ("emploi.ma", "Emploi.ma"),
        ("linkedin", "LinkedIn"),
        ("marocannonces", "MarocAnnonces"),
        ("jooble", "Jooble"),
        ("anapec", "ANAPEC"),
    )

    for cle, nom in sources:

        if cle in hote:
            return nom

    return (
        hote.replace("www.", "")
        or NON_PRECISE
    )


# =========================================================
# TRAITEMENT D'UNE OFFRE
# =========================================================

def traiter(
    offre,
    trouve_par,
    controler_lien=True
):
    """
    Applique les règles StageX puis
    ajoute l'offre à la file d'attente.
    """

    ok, raisons, domaine, typ = analyser(
        offre
    )

    titre = offre.get(
        "titre",
        "?"
    )

    # -----------------------------------------------------
    # Offre refusée par les règles
    # -----------------------------------------------------

    if not ok:

        print(
            f"   [REJET] "
            f"{titre[:70]} -> "
            f"{', '.join(raisons)}"
        )

        return False

    # -----------------------------------------------------
    # Informations StageX
    # -----------------------------------------------------

    offre["domaine"] = domaine
    offre["type"] = typ

    # -----------------------------------------------------
    # Durée
    # -----------------------------------------------------

    if valeur(
        offre.get("duree")
    ) == NON_PRECISE:

        offre["duree"] = extraire_duree(
            offre.get("description"),
            offre.get("profil")
        )

    # -----------------------------------------------------
    # Source
    # -----------------------------------------------------

    offre.setdefault(
        "source",
        nom_source(
            offre["url_source"]
        )
    )

    if valeur(
        offre.get("source")
    ) == NON_PRECISE:

        offre["source"] = nom_source(
            offre["url_source"]
        )

    # -----------------------------------------------------
    # Vérification URL
    # -----------------------------------------------------

    controle = ""

    if controler_lien:

        statut, detail = verifier_url.controler(
            offre["url_source"],
            titre
        )

        controle = f"{statut}: {detail}"

        if statut == verifier_url.MORT:

            print(
                f"   [REJET] "
                f"{titre[:70]} -> "
                f"lien mort ({detail})"
            )

            return False

    # -----------------------------------------------------
    # Ajouter dans candidates
    # -----------------------------------------------------

    if db.ajouter_candidate(
        offre,
        trouve_par,
        controle
    ):

        print(
            f"   [EN ATTENTE] "
            f"{titre[:70]} | "
            f"{domaine} | "
            f"{controle or 'non contrôlé'}"
        )

        return True

    print(
        f"   [DÉJÀ CONNUE] "
        f"{titre[:70]}"
    )

    return False


# =========================================================
# COMMANDE MANUELLE
# =========================================================

def cmd_manuel(_args):

    os.makedirs(
        DOSSIER_MANUEL,
        exist_ok=True
    )

    fichiers = sorted(
        glob.glob(
            os.path.join(
                DOSSIER_MANUEL,
                "*.txt"
            )
        )
        +
        glob.glob(
            os.path.join(
                DOSSIER_MANUEL,
                "*.json"
            )
        )
    )

    if not fichiers:

        print(
            f"Aucun fichier dans "
            f"{DOSSIER_MANUEL}."
        )

        return

    for chemin in fichiers:

        print(
            f"\n> {os.path.basename(chemin)}"
        )

        if chemin.endswith(".json"):

            with open(
                chemin,
                encoding="utf-8"
            ) as f:

                offre = json.load(f)

        else:

            with open(
                chemin,
                encoding="utf-8"
            ) as f:

                lignes = f.read().splitlines()

            url = (
                lignes[0].strip()
                if lignes
                else ""
            )

            texte = "\n".join(
                lignes[1:]
            ).strip()

            if (
                not url.startswith("http")
                or len(texte) < 50
            ):

                print(
                    "   [ERREUR] "
                    "1re ligne = URL de l'offre, "
                    "puis le texte complet."
                )

                continue

            import backend.source_claude as source_claude

            offre = source_claude.extraire(
                texte,
                url
            )

            if offre is None:

                print(
                    "   [REJET] "
                    "Claude n'a pas pu extraire "
                    "le titre."
                )

                continue

        traiter(
            offre,
            "manuel"
        )


# =========================================================
# CLAUDE
# =========================================================

def cmd_claude(args):

    import backend.source_claude as source_claude

    domaines = (
        [args.domaine]
        if args.domaine
        else DOMAINES
    )

    for d in domaines:

        print(
            f"\n=== Claude : {d} ==="
        )

        offres, stats = (
            source_claude.rechercher(d)
        )

        print(
            f"   {stats['proposees']} "
            f"proposée(s), "
            f"{stats['url_confirmees']} "
            f"avec URL confirmée"
        )

        for u in stats[
            "url_non_confirmees"
        ]:

            print(
                f"   [IGNORÉE] "
                f"URL absente des résultats réels : "
                f"{u}"
            )

        for o in offres:

            traiter(
                o,
                "claude"
            )


# =========================================================
# JOOBLE
# =========================================================

def cmd_jooble(args):

    import source_jooble

    domaines = (
        [args.domaine]
        if args.domaine
        else DOMAINES
    )

    for d in domaines:

        print(
            f"\n=== Jooble : {d} ==="
        )

        offres = source_jooble.rechercher(
            d
        )

        print(
            f"   {len(offres)} "
            f"résultat(s) brut(s)"
        )

        for o in offres:

            traiter(
                o,
                "jooble"
            )


# =========================================================
# LINKEDIN
# =========================================================

def cmd_linkedin(args):

    import source_linkedin

    print()
    print(
        "=================================================="
    )
    print(
        "       STAGEX - LINKEDIN SCRAPER"
    )
    print(
        "=================================================="
    )

    print()
    print(
        "🔎 Recherche des offres dans les 5 domaines..."
    )

    offres = source_linkedin.collecter_tous_domaines(
        localisation="Marrakech, Morocco",
        max_par_domaine=args.max_offres
    )

    print()
    print(
        f"📊 {len(offres)} offre(s) "
        "récupérée(s) depuis LinkedIn."
    )

    ajoutees = 0
    rejetees = 0

    for i, offre in enumerate(
        offres,
        start=1
    ):

        print()
        print(
            "----------------------------------------------"
        )

        print(
            f"🔹 Offre {i}/{len(offres)}"
        )

        print(
            f"   Titre : "
            f"{offre.get('titre', '')[:100]}"
        )

        print(
            f"   Entreprise : "
            f"{offre.get('entreprise', NON_PRECISE)}"
        )

        print(
            f"   Ville : "
            f"{offre.get('ville', NON_PRECISE)}"
        )

        offre_stagex = {

            "titre": offre.get(
                "titre",
                ""
            ),

            "entreprise_source": offre.get(
                "entreprise",
                NON_PRECISE
            ),

            "ville": offre.get(
                "ville",
                "Marrakech"
            ),

            "description": offre.get(
                "description",
                ""
            ),

            "date_publication": offre.get(
                "date_publication",
                NON_PRECISE
            ),

            "url_source": offre.get(
                "url",
                ""
            ),

            "source": "LinkedIn",

            "duree": NON_PRECISE,

            "profil": ""
        }

        print(
            "   🧠 Analyse avec les règles StageX..."
        )

        if traiter(
            offre_stagex,
            "linkedin",
            controler_lien=False
        ):

            ajoutees += 1

        else:

            rejetees += 1

    print()
    print(
        "=================================================="
    )

    print(
        "                 RÉSULTAT"
    )

    print(
        "=================================================="
    )

    print(
        f"✅ Ajoutées à la file : {ajoutees}"
    )

    print(
        f"❌ Rejetées : {rejetees}"
    )

    print()
    print(
        "➡️ Voir les offres en attente :"
    )

    print(
        "   python backend\\importer_offres.py liste"
    )

    print()
    print(
        "➡️ Valider les offres :"
    )

    print(
        "   python backend\\importer_offres.py valider"
    )

# =========================================================
# AFFICHAGE D'UNE CANDIDATE
# =========================================================

def _afficher(c):

    print()
    print(
        f"#{c['id']}  {c['titre']}"
    )

    for k in (
        "entreprise_source",
        "ville",
        "domaine",
        "type",
        "duree",
        "date_publication",
        "source"
    ):

        print(
            f"   {k:18}: {c[k]}"
        )

    print(
        f"   {'url_source':18}: "
        f"{c['url_source']}"
    )

    print(
        f"   {'contrôle auto':18}: "
        f"{c['controle_auto'] or 'non contrôlé'}"
    )

    print(
        f"   {'description':18}: "
        f"{(c['description'] or '')[:300]}"
    )


# =========================================================
# LISTE
# =========================================================

def cmd_liste(_args):

    cs = db.candidates_en_attente()

    print(
        f"{len(cs)} offre(s) en attente."
    )

    for c in cs:

        _afficher(c)


# =========================================================
# VALIDATION HUMAINE
# =========================================================

def cmd_valider(_args):

    cs = db.candidates_en_attente()

    if not cs:

        print(
            "Aucune offre en attente."
        )

        return

    print()
    print(
        "Pour chaque offre, "
        "le lien s'ouvre dans votre navigateur."
    )

    print(
        "Vérifiez : titre + entreprise + "
        "Marrakech + stage."
    )

    for c in cs:

        _afficher(c)

        webbrowser.open(
            c["url_source"]
        )

        rep = input(
            "\n   Publier ? "
            "[o]ui / "
            "[n]on / "
            "[p]asser / "
            "[q]uitter : "
        ).strip().lower()

        if rep == "o":

            oid = db.publier(
                c["id"],
                "humain",
                c["controle_auto"]
            )

            print(
                f"   -> publiée "
                f"(offres.id = {oid})"
            )

        elif rep == "n":

            raison = input(
                "   Raison (optionnel) : "
            ).strip()

            db.rejeter(
                c["id"],
                raison or "rejet manuel"
            )

            print(
                "   -> rejetée"
            )

        elif rep == "q":

            break


# =========================================================
# PUBLICATION AUTOMATIQUE
# =========================================================

def cmd_publier_auto(_args):

    n = 0

    for c in db.candidates_en_attente():

        if (
            c["controle_auto"] or ""
        ).startswith(
            verifier_url.OK + ":"
        ):

            oid = db.publier(
                c["id"],
                "auto",
                c["controle_auto"]
            )

            if oid:

                n += 1

                print(
                    f"   publiée : "
                    f"{c['titre'][:70]} "
                    f"(offres.id = {oid})"
                )

    print(
        f"{n} offre(s) publiée(s). "
        "Les autres attendent `valider`."
    )


# =========================================================
# REVERIFICATION
# =========================================================

def cmd_reverifier(_args):

    for o in db.offres_a_reverifier():

        if not (
            o["url_source"] or ""
        ).startswith("http"):

            continue

        statut, detail = (
            verifier_url.controler(
                o["url_source"],
                o["titre"]
            )
        )

        print(
            f"   [{statut}] "
            f"#{o['id']} "
            f"{o['titre'][:60]} "
            f"({detail})"
        )

        if statut == verifier_url.MORT:

            db.depublier(
                o["id"]
            )

            print(
                "      -> retirée du site "
                "(offre expirée)"
            )


# =========================================================
# TEST DES RÈGLES
# =========================================================

def cmd_test_regles(_args):

    cas = [

        (
            {
                "titre": "Stage PFE Data Analyst",
                "ville": "Marrakech",
                "description": "Power BI, SQL. Durée 6 mois.",
                "url_source": "https://exemple.test/1"
            },
            True
        ),

        (
            {
                "titre": "Stagiaire Développeur Full Stack",
                "ville": "Marrakech, Marrakech-Safi",
                "description": "React et Node.js",
                "url_source": "https://exemple.test/2"
            },
            True
        ),

        (
            {
                "titre": "Stage SOC analyste",
                "ville": "Marrakech",
                "description": "",
                "url_source": "https://exemple.test/3"
            },
            True
        ),

        (
            {
                "titre": "Stage Marketing digital",
                "ville": "Marrakech",
                "description": "réseaux sociaux",
                "url_source": "https://exemple.test/4"
            },
            False
        ),

        (
            {
                "titre": "Data Analyst (CDI)",
                "ville": "Marrakech",
                "description": "",
                "url_source": "https://exemple.test/5"
            },
            False
        ),

        (
            {
                "titre": "Stage Développeur",
                "ville": "Casablanca",
                "description": "",
                "url_source": "https://exemple.test/6"
            },
            False
        ),

        (
            {
                "titre": "Stage assistant commercial",
                "ville": "Marrakech",
                "description": "J'ai besoin d'une personne pour la société",
                "url_source": "https://exemple.test/7"
            },
            False
        ),
    ]

    attendus_domaine = {
        1: "Data Analyst",
        2: "Développement",
        3: "Cybersécurité"
    }

    erreurs = 0

    for i, (offre, attendu) in enumerate(
        cas,
        1
    ):

        ok, raisons, domaine, typ = (
            analyser(offre)
        )

        bon = (
            ok == attendu
            and (
                not ok
                or attendus_domaine.get(i)
                in (None, domaine)
            )
        )

        erreurs += not bon

        print(
            f"{'OK ' if bon else 'ÉCHEC'} | "
            f"{offre['titre']:<40} "
            f"accepte={ok} "
            f"domaine={domaine} "
            f"type={typ} "
            f"{raisons}"
        )

    print()

    print(
        "Durée extraite du cas 1 : "
        f"{extraire_duree(cas[0][0]['description'])}"
    )

    if erreurs == 0:

        print(
            "TOUS LES TESTS PASSENT"
        )

    else:

        print(
            f"{erreurs} TEST(S) EN ÉCHEC"
        )


# =========================================================
# MAIN
# =========================================================

def main():

    if hasattr(
        sys.stdout,
        "reconfigure"
    ):

        sys.stdout.reconfigure(
            encoding="utf-8"
        )

    charger_env()

    p = argparse.ArgumentParser(
        description=(
            "Import des offres "
            "StageX-Marrakech"
        )
    )

    # -----------------------------------------------------
    # Commande principale
    # -----------------------------------------------------

    p.add_argument(
        "commande",
        choices=[
            "test-regles",
            "manuel",
            "claude",
            "jooble",
            "linkedin",
            "liste",
            "valider",
            "publier-auto",
            "reverifier"
        ]
    )

    # -----------------------------------------------------
    # Domaine
    # -----------------------------------------------------

    p.add_argument(
        "--domaine",
        choices=DOMAINES
    )

    # -----------------------------------------------------
    # Nombre d'offres LinkedIn
    # -----------------------------------------------------

    p.add_argument(
        "--max-offres",
        type=int,
        default=10,
        help=(
            "Nombre maximum "
            "d'offres LinkedIn à récupérer"
        )
    )

    args = p.parse_args()

    # -----------------------------------------------------
    # Initialiser DB
    # -----------------------------------------------------

    if args.commande != "test-regles":

        db.initialiser()

    # -----------------------------------------------------
    # Dispatcher
    # -----------------------------------------------------

    commandes = {

        "test-regles": cmd_test_regles,

        "manuel": cmd_manuel,

        "claude": cmd_claude,

        "jooble": cmd_jooble,

        "linkedin": cmd_linkedin,

        "liste": cmd_liste,

        "valider": cmd_valider,

        "publier-auto": cmd_publier_auto,

        "reverifier": cmd_reverifier
    }

    commandes[
        args.commande
    ](args)


# =========================================================
# START
# =========================================================

if __name__ == "__main__":
    main()