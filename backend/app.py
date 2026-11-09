from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

load_dotenv(os.path.join(BASE_DIR, ".env"))

from flask import session
from werkzeug.security import generate_password_hash, check_password_hash
from auth_db import connexion, initialiser_auth

from flask import send_file
from werkzeug.utils import secure_filename
import csv
import io
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

if not app.secret_key:
    raise RuntimeError("SECRET_KEY manquante dans le fichier .env")

CORS(
    app,
    supports_credentials=True,
    origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:5000",
        "http://localhost:5000"
    ]
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.environ.get(
    "STAGEX_DB",
    os.path.join(BASE_DIR, "database", "stagex.db")
)
initialiser_auth()

# =========================================================
# CONNEXION DATABASE
# =========================================================

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# =========================================================
# PAGE ACCUEIL API
# =========================================================

@app.route("/")
def home():

    return jsonify({
        "message": "Bienvenue sur l'API StageX-Marrakech",
        "status": "Backend opérationnel"
    })


# =========================================================
# STATS
# =========================================================

@app.route("/api/stats")
def stats():

    conn = get_db_connection()

    total = conn.execute(
        "SELECT COUNT(*) AS total FROM entreprises"
    ).fetchone()["total"]

    niveaux = conn.execute("""
        SELECT niveau_stage, COUNT(*) AS nombre
        FROM entreprises
        GROUP BY niveau_stage
    """).fetchall()

    total_offres = conn.execute(
        "SELECT COUNT(*) AS total FROM offres"
    ).fetchone()["total"]

    conn.close()

    return jsonify({

        "total_entreprises": total,

        "total_offres": total_offres,

        "niveaux": [
            {
                "niveau": row["niveau_stage"],
                "nombre": row["nombre"]
            }
            for row in niveaux
        ]
    })


# =========================================================
# ENTREPRISES
# =========================================================

@app.route("/api/entreprises")
def entreprises():

    conn = get_db_connection()

    query = """
        SELECT
            id,
            google_id,
            nom,
            adresse,
            latitude,
            longitude,
            note,
            nombre_avis,
            google_maps,
            domaine,
            domaines_stage_potentiel,
            score_stage,
            niveau_stage
        FROM entreprises
        ORDER BY score_stage DESC
    """

    rows = conn.execute(query).fetchall()

    conn.close()

    return jsonify([
        dict(row)
        for row in rows
    ])


# =========================================================
# RECHERCHE ENTREPRISES
# =========================================================

@app.route("/api/recherche")
def recherche():

    mot = request.args.get(
        "q",
        ""
    ).strip()

    conn = get_db_connection()

    query = """
        SELECT *
        FROM entreprises
        WHERE
            nom LIKE ?
            OR adresse LIKE ?
            OR domaine LIKE ?
            OR domaines_stage_potentiel LIKE ?
        ORDER BY score_stage DESC
    """

    pattern = f"%{mot}%"

    rows = conn.execute(
        query,
        (
            pattern,
            pattern,
            pattern,
            pattern
        )
    ).fetchall()

    conn.close()

    return jsonify([
        dict(row)
        for row in rows
    ])


# =========================================================
# DETAIL ENTREPRISE
# =========================================================

@app.route("/api/entreprises/<int:entreprise_id>")
def detail_entreprise(entreprise_id):

    conn = get_db_connection()

    row = conn.execute(
        """
        SELECT *
        FROM entreprises
        WHERE id = ?
        """,
        (entreprise_id,)
    ).fetchone()

    conn.close()

    if row is None:

        return jsonify({
            "error": "Entreprise introuvable"
        }), 404

    return jsonify(dict(row))


# =========================================================
# DOMAINES STAGEX
# =========================================================

DOMAINES_CIBLES = {

    "ia": [
        "artificial intelligence",
        "intelligence artificielle",
        "machine learning",
        "deep learning",
        "ai",
        "ml",
        "computer vision",
        "nlp",
        "natural language processing"
    ],

    "data": [
        "data analyst",
        "data analysis",
        "data analytics",
        "data science",
        "data scientist",
        "business intelligence",
        "analytics"
    ],

    "dev": [
        "development",
        "developer",
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
        "programming"
    ],

    "infrastructure": [
        "infrastructure",
        "infrastructure digitale",
        "it infrastructure",
        "systems",
        "system administration",
        "system administrator",
        "network",
        "networking",
        "networks",
        "cloud",
        "cloud computing",
        "devops",
        "linux",
        "servers"
    ],

    "cyber": [
        "cybersecurity",
        "cyber security",
        "cybersécurité",
        "security",
        "information security",
        "network security",
        "soc",
        "ethical hacking",
        "penetration testing",
        "pentest"
    ]
}


# =========================================================
# MOTS POUR IDENTIFIER UN STAGE / PFE
# =========================================================

MOTS_STAGE = [

    "intern",
    "internship",
    "stage",
    "stagiaire",
    "trainee",
    "pfe",
    "end of studies",
    "end-of-studies",
    "final year project"
]


# =========================================================
# OFFRES + FILTRES
# =========================================================

@app.route("/api/offres")
def offres():

    ville = request.args.get(
        "ville",
        ""
    ).strip().lower()

    type_offre = request.args.get(
        "type",
        ""
    ).strip().lower()

    domaine = request.args.get(
        "domaine",
        ""
    ).strip().lower()

    recherche = request.args.get(
        "q",
        ""
    ).strip().lower()


    conn = get_db_connection()


    # -----------------------------------------------------
    # RÉCUPÉRER LES OFFRES
    # -----------------------------------------------------

    rows = conn.execute("""
        SELECT *
        FROM offres
        ORDER BY id DESC
    """).fetchall()

    conn.close()


    offres_filtrees = []


    # =====================================================
    # FILTRAGE
    # =====================================================

    for row in rows:

        offre = dict(row)


        titre = str(
            offre.get("titre") or ""
        ).lower()


        description = str(
            offre.get("description") or ""
        ).lower()


        offre_domaine = str(
            offre.get("domaine") or ""
        ).lower()


        offre_ville = str(
            offre.get("ville") or ""
        ).lower()


        offre_adresse = str(
            offre.get("adresse") or ""
        ).lower()


        offre_type = str(
            offre.get("type") or ""
        ).lower()


        entreprise = str(
            offre.get("entreprise_source") or ""
        ).lower()


        # Texte utilisé pour détecter le domaine
        texte_complet = " ".join([

            titre,

            description,

            offre_domaine
        ])


        # =================================================
        # 1. DÉTECTER LE DOMAINE
        # =================================================

        domaine_trouve = None


        for domaine_nom, mots in DOMAINES_CIBLES.items():

            if any(
                mot in texte_complet
                for mot in mots
            ):

                domaine_trouve = domaine_nom

                break


        # Pas de domaine StageX
        if domaine_trouve is None:

            continue


        # =================================================
        # 2. VÉRIFIER STAGE / PFE
        # =================================================

        stage_trouve = any(

            mot in texte_complet

            for mot in MOTS_STAGE

        )


        if not stage_trouve:

            continue


        # =================================================
        # 3. FILTRE VILLE
        # =================================================

        if ville and ville != "all":

            texte_ville = " ".join([

                offre_ville,

                offre_adresse

            ])


            if ville not in texte_ville:

                continue


        # =================================================
        # 4. FILTRE TYPE
        # =================================================

        if type_offre and type_offre != "all":

            if type_offre == "stage":

                if not stage_trouve:

                    continue

            else:

                if type_offre not in offre_type:

                    continue


        # =================================================
        # 5. FILTRE DOMAINE
        # =================================================

        if domaine and domaine != "all":

            mots_recherche = DOMAINES_CIBLES.get(

                domaine,

                [domaine]

            )


            if not any(

                mot in texte_complet

                for mot in mots_recherche

            ):

                continue


        # =================================================
        # 6. RECHERCHE
        # =================================================

        if recherche:

            texte_recherche = " ".join([

                titre,

                description,

                offre_domaine,

                offre_ville,

                entreprise

            ])


            if recherche not in texte_recherche:

                continue


        # =================================================
        # 7. AJOUT DU DOMAINE STAGEX
        # =================================================

        noms_domaines = {

            "ia":
                "Intelligence Artificielle",

            "data":
                "Data Analyst",

            "dev":
                "Développement",

            "infrastructure":
                "Infrastructure Digitale",

            "cyber":
                "Cybersécurité"
        }


        offre["domaine_stagex"] = noms_domaines.get(

            domaine_trouve,

            domaine_trouve

        )


        offres_filtrees.append(offre)


    # =====================================================
    # RÉSULTAT
    # =====================================================

    return jsonify(
        offres_filtrees
    )


# =========================================================
# DETAIL OFFRE
# =========================================================

@app.route("/api/offres/<int:offre_id>")
def detail_offre(offre_id):

    conn = get_db_connection()

    row = conn.execute("""
        SELECT *
        FROM offres
        WHERE id = ?
    """, (offre_id,)).fetchone()

    conn.close()


    if row is None:

        return jsonify({
            "error": "Offre introuvable"
        }), 404


    return jsonify(
        dict(row)
    )

# =========================================================
# PROTECTION ADMIN
# =========================================================

def verifier_admin():
    user_id = session.get("user_id")

    if not user_id:
        return None, (jsonify({"error": "Connexion obligatoire"}), 401)

    con = connexion()

    try:
        user = con.execute("""
            SELECT id, nom, prenom, email, role
            FROM users
            WHERE id = ?
        """, (user_id,)).fetchone()
    finally:
        con.close()

    if user is None:
        return None, (jsonify({"error": "Utilisateur introuvable"}), 401)

    if user["role"] != "admin":
        return None, (jsonify({"error": "Accès réservé à l'administration"}), 403)

    return dict(user), None

# =========================================================
# AUTHENTIFICATION
# =========================================================

@app.route("/api/auth/register", methods=["POST"])
def register():

    data = request.get_json(silent=True) or {}

    nom = data.get("nom", "").strip()
    prenom = data.get("prenom", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not nom or not prenom or not email or not password:
        return jsonify({"error": "Tous les champs sont obligatoires"}), 400

    if len(password) < 8:
        return jsonify({
            "error": "Le mot de passe doit contenir au moins 8 caractères"
        }), 400

    password_hash = generate_password_hash(password)

    con = connexion()

    try:
        cur = con.execute("""
            INSERT INTO users (nom, prenom, email, password_hash)
            VALUES (?, ?, ?, ?)
        """, (nom, prenom, email, password_hash))

        user_id = cur.lastrowid
        con.commit()

        session.clear()
        session["user_id"] = user_id

        return jsonify({
            "message": "Compte créé avec succès",
            "user": {
                "id": user_id,
                "nom": nom,
                "prenom": prenom,
                "email": email
            }
        }), 201

    except sqlite3.IntegrityError:
        return jsonify({
            "error": "Cette adresse email est déjà utilisée"
        }), 409

    finally:
        con.close()


@app.route("/api/auth/login", methods=["POST"])
def login():

    data = request.get_json(silent=True) or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    con = connexion()

    try:
        user = con.execute("""
            SELECT *
            FROM users
            WHERE email = ?
        """, (email,)).fetchone()

        if user is None or not check_password_hash(
            user["password_hash"], password
        ):
            return jsonify({
                "error": "Email ou mot de passe incorrect"
            }), 401

        session.clear()
        session["user_id"] = user["id"]

        return jsonify({
            "message": "Connexion réussie",
            "user": {
                "id": user["id"],
                "nom": user["nom"],
                "prenom": user["prenom"],
                "email": user["email"]
            }
        })

    finally:
        con.close()


@app.route("/api/auth/me")
def current_user():

    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Non connecté"}), 401

    con = connexion()

    try:
        user = con.execute("""
            SELECT id, nom, prenom, email, role
            FROM users
            WHERE id = ?
        """, (user_id,)).fetchone()

        if user is None:
            session.clear()
            return jsonify({"error": "Utilisateur introuvable"}), 401

        return jsonify(dict(user))

    finally:
        con.close()


@app.route("/api/auth/logout", methods=["POST"])
def logout():

    session.clear()

    return jsonify({
        "message": "Déconnexion réussie"
    })


# =========================================================
# CANDIDATURES
# =========================================================

@app.route("/api/candidatures", methods=["GET", "POST"])
def candidatures():

    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Veuillez vous connecter"}), 401

    con = connexion()

    try:

        # Afficher les candidatures du étudiant connecté
        if request.method == "GET":

            rows = con.execute("""
                SELECT
                    c.id,
                    c.offre_id,
                    c.statut,
                    c.date_candidature,
                    c.date_modification,
                    c.message,
                    o.titre,
                    o.entreprise_source,
                    o.ville,
                    o.url_source
                FROM candidatures c
                JOIN offres o ON o.id = c.offre_id
                WHERE c.user_id = ?
                ORDER BY c.date_candidature DESC
            """, (user_id,)).fetchall()

            return jsonify([dict(row) for row in rows])

        # Ajouter une candidature
        data = request.get_json(silent=True) or {}

        offre_id = data.get("offre_id")
        message = data.get("message", "").strip()

        if not offre_id:
            return jsonify({"error": "offre_id obligatoire"}), 400

        offre = con.execute("""
            SELECT id FROM offres WHERE id = ?
        """, (offre_id,)).fetchone()

        if offre is None:
            return jsonify({"error": "Offre introuvable"}), 404

        cur = con.execute("""
            INSERT INTO candidatures
            (user_id, offre_id, statut, message)
            VALUES (?, ?, 'Envoyée', ?)
        """, (user_id, offre_id, message))

        con.commit()

        return jsonify({
            "message": "Candidature enregistrée avec succès",
            "candidature_id": cur.lastrowid
        }), 201

    except sqlite3.IntegrityError:

        return jsonify({
            "error": "Vous avez déjà postulé à cette offre"
        }), 409

    finally:
        con.close()


@app.route("/api/candidatures/<int:candidature_id>")
def detail_candidature(candidature_id):

    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Veuillez vous connecter"}), 401

    con = connexion()

    try:

        row = con.execute("""
            SELECT
                c.*,
                o.titre,
                o.entreprise_source,
                o.ville
            FROM candidatures c
            JOIN offres o ON o.id = c.offre_id
            WHERE c.id = ? AND c.user_id = ?
        """, (candidature_id, user_id)).fetchone()

        if row is None:
            return jsonify({
                "error": "Candidature introuvable"
            }), 404

        return jsonify(dict(row))

    finally:
        con.close()

# =========================================================
# ADMIN - STATISTIQUES
# =========================================================

@app.route("/api/admin/stats")
def admin_stats():

    admin, erreur = verifier_admin()

    if erreur:
        return erreur

    con = connexion()

    try:
        total_etudiants = con.execute("""
            SELECT COUNT(*) AS total
            FROM users
            WHERE role = 'etudiant'
        """).fetchone()["total"]

        total_candidatures = con.execute("""
            SELECT COUNT(*) AS total
            FROM candidatures
        """).fetchone()["total"]

        en_attente = con.execute("""
            SELECT COUNT(*) AS total
            FROM candidatures
            WHERE statut = 'En attente'
        """).fetchone()["total"]

        entretiens = con.execute("""
            SELECT COUNT(*) AS total
            FROM candidatures
            WHERE statut = 'Entretien'
        """).fetchone()["total"]

        acceptees = con.execute("""
            SELECT COUNT(*) AS total
            FROM candidatures
            WHERE statut = 'Acceptée'
        """).fetchone()["total"]

        refusees = con.execute("""
            SELECT COUNT(*) AS total
            FROM candidatures
            WHERE statut = 'Refusée'
        """).fetchone()["total"]

        return jsonify({
            "total_etudiants": total_etudiants,
            "total_candidatures": total_candidatures,
            "en_attente": en_attente,
            "entretiens": entretiens,
            "acceptees": acceptees,
            "refusees": refusees
        })

    finally:
        con.close()


# =========================================================
# ADMIN - TOUTES LES CANDIDATURES
# =========================================================

@app.route("/api/admin/candidatures")
def admin_candidatures():

    admin, erreur = verifier_admin()

    if erreur:
        return erreur

    con = connexion()

    try:
        rows = con.execute("""
            SELECT
                c.id,
                c.user_id,
                c.offre_id,
                c.statut,
                c.date_candidature,
                c.date_modification,
                c.message,

                u.nom AS nom_etudiant,
                u.prenom AS prenom_etudiant,
                u.email AS email_etudiant,

                o.titre,
                o.entreprise_source,
                o.ville

            FROM candidatures c

            JOIN users u
                ON u.id = c.user_id

            JOIN offres o
                ON o.id = c.offre_id

            ORDER BY c.date_candidature DESC
        """).fetchall()

        return jsonify([dict(row) for row in rows])

    finally:
        con.close()


# =========================================================
# ADMIN - MODIFIER LE STATUT
# =========================================================

@app.route(
    "/api/admin/candidatures/<int:candidature_id>/statut",
    methods=["PATCH"]
)
def admin_modifier_statut(candidature_id):

    admin, erreur = verifier_admin()

    if erreur:
        return erreur

    data = request.get_json(silent=True) or {}
    nouveau_statut = data.get("statut", "").strip()

    statuts_autorises = [
        "En attente",
        "Envoyée",
        "Entretien",
        "Acceptée",
        "Refusée"
    ]

    if nouveau_statut not in statuts_autorises:
        return jsonify({"error": "Statut invalide"}), 400

    con = connexion()

    try:
        # Récupérer la candidature et son propriétaire
        candidature = con.execute("""
            SELECT id, user_id, statut
            FROM candidatures
            WHERE id = ?
        """, (candidature_id,)).fetchone()

        if candidature is None:
            return jsonify({
                "error": "Candidature introuvable"
            }), 404

        ancien_statut = candidature["statut"]
        user_id = candidature["user_id"]

        # Éviter une notification si le statut n'a pas changé
        if ancien_statut == nouveau_statut:
            return jsonify({
                "message": "Le statut est déjà à jour",
                "candidature_id": candidature_id,
                "nouveau_statut": nouveau_statut
            })

        # Modifier le statut
        con.execute("""
            UPDATE candidatures
            SET statut = ?,
                date_modification = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (nouveau_statut, candidature_id))

        # Préparer la notification
        titre = "Mise à jour de votre candidature"

        message = (
            f"Le statut de votre candidature est maintenant : "
            f"{nouveau_statut}"
        )

        # Enregistrer la notification
        con.execute("""
            INSERT INTO notifications (
                user_id,
                candidature_id,
                titre,
                message
            )
            VALUES (?, ?, ?, ?)
        """, (
            user_id,
            candidature_id,
            titre,
            message
        ))

        con.commit()

        return jsonify({
            "message": "Statut modifié et notification créée",
            "candidature_id": candidature_id,
            "ancien_statut": ancien_statut,
            "nouveau_statut": nouveau_statut
        })

    except Exception as e:
        con.rollback()

        return jsonify({
            "error": "Erreur lors de la modification",
            "details": str(e)
        }), 500

    finally:
        con.close()

# =========================================================
# PROFIL ETUDIANT - MODIFICATION
# =========================================================

@app.route("/api/profil", methods=["PUT"])
def modifier_profil():

    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Connexion obligatoire"}), 401

    data = request.get_json(silent=True) or {}

    nom = data.get("nom", "").strip()
    prenom = data.get("prenom", "").strip()
    email = data.get("email", "").strip().lower()

    if not nom or not prenom or not email:
        return jsonify({"error": "Tous les champs sont obligatoires"}), 400

    con = connexion()

    try:
        con.execute("""
            UPDATE users
            SET nom = ?, prenom = ?, email = ?
            WHERE id = ?
        """, (nom, prenom, email, user_id))

        con.commit()

        return jsonify({"message": "Profil modifié avec succès"})

    except sqlite3.IntegrityError:
        return jsonify({"error": "Email déjà utilisé"}), 409

    finally:
        con.close()

# =========================================================
# FAVORIS - LISTE
# =========================================================

@app.route("/api/favoris", methods=["GET"])
def afficher_favoris():

    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Connexion obligatoire"}), 401

    con = connexion()

    try:
        rows = con.execute("""
            SELECT f.id AS favori_id, f.date_ajout,
                   o.*
            FROM favoris f
            JOIN offres o ON o.id = f.offre_id
            WHERE f.user_id = ?
            ORDER BY f.date_ajout DESC
        """, (user_id,)).fetchall()

        return jsonify([dict(row) for row in rows])

    finally:
        con.close()


# =========================================================
# FAVORIS - AJOUT
# =========================================================

@app.route("/api/favoris", methods=["POST"])
def ajouter_favori():

    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Connexion obligatoire"}), 401

    data = request.get_json(silent=True) or {}
    offre_id = data.get("offre_id")

    if not offre_id:
        return jsonify({"error": "offre_id obligatoire"}), 400

    con = connexion()

    try:
        offre = con.execute(
            "SELECT id FROM offres WHERE id = ?", (offre_id,)
        ).fetchone()

        if offre is None:
            return jsonify({"error": "Offre introuvable"}), 404

        con.execute("""
            INSERT INTO favoris (user_id, offre_id)
            VALUES (?, ?)
        """, (user_id, offre_id))

        con.commit()

        return jsonify({"message": "Offre ajoutée aux favoris"}), 201

    except sqlite3.IntegrityError:
        return jsonify({"error": "Cette offre est déjà dans vos favoris"}), 409

    finally:
        con.close()


# =========================================================
# FAVORIS - SUPPRESSION
# =========================================================

@app.route("/api/favoris/<int:favori_id>", methods=["DELETE"])
def supprimer_favori(favori_id):

    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Connexion obligatoire"}), 401

    con = connexion()

    try:
        cur = con.execute("""
            DELETE FROM favoris
            WHERE id = ? AND user_id = ?
        """, (favori_id, user_id))

        con.commit()

        if cur.rowcount == 0:
            return jsonify({"error": "Favori introuvable"}), 404

        return jsonify({"message": "Favori supprimé"})

    finally:
        con.close()

# =========================================================
# CANDIDATURE - ANNULATION
# =========================================================

@app.route("/api/candidatures/<int:candidature_id>", methods=["DELETE"])
def annuler_candidature(candidature_id):

    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Connexion obligatoire"}), 401

    con = connexion()

    try:
        candidature = con.execute("""
            SELECT id, statut
            FROM candidatures
            WHERE id = ? AND user_id = ?
        """, (candidature_id, user_id)).fetchone()

        if candidature is None:
            return jsonify({"error": "Candidature introuvable"}), 404

        if candidature["statut"] in ["Acceptée", "Refusée"]:
            return jsonify({
                "error": "Cette candidature ne peut plus être annulée"
            }), 400

        con.execute("""
            DELETE FROM candidatures
            WHERE id = ? AND user_id = ?
        """, (candidature_id, user_id))

        con.commit()

        return jsonify({"message": "Candidature annulée"})

    finally:
        con.close()

# =========================================================
# CV - UPLOAD PDF
# =========================================================

@app.route("/api/cv", methods=["POST"])
def upload_cv():

    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Connexion obligatoire"}), 401

    if "cv" not in request.files:
        return jsonify({"error": "Veuillez sélectionner un CV"}), 400

    fichier = request.files["cv"]

    if fichier.filename == "":
        return jsonify({"error": "Nom de fichier invalide"}), 400

    if not fichier.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Seuls les fichiers PDF sont acceptés"}), 400

    # Limite : 5 Mo
    fichier.seek(0, os.SEEK_END)
    taille = fichier.tell()
    fichier.seek(0)

    if taille > 5 * 1024 * 1024:
        return jsonify({"error": "Le CV ne doit pas dépasser 5 Mo"}), 400

    dossier = os.path.join(BASE_DIR, "backend", "uploads", "cv")
    os.makedirs(dossier, exist_ok=True)

    nom_fichier = secure_filename(f"cv_etudiant_{user_id}.pdf")
    chemin = os.path.join(dossier, nom_fichier)

    fichier.save(chemin)

    con = connexion()

    try:
        con.execute("""
            UPDATE users
            SET cv_path = ?
            WHERE id = ?
        """, (chemin, user_id))

        con.commit()

        return jsonify({"message": "CV envoyé avec succès"})

    finally:
        con.close()


# =========================================================
# CV - TELECHARGEMENT
# =========================================================

@app.route("/api/cv", methods=["GET"])
def telecharger_cv():

    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Connexion obligatoire"}), 401

    con = connexion()

    try:
        user = con.execute("""
            SELECT cv_path
            FROM users
            WHERE id = ?
        """, (user_id,)).fetchone()

    finally:
        con.close()

    if not user or not user["cv_path"]:
        return jsonify({"error": "Aucun CV enregistré"}), 404

    if not os.path.isfile(user["cv_path"]):
        return jsonify({"error": "Fichier CV introuvable"}), 404

    return send_file(
        user["cv_path"],
        as_attachment=True,
        download_name="Mon_CV.pdf"
    )

# =========================================================
# ADMIN - EXPORT CSV
# =========================================================

@app.route("/api/admin/export-candidatures")
def exporter_candidatures():

    admin, erreur = verifier_admin()

    if erreur:
        return erreur

    con = connexion()

    try:
        rows = con.execute("""
            SELECT
                u.nom,
                u.prenom,
                u.email,
                o.titre,
                o.entreprise_source,
                o.ville,
                c.statut,
                c.date_candidature
            FROM candidatures c
            JOIN users u ON u.id = c.user_id
            JOIN offres o ON o.id = c.offre_id
            ORDER BY c.date_candidature DESC
        """).fetchall()

    finally:
        con.close()

    output = io.StringIO()
    output.write("\\ufeff")

    writer = csv.writer(output, delimiter=";")

    writer.writerow([
        "Nom",
        "Prénom",
        "Email",
        "Offre",
        "Entreprise",
        "Ville",
        "Statut",
        "Date candidature"
    ])

    for row in rows:
        writer.writerow([
            row["nom"],
            row["prenom"],
            row["email"],
            row["titre"],
            row["entreprise_source"],
            row["ville"],
            row["statut"],
            row["date_candidature"]
        ])

    response = app.response_class(
        output.getvalue(),
        mimetype="text/csv"
    )

    response.headers["Content-Disposition"] = (
        "attachment; filename=candidatures_stagex.csv"
    )

    return response

# ==============================
# NOTIFICATIONS
# ==============================

@app.route("/api/notifications", methods=["GET"])
def mes_notifications():

    if "user_id" not in session:
        return jsonify({"error": "Connexion obligatoire"}), 401

    user_id = session["user_id"]

    con = connexion()

    notifications = con.execute("""
        SELECT *
        FROM notifications
        WHERE user_id = ?
        ORDER BY date_creation DESC
    """, (user_id,)).fetchall()

    con.close()

    return jsonify([dict(n) for n in notifications])


@app.route("/api/notifications/<int:notification_id>/lu",
           methods=["PATCH"])
def notification_lue(notification_id):

    if "user_id" not in session:
        return jsonify({"error": "Connexion obligatoire"}), 401

    user_id = session["user_id"]

    con = connexion()

    result = con.execute("""
        UPDATE notifications
        SET lu = 1
        WHERE id = ? AND user_id = ?
    """, (notification_id, user_id))

    con.commit()
    con.close()

    if result.rowcount == 0:
        return jsonify({"error": "Notification introuvable"}), 404

    return jsonify({"message": "Notification marquée comme lue"})


@app.route("/api/notifications/non-lues", methods=["GET"])
def notifications_non_lues():

    if "user_id" not in session:
        return jsonify({"error": "Connexion obligatoire"}), 401

    con = connexion()

    resultat = con.execute("""
        SELECT COUNT(*) AS total
        FROM notifications
        WHERE user_id = ? AND lu = 0
    """, (session["user_id"],)).fetchone()

    con.close()

    return jsonify({"total": resultat["total"]})

# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=os.environ.get("FLASK_DEBUG") == "1"
    )