
const API_URL = "http://127.0.0.1:5000/api";

// Charger les informations et les candidatures
async function chargerDashboard() {
    const container = document.getElementById("candidatures");

    try {
        // Vérifier la connexion de l'étudiant
        const responseUser = await fetch(API_URL + "/auth/me", {
            credentials: "include"
        });

        if (!responseUser.ok) {
            window.location.href = "connexion.html";
            return;
        }

        const user = await responseUser.json();

        // Afficher les informations de l'étudiant
        document.getElementById("userInfo").innerHTML = `
            <h3>Bienvenue ${escapeHTML(user.prenom)} ${escapeHTML(user.nom)}</h3>
            <p>${escapeHTML(user.email)}</p>
        `;

        // Récupérer les candidatures
        const response = await fetch(API_URL + "/candidatures", {
            credentials: "include"
        });

        if (!response.ok) {
            throw new Error("Erreur lors du chargement des candidatures");
        }

        const candidatures = await response.json();

        // Vérifier si aucune candidature
        if (!Array.isArray(candidatures) || candidatures.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>Aucune candidature pour le moment</h3>
                    <p>Consultez les offres et postulez à celles qui vous intéressent.</p>
                    <a href="offres.html" class="btn-primary">
                        Découvrir les offres
                    </a>
                </div>
            `;
            return;
        }

        // Afficher les candidatures
        container.innerHTML = candidatures.map(c => `
            <article class="candidature-card">

                <div class="candidature-header">
                    <h3>${escapeHTML(c.titre || "Offre de stage")}</h3>

                    <span class="statut ${getClasseStatut(c.statut)}">
                        ${escapeHTML(c.statut || "En attente")}
                    </span>
                </div>

                <p>
                    <strong>Entreprise :</strong>
                    ${escapeHTML(c.entreprise_source || "Non précisée")}
                </p>

                <p>
                    <strong>Ville :</strong>
                    ${escapeHTML(c.ville || "Non précisée")}
                </p>

                <p>
                    <strong>Date de candidature :</strong>
                    ${escapeHTML(c.date_candidature || "Non disponible")}
                </p>

                <button type="button"
                        class="btn-primary"
                        onclick="annulerMaCandidature(${c.id})">
                    Annuler ma candidature
                </button>

            </article>
        `).join("");

    } catch (error) {
        console.error("Erreur Dashboard :", error);

        container.innerHTML = `
            <p class="error-message">
                Impossible de charger les candidatures.
                Vérifiez que le serveur est démarré.
            </p>
        `;
    }
}

// Déterminer la classe CSS selon le statut
function getClasseStatut(statut) {
    const statuts = {
        "En attente": "statut-attente",
        "Envoyée": "statut-envoyee",
        "Entretien": "statut-entretien",
        "Acceptée": "statut-acceptee",
        "Refusée": "statut-refusee"
    };

    return statuts[statut] || "statut-attente";
}

// Échapper les caractères HTML
function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, character => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[character]);
}

// Actualiser les candidatures
async function actualiserCandidatures() {
    const bouton = document.getElementById("btnActualiser");

    bouton.disabled = true;
    bouton.textContent = "Actualisation en cours...";

    try {
        await chargerDashboard();

        bouton.textContent = "Candidatures actualisées ✓";

        setTimeout(() => {
            bouton.textContent = "Actualiser mes candidatures";
        }, 2000);

    } catch (error) {
        bouton.textContent = "Erreur lors de l'actualisation";
    }

    bouton.disabled = false;
}

// Charger le Dashboard et connecter le bouton
document.addEventListener("DOMContentLoaded", function () {

    chargerDashboard();

    const bouton = document.getElementById("btnActualiser");

    if (bouton) {
        bouton.addEventListener("click", actualiserCandidatures);
    }

});

async function annulerMaCandidature(id) {
    const confirmation = confirm(
        "Voulez-vous vraiment annuler cette candidature ?"
    );

    if (!confirmation) return;

    try {
        const response = await fetch(
            API_URL + "/candidatures/" + id,
            {
                method: "DELETE",
                credentials: "include"
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Erreur d'annulation");
        }

        alert(data.message);
        await chargerDashboard();

    } catch (error) {
        alert(error.message);
    }
}