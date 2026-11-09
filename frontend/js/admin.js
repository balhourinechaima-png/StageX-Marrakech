// ========================================
// STAGEX-MARRAKECH - ADMIN DASHBOARD
// ========================================

const API_URL = "http://127.0.0.1:5000/api";

// Statuts des candidatures
const STATUTS = [
    "En attente",
    "Envoyée",
    "Entretien",
    "Acceptée",
    "Refusée"
];

// ========================================
// PROTECTION ADMIN
// ========================================

async function verifierAdmin() {
    const message = document.getElementById("adminMessage");

    try {
        const response = await fetch(API_URL + "/auth/me", {
            credentials: "include"
        });

        if (!response.ok) {
            window.location.href = "connexion.html";
            return false;
        }

        const user = await response.json();

        if (user.role !== "admin") {
            message.innerHTML = `
                <p class="error-message">
                    Accès refusé : page réservée à l'administration.
                </p>
            `;
            return false;
        }

        message.innerHTML = `
            <p>
                Bienvenue dans l'espace administrateur,
                <strong>${escapeHTML(user.prenom)} ${escapeHTML(user.nom)}</strong>
            </p>
        `;

        return true;

    } catch (error) {
        console.error(error);

        message.innerHTML = `
            <p class="error-message">
                Impossible de vérifier les droits administrateur.
            </p>
        `;

        return false;
    }
}

// ========================================
// PROTECTION CONTRE HTML INJECTÉ
// ========================================

function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, character => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[character]);
}

// ========================================
// CHARGER LES STATISTIQUES
// ========================================

async function chargerStatsAdmin() {
    const container = document.getElementById("adminStats");

    try {
        const response = await fetch(API_URL + "/admin/stats", {
            credentials: "include"
        });

        if (!response.ok) {
            throw new Error("Erreur de chargement des statistiques");
        }

        const stats = await response.json();

        container.innerHTML = `
            <div class="admin-stat-card">
                <h3>Étudiants</h3>
                <p>${stats.total_etudiants}</p>
            </div>

            <div class="admin-stat-card">
                <h3>Candidatures</h3>
                <p>${stats.total_candidatures}</p>
            </div>

            <div class="admin-stat-card">
                <h3>En attente</h3>
                <p>${stats.en_attente}</p>
            </div>

            <div class="admin-stat-card">
                <h3>Entretiens</h3>
                <p>${stats.entretiens}</p>
            </div>

            <div class="admin-stat-card">
                <h3>Acceptées</h3>
                <p>${stats.acceptees}</p>
            </div>

            <div class="admin-stat-card">
                <h3>Refusées</h3>
                <p>${stats.refusees}</p>
            </div>
        `;

    } catch (error) {
        console.error(error);

        container.innerHTML = `
            <p class="error-message">
                Impossible de charger les statistiques.
            </p>
        `;
    }
}

// ========================================
// CHARGER LES CANDIDATURES
// ========================================

async function chargerCandidaturesAdmin() {
    const container = document.getElementById("adminCandidatures");

    container.innerHTML = "Chargement des candidatures...";

    try {
        const response = await fetch(API_URL + "/admin/candidatures", {
            credentials: "include"
        });

        if (!response.ok) {
            throw new Error("Impossible de charger les candidatures");
        }

        const candidatures = await response.json();

        if (!Array.isArray(candidatures) || candidatures.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>Aucune candidature</h3>
                    <p>Les candidatures apparaîtront ici.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = candidatures.map(c => `
            <article class="candidature-card admin-candidature-card">

                <div class="candidature-header">
                    <h3>${escapeHTML(c.titre || "Offre de stage")}</h3>

                    <span class="statut ${getClasseStatut(c.statut)}">
                        ${escapeHTML(c.statut)}
                    </span>
                </div>

                <p>
                    <strong>Étudiant :</strong>
                    ${escapeHTML(c.prenom_etudiant)}
                    ${escapeHTML(c.nom_etudiant)}
                </p>

                <p>
                    <strong>Email :</strong>
                    ${escapeHTML(c.email_etudiant)}
                </p>

                <p>
                    <strong>Entreprise :</strong>
                    ${escapeHTML(c.entreprise_source || "Non précisée")}
                </p>

                <p>
                    <strong>Ville :</strong>
                    ${escapeHTML(c.ville || "Non précisée")}
                </p>

                <p>
                    <strong>Date :</strong>
                    ${escapeHTML(c.date_candidature || "Non disponible")}
                </p>

                <p>
                    <strong>Message :</strong>
                    ${escapeHTML(c.message || "Aucun message")}
                </p>

                <label for="statut-${c.id}">
                    Modifier le statut :
                </label>

                <select id="statut-${c.id}">
                    ${STATUTS.map(statut => `
                        <option value="${escapeHTML(statut)}"
                            ${statut === c.statut ? "selected" : ""}>
                            ${escapeHTML(statut)}
                        </option>
                    `).join("")}
                </select>

                <button
                    type="button"
                    class="btn-primary"
                    onclick="modifierStatut(${c.id})">

                    Enregistrer le statut

                </button>

                <p id="message-${c.id}"></p>

            </article>
        `).join("");

    } catch (error) {
        console.error(error);

        container.innerHTML = `
            <p class="error-message">
                Impossible de charger les candidatures.
                Vérifiez que le Backend est démarré.
            </p>
        `;
    }
}

// ========================================
// MODIFIER LE STATUT
// ========================================

async function modifierStatut(candidatureId) {

    const select = document.getElementById("statut-" + candidatureId);
    const message = document.getElementById("message-" + candidatureId);

    const nouveauStatut = select.value;

    try {
        const response = await fetch(
            API_URL + "/admin/candidatures/" + candidatureId + "/statut",
            {
                method: "PATCH",

                credentials: "include",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    statut: nouveauStatut
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Erreur de modification");
        }

        message.textContent = "Statut modifié avec succès ✓";
        message.style.color = "green";

        // Actualiser les statistiques
        await chargerStatsAdmin();

        // Actualiser les candidatures
        await chargerCandidaturesAdmin();

    } catch (error) {
        console.error(error);

        message.textContent = error.message;
        message.style.color = "red";
    }
}

// ========================================
// COULEURS DES STATUTS
// ========================================

function getClasseStatut(statut) {

    const classes = {
        "En attente": "statut-attente",
        "Envoyée": "statut-envoyee",
        "Entretien": "statut-entretien",
        "Acceptée": "statut-acceptee",
        "Refusée": "statut-refusee"
    };

    return classes[statut] || "statut-attente";
}

// ========================================
// INITIALISATION
// ========================================

document.addEventListener("DOMContentLoaded", async function () {

    const autorise = await verifierAdmin();

    if (!autorise) {
        return;
    }

    await chargerStatsAdmin();

    await chargerCandidaturesAdmin();

});

async function exporterCandidatures() {
    try {
        const response = await fetch(
            API_URL + "/admin/export-candidatures",
            { credentials: "include" }
        );

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || "Erreur export");
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);

        const lien = document.createElement("a");
        lien.href = url;
        lien.download = "candidatures_stagex.csv";
        lien.click();

        URL.revokeObjectURL(url);

    } catch (error) {
        alert(error.message);
    }
}