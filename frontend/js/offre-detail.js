const params = new URLSearchParams(window.location.search);
const offreId = params.get("id");

document.addEventListener("DOMContentLoaded", () => {
    chargerDetail();
});


async function chargerDetail() {

    if (!offreId) {
        afficherErreur("Identifiant de l'offre manquant.");
        return;
    }

    try {

        const response = await fetch(
            `http://127.0.0.1:5000/api/offres/${offreId}`
        );

        if (!response.ok) {
            throw new Error("Offre introuvable");
        }

        const offre = await response.json();

        console.log("Offre chargée :", offre);

        afficherDetail(offre);

    } catch (error) {

        console.error(
            "Erreur chargement offre :",
            error
        );

        afficherErreur(
            "Impossible de charger cette offre."
        );
    }
}


/* =========================
   AFFICHER LES INFORMATIONS
========================= */

function afficherDetail(offre) {

    // TITRE
    const title = document.querySelector("#offerTitle");

    if (title) {
        title.textContent =
            offre.titre || "Offre sans titre";
    }


    // ENTREPRISE
    const company =
        offre.entreprise_source ||
        "Entreprise non précisée";

    const companyName =
        document.querySelector("#companyName");

    if (companyName) {
        companyName.textContent = company;
    }


    // LOGO / INITIALES
    const initiales = getInitiales(company);

    const logo =
        document.querySelector("#companyLogo");

    if (logo) {
        logo.textContent = initiales;
    }

    const sideLogo =
        document.querySelector("#sideLogo");

    if (sideLogo) {
        sideLogo.textContent = initiales;
    }


    // TYPE
    const type =
        offre.type || "Non précisé";

    const offerType =
        document.querySelector("#offerType");

    if (offerType) {
        offerType.textContent = type;
    }


    // VILLE
    const location =
        offre.ville || "Non précisé";

    const offerLocation =
        document.querySelector("#offerLocation");

    if (offerLocation) {
        offerLocation.textContent = location;
    }

    const sideLocation =
        document.querySelector("#sideLocation");

    if (sideLocation) {
        sideLocation.textContent = location;
    }


    // DURÉE
    const duration =
        offre.duree || "Non précisée";

    const offerDuration =
        document.querySelector("#offerDuration");

    if (offerDuration) {
        offerDuration.textContent = duration;
    }

    const sideDuration =
        document.querySelector("#sideDuration");

    if (sideDuration) {
        sideDuration.textContent = duration;
    }


    // DESCRIPTION
    const description =
        document.querySelector("#description");

    if (description) {

        description.textContent =
            offre.description ||
            "Aucune description disponible dans la source originale.";
    }


    // PROFIL
    const profile =
        document.querySelector("#profile");

    if (profile) {

        profile.textContent =
            offre.profil ||
            "Profil non précisé dans la source originale.";
    }


    // DOMAINE
    const domain =
        offre.domaine || "Non précisé";

    const sideDomain =
        document.querySelector("#sideDomain");

    if (sideDomain) {
        sideDomain.textContent = domain;
    }


    // ENTREPRISE SIDEBAR
    const sideCompany =
        document.querySelector("#sideCompany");

    if (sideCompany) {
        sideCompany.textContent = company;
    }


    // DESCRIPTION ENTREPRISE
    const companyDescription =
        document.querySelector("#companyDescription");

    if (companyDescription) {

        companyDescription.textContent =
            `Cette offre est publiée par ${company}. ` +
            `Consultez la source originale pour obtenir ` +
            `les informations complètes sur l'entreprise.`;
    }


    // MISSIONS
    const missions =
        document.querySelector("#missions");

    if (missions) {

        if (offre.description) {

            missions.innerHTML = `
                <li>
                    Consultez la description originale
                    pour connaître les missions du poste.
                </li>

                <li>
                    Les missions présentées par l'entreprise
                    sont disponibles dans la source de l'offre.
                </li>
            `;

        } else {

            missions.innerHTML = `
                <li>
                    Missions non précisées.
                </li>
            `;
        }
    }


    // COMPÉTENCES
    const skills =
        document.querySelector("#skills");

    if (skills) {

        if (domain !== "Non précisé") {

            skills.innerHTML = `
                <span>
                    ${escapeHTML(domain)}
                </span>
            `;

        } else {

            skills.innerHTML = `
                <span>
                    Non précisé
                </span>
            `;
        }
    }


    // AI INSIGHT
    const aiInsight =
        document.querySelector("#aiInsight");

    if (aiInsight) {

        aiInsight.textContent =
            "Les informations affichées sur cette page " +
            "proviennent de la source originale de l'offre. " +
            "StageX ne modifie pas les informations publiées " +
            "par l'entreprise.";
    }


    // =========================
    // BOUTON POSTULER
    // =========================

    const applyButton =
        document.querySelector("#applyButton");

    if (applyButton) {

        const lien =
            offre.url_candidature ||
            offre.url_source;

        if (lien) {

            applyButton.href = lien;

            applyButton.target = "_blank";

            applyButton.rel =
                "noopener noreferrer";

            applyButton.textContent =
                "Postuler à l'offre →";

        } else {

            applyButton.removeAttribute("href");

            applyButton.textContent =
                "Lien de candidature non disponible";

            applyButton.style.opacity = "0.6";

            applyButton.style.cursor =
                "not-allowed";
        }
    }
}


/* =========================
   ERREUR
========================= */

function afficherErreur(message) {

    const title =
        document.querySelector("#offerTitle");

    if (title) {
        title.textContent = message;
    }
}


/* =========================
   INITIALES
========================= */

function getInitiales(nom) {

    if (!nom) {
        return "SX";
    }

    const mots =
        nom.trim().split(/\s+/);

    if (mots.length === 1) {

        return mots[0]
            .substring(0, 2)
            .toUpperCase();
    }

    return (
        mots[0][0] +
        mots[1][0]
    ).toUpperCase();
}


/* =========================
   PROTECTION HTML
========================= */

function escapeHTML(value) {

    const div =
        document.createElement("div");

    div.textContent = value;

    return div.innerHTML;
}


/* =========================
   PARTAGE
========================= */

function shareOffer() {

    const url =
        window.location.href;

    if (navigator.clipboard) {

        navigator.clipboard
            .writeText(url)
            .then(() => {

                alert(
                    "Lien de l'offre copié !"
                );

            })
            .catch(() => {

                alert(
                    "Impossible de copier le lien."
                );
            });

    } else {

        alert(
            "Copiez le lien depuis la barre d'adresse."
        );
    }
}