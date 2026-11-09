# -*- coding: utf-8 -*-
"""
StageX-Marrakech - Accès SQLite pour l'import des offres.

Ne modifie PAS la table `offres` existante (mêmes colonnes, même schéma).
Ajoute seulement deux tables NOUVELLES :
  - offres_candidates : file d'attente des offres trouvées, pas encore publiées
  - offres_verification : trace de qui/quand/comment chaque offre publiée a été vérifiée
Le frontend et /api/offres continuent de lire uniquement `offres`.
"""

import os
import sqlite3
from datetime import datetime

from stagex_regles import NON_PRECISE, valeur

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.environ.get("STAGEX_DB", os.path.join(RACINE, "database", "stagex.db"))

COLONNES_OFFRE = [
    "titre", "entreprise_source", "ville", "adresse", "description", "profil",
    "date_publication", "url_source", "url_candidature", "email_candidature",
    "source", "type", "duree", "domaine",
]


def connexion():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def initialiser():
    con = connexion()
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS offres_candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titre TEXT, entreprise_source TEXT, ville TEXT, adresse TEXT,
            description TEXT, profil TEXT, date_publication TEXT,
            url_source TEXT UNIQUE, url_candidature TEXT, email_candidature TEXT,
            source TEXT, type TEXT, duree TEXT, domaine TEXT,
            trouve_par TEXT,              -- 'claude', 'jooble', 'manuel'
            statut TEXT DEFAULT 'en_attente',  -- en_attente / publiee / rejetee
            controle_auto TEXT,           -- résultat du contrôle de lien
            raisons_rejet TEXT,
            ajoute_le TEXT
        );
        CREATE TABLE IF NOT EXISTS offres_verification (
            offre_id INTEGER PRIMARY KEY,
            methode TEXT,                 -- 'humain' ou 'auto'
            controle_auto TEXT,
            verifie_le TEXT
        );
        """
    )
    con.commit()
    con.close()


def deja_connue(con, url):
    if con.execute("SELECT 1 FROM offres WHERE url_source = ?", (url,)).fetchone():
        return True
    return con.execute("SELECT 1 FROM offres_candidates WHERE url_source = ?", (url,)).fetchone() is not None


def ajouter_candidate(offre, trouve_par, controle_auto=""):
    """Ajoute une offre dans la file d'attente. Renvoie True si nouvelle."""
    con = connexion()
    try:
        if deja_connue(con, offre["url_source"]):
            return False
        donnees = {c: valeur(offre.get(c)) for c in COLONNES_OFFRE}
        donnees["url_source"] = offre["url_source"]
        donnees["trouve_par"] = trouve_par
        donnees["controle_auto"] = controle_auto
        donnees["ajoute_le"] = datetime.now().isoformat(timespec="seconds")
        cols = ", ".join(donnees)
        marques = ", ".join("?" for _ in donnees)
        con.execute(f"INSERT INTO offres_candidates ({cols}) VALUES ({marques})", list(donnees.values()))
        con.commit()
        return True
    finally:
        con.close()


def candidates_en_attente():
    con = connexion()
    lignes = [dict(r) for r in con.execute(
        "SELECT * FROM offres_candidates WHERE statut = 'en_attente' ORDER BY id")]
    con.close()
    return lignes


def publier(candidate_id, methode, controle_auto=""):
    """Copie une candidate dans la table `offres` (celle lue par /api/offres)."""
    con = connexion()
    try:
        c = con.execute("SELECT * FROM offres_candidates WHERE id = ?", (candidate_id,)).fetchone()
        if c is None:
            return None
        if con.execute("SELECT 1 FROM offres WHERE url_source = ?", (c["url_source"],)).fetchone():
            con.execute("UPDATE offres_candidates SET statut='publiee' WHERE id=?", (candidate_id,))
            con.commit()
            return None
        valeurs = [c[col] for col in COLONNES_OFFRE]
        # url_candidature : si inconnue, le bouton Postuler utilisera url_source
        idx = COLONNES_OFFRE.index("url_candidature")
        if valeurs[idx] == NON_PRECISE:
            valeurs[idx] = None
        idx = COLONNES_OFFRE.index("email_candidature")
        if valeurs[idx] == NON_PRECISE:
            valeurs[idx] = None
        cur = con.execute(
            f"INSERT INTO offres ({', '.join(COLONNES_OFFRE)}) VALUES ({', '.join('?' for _ in COLONNES_OFFRE)})",
            valeurs)
        offre_id = cur.lastrowid
        con.execute("INSERT OR REPLACE INTO offres_verification VALUES (?, ?, ?, ?)",
                    (offre_id, methode, controle_auto, datetime.now().isoformat(timespec="seconds")))
        con.execute("UPDATE offres_candidates SET statut='publiee' WHERE id=?", (candidate_id,))
        con.commit()
        return offre_id
    finally:
        con.close()


def rejeter(candidate_id, raison):
    con = connexion()
    con.execute("UPDATE offres_candidates SET statut='rejetee', raisons_rejet=? WHERE id=?",
                (raison, candidate_id))
    con.commit()
    con.close()


def offres_a_reverifier():
    """Offres publiées avec leur URL, pour le contrôle périodique des liens morts."""
    con = connexion()
    lignes = [dict(r) for r in con.execute("SELECT id, titre, url_source, source FROM offres")]
    con.close()
    return lignes


def depublier(offre_id):
    """Retire une offre expirée de `offres` (conservée dans offres_candidates, statut 'expiree')."""
    con = connexion()
    row = con.execute("SELECT url_source FROM offres WHERE id=?", (offre_id,)).fetchone()
    con.execute("DELETE FROM offres WHERE id=?", (offre_id,))
    con.execute("DELETE FROM offres_verification WHERE offre_id=?", (offre_id,))
    if row:
        con.execute("UPDATE offres_candidates SET statut='expiree' WHERE url_source=?", (row["url_source"],))
    con.commit()
    con.close()
