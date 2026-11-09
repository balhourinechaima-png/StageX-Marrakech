
const API = "http://127.0.0.1:5000/api";

async function apiRequest(url, options = {}) {
    const response = await fetch(API + url, {
        credentials: "include",
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {})
        }
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error || "Une erreur est survenue");
    }

    return data;
}

// INSCRIPTION
const registerForm = document.getElementById("registerForm");

if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const message = document.getElementById("message");

        try {
            const data = await apiRequest("/auth/register", {
                method: "POST",
                body: JSON.stringify({
                    nom: document.getElementById("nom").value,
                    prenom: document.getElementById("prenom").value,
                    email: document.getElementById("email").value,
                    password: document.getElementById("password").value
                })
            });

            message.textContent = data.message;

            window.location.href = "dashboard.html";

        } catch (error) {
            message.textContent = error.message;
        }
    });
}

// CONNEXION
const loginForm = document.getElementById("loginForm");

if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const message = document.getElementById("message");

        try {
            const data = await apiRequest("/auth/login", {
                method: "POST",
                body: JSON.stringify({
                    email: document.getElementById("email").value,
                    password: document.getElementById("password").value
                })
            });

            message.textContent = data.message;

            window.location.href = "dashboard.html";

        } catch (error) {
            message.textContent = error.message;
        }
    });
}

// DECONNEXION
async function logout() {
    try {
        await apiRequest("/auth/logout", {
            method: "POST"
        });

        window.location.href = "connexion.html";

    } catch (error) {
        alert(error.message);
    }
}

// =====================================================
// PROFIL ETUDIANT
// =====================================================

async function modifierProfil(nom, prenom, email) {
    return await apiRequest("/profil", {
        method: "PUT",
        body: JSON.stringify({ nom, prenom, email })
    });
}


// =====================================================
// CV - UPLOAD
// =====================================================

async function envoyerCV(fichier) {
    const formData = new FormData();
    formData.append("cv", fichier);

    const response = await fetch(API + "/cv", {
        method: "POST",
        credentials: "include",
        body: formData
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error || "Erreur lors de l'envoi du CV");
    }

    return data;
}


// =====================================================
// CV - TELECHARGEMENT
// =====================================================

async function telechargerCV() {
    const response = await fetch(API + "/cv", {
        credentials: "include"
    });

    if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || "Impossible de télécharger le CV");
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);

    const lien = document.createElement("a");
    lien.href = url;
    lien.download = "Mon_CV.pdf";
    lien.click();

    URL.revokeObjectURL(url);
}


// =====================================================
// FAVORIS
// =====================================================

async function ajouterAuxFavoris(offreId) {
    return await apiRequest("/favoris", {
        method: "POST",
        body: JSON.stringify({ offre_id: offreId })
    });
}

async function chargerFavoris() {
    return await apiRequest("/favoris");
}

async function supprimerFavori(favoriId) {
    return await apiRequest("/favoris/" + favoriId, {
        method: "DELETE"
    });
}


// =====================================================
// ANNULER CANDIDATURE
// =====================================================

async function annulerCandidature(candidatureId) {
    return await apiRequest("/candidatures/" + candidatureId, {
        method: "DELETE"
    });
}