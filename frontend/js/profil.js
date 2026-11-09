
const API_URL = "http://127.0.0.1:5000/api";

// تحميل معلومات المستخدم
async function chargerProfil() {
    try {
        const response = await fetch(`${API_URL}/auth/me`, {
            credentials: "include"
        });

        if (!response.ok) {
            window.location.href = "connexion.html";
            return;
        }

        const user = await response.json();

        document.getElementById("prenom").value = user.prenom || "";
        document.getElementById("nom").value = user.nom || "";
        document.getElementById("email").value = user.email || "";

    } catch (error) {
        afficherMessage("profilMessage", "Erreur de connexion au serveur.");
    }
}

// Afficher un message
function afficherMessage(id, message) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = message;
    }
}

// Modifier le profil
document.getElementById("profilForm").addEventListener("submit", async function(e) {
    e.preventDefault();

    const donnees = {
        prenom: document.getElementById("prenom").value.trim(),
        nom: document.getElementById("nom").value.trim(),
        email: document.getElementById("email").value.trim()
    };

    try {
        const response = await fetch(`${API_URL}/profil`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json"
            },
            credentials: "include",
            body: JSON.stringify(donnees)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Erreur de modification");
        }

        afficherMessage("profilMessage", "Profil modifié avec succès !");

    } catch (error) {
        afficherMessage("profilMessage", error.message);
    }
});

// Upload du CV
document.getElementById("cvForm").addEventListener("submit", async function(e) {
    e.preventDefault();

    const fichier = document.getElementById("cv").files[0];

    if (!fichier) {
        afficherMessage("cvMessage", "Veuillez sélectionner votre CV.");
        return;
    }

    if (fichier.type !== "application/pdf") {
        afficherMessage("cvMessage", "Le CV doit être au format PDF.");
        return;
    }

    if (fichier.size > 5 * 1024 * 1024) {
        afficherMessage("cvMessage", "Le fichier ne doit pas dépasser 5 MB.");
        return;
    }

    const formData = new FormData();
    formData.append("cv", fichier);

    try {
        const response = await fetch(`${API_URL}/cv`, {
            method: "POST",
            credentials: "include",
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Erreur lors de l'envoi du CV");
        }

        afficherMessage("cvMessage", "CV envoyé avec succès !");

    } catch (error) {
        afficherMessage("cvMessage", error.message);
    }
});

// Télécharger le CV
document.getElementById("btnTelechargerCV").addEventListener("click", async function() {
    try {
        const response = await fetch(`${API_URL}/cv`, {
            credentials: "include"
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || "CV non disponible");
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);

        const lien = document.createElement("a");
        lien.href = url;
        lien.download = "Mon_CV.pdf";
        lien.click();

        window.URL.revokeObjectURL(url);

    } catch (error) {
        afficherMessage("cvMessage", error.message);
    }
});

// Initialisation
chargerProfil();
