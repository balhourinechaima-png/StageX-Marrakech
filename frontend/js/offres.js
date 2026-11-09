document.addEventListener("DOMContentLoaded", () => {
    chargerOffres();

    const searchInput = document.getElementById("searchInput");
    const searchBtn = document.getElementById("searchBtn");

    const domainFilter = document.getElementById("domainFilter");
    const typeFilter = document.getElementById("typeFilter");
    const durationFilter = document.getElementById("durationFilter");
    const locationFilter = document.getElementById("locationFilter");
    const aiFilter = document.getElementById("aiFilter");
    const sortFilter = document.getElementById("sortFilter");
    const resetFilters = document.getElementById("resetFilters");


    // =========================
    // RECHERCHE
    // =========================

    if (searchBtn) {
        searchBtn.addEventListener("click", chargerOffres);
    }

    if (searchInput) {
        searchInput.addEventListener("keydown", (event) => {
            if (event.key === "Enter") {
                chargerOffres();
            }
        });
    }


    // =========================
    // FILTERS
    // =========================

    if (domainFilter) {
        domainFilter.addEventListener("change", chargerOffres);
    }

    if (typeFilter) {
        typeFilter.addEventListener("change", chargerOffres);
    }

    if (durationFilter) {
        durationFilter.addEventListener("change", chargerOffres);
    }

    if (locationFilter) {
        locationFilter.addEventListener("change", chargerOffres);
    }

    if (aiFilter) {
        aiFilter.addEventListener("change", chargerOffres);
    }

    if (sortFilter) {
        sortFilter.addEventListener("change", chargerOffres);
    }


    // =========================
    // RESET
    // =========================

    if (resetFilters) {
        resetFilters.addEventListener("click", () => {

            if (searchInput) {
                searchInput.value = "";
            }

            if (domainFilter) {
                domainFilter.value = "all";
            }

            if (typeFilter) {
                typeFilter.value = "all";
            }

            if (durationFilter) {
                durationFilter.value = "all";
            }

            if (locationFilter) {
                locationFilter.value = "all";
            }

            if (aiFilter) {
                aiFilter.checked = false;
            }

            if (sortFilter) {
                sortFilter.value = "recent";
            }

            chargerOffres();
        });
    }
});


// =========================================================
// CHARGER LES OFFRES
// =========================================================

async function chargerOffres() {

    const offersGrid =
        document.getElementById("offersGrid");

    const resultsCount =
        document.getElementById("resultsCount");

    const noResults =
        document.getElementById("noResults");


    if (!offersGrid) {
        return;
    }


    // =========================
    // RÉCUPÉRER LES FILTRES
    // =========================

    const searchInput =
        document.getElementById("searchInput");

    const domainFilter =
        document.getElementById("domainFilter");

    const typeFilter =
        document.getElementById("typeFilter");

    const durationFilter =
        document.getElementById("durationFilter");

    const locationFilter =
        document.getElementById("locationFilter");

    const aiFilter =
        document.getElementById("aiFilter");

    const sortFilter =
        document.getElementById("sortFilter");


    const search =
        searchInput
            ? searchInput.value.trim().toLowerCase()
            : "";


    const domain =
        domainFilter
            ? domainFilter.value
            : "all";


    const type =
        typeFilter
            ? typeFilter.value
            : "all";


    const duration =
        durationFilter
            ? durationFilter.value
            : "all";


    const location =
        locationFilter
            ? locationFilter.value
            : "all";


    const aiMatch =
        aiFilter
            ? aiFilter.checked
            : false;


    // =====================================================
    // API
    // =====================================================

    const params = new URLSearchParams();


    if (search) {
        params.set("q", search);
    }


    if (
        location &&
        location !== "all"
    ) {
        params.set(
            "ville",
            location
        );
    }


    if (
        type &&
        type !== "all"
    ) {
        params.set(
            "type",
            type
        );
    }


    if (
        domain &&
        domain !== "all"
    ) {
        params.set(
            "domaine",
            domain
        );
    }


    try {

        const response = await fetch(
            `http://127.0.0.1:5000/api/offres?${params.toString()}`
        );


        if (!response.ok) {
            throw new Error("Erreur API");
        }


        let offres =
            await response.json();


        console.log(
            "Offres reçues :",
            offres
        );


        // =================================================
        // FILTRE LOCAL : DURÉE
        // =================================================

        if (duration !== "all") {

            offres =
                offres.filter(offre => {

                    const duree =
                        String(
                            offre.duree || ""
                        ).toLowerCase();

                    return duree.includes(
                        duration
                    );
                });
        }


        // =================================================
        // FILTRE LOCAL : AI MATCH
        // =================================================

        if (aiMatch) {

            offres =
                offres.filter(offre => {

                    const texte =
                        `${offre.titre || ""} ${
                            offre.domaine || ""
                        } ${
                            offre.description || ""
                        }`.toLowerCase();


                    return (
                        texte.includes("ai") ||
                        texte.includes("artificial intelligence") ||
                        texte.includes("machine learning") ||
                        texte.includes("data") ||
                        texte.includes("python")
                    );
                });
        }


        // =================================================
        // TRI
        // =================================================

        const sortFilter =
            document.getElementById("sortFilter");


        const sort =
            sortFilter
                ? sortFilter.value
                : "recent";


        if (sort === "recent") {

            offres.sort((a, b) => {

                const dateA =
                    new Date(
                        a.date_publication || 0
                    );

                const dateB =
                    new Date(
                        b.date_publication || 0
                    );

                return dateB - dateA;
            });
        }


        if (sort === "duration") {

            offres.sort((a, b) => {

                const dureeA =
                    parseInt(
                        a.duree || 0
                    ) || 0;

                const dureeB =
                    parseInt(
                        b.duree || 0
                    ) || 0;

                return dureeA - dureeB;
            });
        }


        // =================================================
        // AFFICHAGE NOMBRE
        // =================================================

        if (resultsCount) {

            resultsCount.textContent =
                `${offres.length} offres trouvées`;
        }


        // =================================================
        // AUCUN RÉSULTAT
        // =================================================

        if (offres.length === 0) {

            offersGrid.innerHTML = "";

            if (noResults) {
                noResults.style.display = "block";
            }

            return;
        }


        if (noResults) {
            noResults.style.display = "none";
        }


        // =================================================
        // CREATION DES CARDS
        // =================================================

        offersGrid.innerHTML =
            offres
                .map(creerCarteOffre)
                .join("");


    } catch (error) {

        console.error(
            "Erreur chargement offres :",
            error
        );


        offersGrid.innerHTML = "";


        if (noResults) {
            noResults.style.display = "block";
        }


        if (resultsCount) {
            resultsCount.textContent =
                "Erreur de chargement";
        }
    }
}


// =========================================================
// CREER UNE CARD
// =========================================================

function creerCarteOffre(offre) {

    const entreprise =
        offre.entreprise_source ||
        "Entreprise non précisée";


    const titre =
        offre.titre ||
        "Offre sans titre";


    const ville =
        offre.ville ||
        "Non précisé";


    const type =
        offre.type ||
        "Non précisé";


    const domaine =
        offre.domaine ||
        "Non précisé";


    const source =
        offre.source ||
        "Source externe";


    const lienDetail =
        `./offre-detail.html?id=${encodeURIComponent(
            offre.id
        )}`;


    return `
        <article
            class="offer-card"
            data-offre-id="${escapeHTML(
                String(offre.id)
            )}"
        >

            <div class="card-top">

                <div class="company-logo">
                    ${getInitiales(entreprise)}
                </div>

                <span class="stage-badge">
                    ${escapeHTML(type)}
                </span>

            </div>


            <div class="company">
                ${escapeHTML(entreprise)}
            </div>


            <h3>
                ${escapeHTML(titre)}
            </h3>


            <div class="offer-info">

                <span>
                    📍 ${escapeHTML(ville)}
                </span>

                <span>
                    🧩 ${escapeHTML(domaine)}
                </span>

            </div>


            <div class="skills">

                <span>
                    ${escapeHTML(source)}
                </span>

            </div>


            <div class="card-bottom">

                <div class="match">

                    <strong>—</strong>

                    <small>
                        AI Match
                    </small>

                </div>


                
                 <div class="offer-actions">
                 
                     <a
                         class="view-offer"
                         href="${lienDetail}"
                     >
                         Voir l'offre →
                     </a>

                     <button
                         class="btn-postuler"
                         onclick="postuler(${Number(offre.id)})"
                     >
                         Postuler
                     </button>

                 </div>


            </div>

        </article>
    `;
}


// =========================================================
// INITIALES
// =========================================================

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


// =========================================================
// PROTECTION HTML
// =========================================================

function escapeHTML(value) {

    const div =
        document.createElement("div");

    div.textContent =
        value;

    return div.innerHTML;
}



async function postuler(offreId) {

    try {

        // Vérifier si l'étudiant est connecté
        const userResponse = await fetch(
            "http://127.0.0.1:5000/api/auth/me",
            {
                credentials: "include"
            }
        );

        if (!userResponse.ok) {
            window.location.href = "connexion.html";
            return;
        }

        // Envoyer la candidature
        const response = await fetch(
            "http://127.0.0.1:5000/api/candidatures",
            {
                method: "POST",
                credentials: "include",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    offre_id: offreId
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            alert(data.error || "Erreur");
            return;
        }

        alert("Candidature enregistrée avec succès !");

        // Accéder au suivi
        window.location.href = "dashboard.html";

    } catch (error) {

        console.error(error);

        alert("Impossible de contacter le serveur StageX.");
    }
}
