
# -*- coding: utf-8 -*-

"""
StageX-Marrakech
Gestion des utilisateurs et candidatures.
"""

import os
import sqlite3

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.environ.get(
    "STAGEX_DB",
    os.path.join(RACINE, "database", "stagex.db")
)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def connexion():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con

def initialiser_auth():
    con = connexion()

    con.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        prenom TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'etudiant',
        date_creation TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS candidatures (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        offre_id INTEGER NOT NULL,
        statut TEXT DEFAULT 'Envoyée',
        date_candidature TEXT DEFAULT CURRENT_TIMESTAMP,
        date_modification TEXT DEFAULT CURRENT_TIMESTAMP,
        message TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(offre_id) REFERENCES offres(id),
        UNIQUE(user_id, offre_id)
    );

    CREATE TABLE IF NOT EXISTS email_notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        candidature_id INTEGER,
        destinataire TEXT NOT NULL,
        sujet TEXT,
        statut TEXT DEFAULT 'en_attente',
        date_envoi TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(candidature_id) REFERENCES candidatures(id)
    );

    CREATE TABLE IF NOT EXISTS favoris (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        offre_id INTEGER NOT NULL,
        date_ajout TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(offre_id) REFERENCES offres(id),
        UNIQUE(user_id, offre_id)
    );
    """)
    
    con.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        candidature_id INTEGER,
        titre TEXT NOT NULL,
        message TEXT NOT NULL,
        lu INTEGER DEFAULT 0,
        date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(candidature_id) REFERENCES candidatures(id)
    )
    """)

    # Ajouter cv_path aux anciennes bases si nécessaire
    colonnes = con.execute("PRAGMA table_info(users)").fetchall()
    noms_colonnes = [col["name"] for col in colonnes]

    if "cv_path" not in noms_colonnes:
        con.execute("ALTER TABLE users ADD COLUMN cv_path TEXT")

    con.commit()
    con.close()

    
