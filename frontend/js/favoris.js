
const API_URL = "http://127.0.0.1:5000/api";

const container = document.getElementById("favorisContainer");
const message = document.getElementById("favorisMessage");

// Afficher un message
function afficherMessage(messageTexte) {
    message.textContent = messageTexte;
}

// Sécuriser l'affichage du texte
function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, function(char) {
        return {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#039;"
        }[char];
    });
}

// Charger les favoris
async function chargerFavoris() {
    try {
        const response = await fetch(`${API_URL}/favoris`, {
            credentials: "include"
        });

        if (response.status === 401) {
            window.location.href = "connexion.html";
            return;
        }

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Erreur de chargement");
        }

        afficherFavoris(data);

    } catch (error) {
        afficherMessage(error.message);
    }
}

// Afficher les favoris
function afficherFavoris(favoris) {
    if (!favoris || favoris.length === 0) {
        container.innerHTML = "<p>Vous n'avez aucune offre favorite.</p>";
        return;
    }

    container.innerHTML = favoris.map(favori => `
        <div class="candidature-card">
            <h3>${escapeHTML(favori.titre)}</h3>

            <p>
                <strong>Entreprise :</strong>
                ${escapeHTML(favori.entreprise_source || "Non précisée")}
            </p>

            <p>
                <strong>Ville :</strong>
                ${escapeHTML(favori.ville || "Marrakech")}
            </p>

            <p>
                <strong>Ajouté le :</strong>
                ${escapeHTML(favori.date_ajout || "")}
            </p>

            <button
                type="button"
                class="btn-primary"
                onclick="supprimerFavori(${Number(favori.favori_id)})">
                Supprimer des favoris
            </button>
        </div>
    `).join("");
}

// Supprimer un favori
async function supprimerFavori(id) {
    if (!confirm("Voulez-vous supprimer cette offre des favoris ?")) {
        return;
    }

    try {
        const response = await fetch(`${API_URL}/favoris/${id}`, {
            method: "DELETE",
            credentials: "include"
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Erreur de suppression");
        }

        afficherMessage("Offre supprimée des favoris !");
        chargerFavoris();

    } catch (error) {
        afficherMessage(error.message);
    }
}

// Initialisation
chargerFavoris();
