const API_URL = "http://127.0.0.1:5000/api/entreprises";

let allCompanies = [];


// ================= LOAD COMPANIES =================

async function loadCompanies() {

    const grid = document.getElementById("companiesGrid");
    const count = document.getElementById("companiesCount");

    try {

        const response = await fetch(API_URL);

        if (!response.ok) {
            throw new Error("Erreur API : " + response.status);
        }

        allCompanies = await response.json();

        console.log("Entreprises reçues :", allCompanies);

        renderCompanies(allCompanies);

    } catch (error) {

        console.error("Erreur chargement entreprises :", error);

        grid.innerHTML = `
            <div class="error-message">
                <h3>Impossible de charger les entreprises</h3>
                <p>
                    Vérifiez que le serveur StageX est bien démarré.
                </p>
            </div>
        `;

        count.textContent = "Erreur";
    }
}


// ================= DISPLAY =================

function renderCompanies(companies) {

    const grid = document.getElementById("companiesGrid");
    const count = document.getElementById("companiesCount");
    const noCompanies = document.getElementById("noCompanies");

    count.textContent = `${companies.length} entreprise${companies.length > 1 ? "s" : ""}`;

    if (companies.length === 0) {

        grid.innerHTML = "";
        noCompanies.style.display = "block";

        return;
    }

    noCompanies.style.display = "none";

    grid.innerHTML = companies.map(company => {

        const name = company.nom || "Entreprise";
        const address = company.adresse || "Adresse non précisée";
        const rating = company.note ?? null;
        const reviews = company.nombre_avis ?? 0;
        const domain = company.domaine || "Domaine non précisé";

        const potentialDomains =
            company.domaines_stage_potentiel ||
            "";

        const mapsUrl =
            company.google_maps ||
            "#";

        // Initiales du nom
        const initials = name
            .split(" ")
            .filter(word => word.length > 0)
            .slice(0, 2)
            .map(word => word[0])
            .join("")
            .toUpperCase();

        return `

            <article class="company-card">

                <div class="company-card-top">

                    <div class="company-logo-company">
                        ${initials || "SX"}
                    </div>

                    <div class="company-rating">

                        ${
                            rating !== null
                            ? `★ ${Number(rating).toFixed(1)}`
                            : "Note non précisée"
                        }

                    </div>

                </div>


                <div class="company-content">

                    <h3>
                        ${escapeHTML(name)}
                    </h3>

                    <p class="company-address">
                        📍 ${escapeHTML(address)}
                    </p>


                    <div class="company-domain">

                        <span>
                            ${escapeHTML(domain)}
                        </span>

                    </div>


                    ${
                        potentialDomains
                        ? `
                            <p class="company-potential">
                                <strong>Stages potentiels :</strong>
                                ${escapeHTML(potentialDomains)}
                            </p>
                        `
                        : ""
                    }

                </div>


                <div class="company-footer">

                    <span class="reviews">

                        ${
                            reviews > 0
                            ? `${reviews} avis Google`
                            : "Avis non précisés"
                        }

                    </span>


                    ${
                        mapsUrl !== "#"
                        ? `
                            <a
                                href="${mapsUrl}"
                                target="_blank"
                                rel="noopener noreferrer"
                                class="maps-button"
                            >
                                Voir sur Google Maps →
                            </a>
                        `
                        : `
                            <span class="maps-disabled">
                                Google Maps non disponible
                            </span>
                        `
                    }

                </div>

            </article>

        `;

    }).join("");
}


// ================= SEARCH =================

function filterCompanies() {

    const search =
        document
            .getElementById("searchCompany")
            .value
            .toLowerCase()
            .trim();

    const domain =
        document
            .getElementById("domainFilter")
            .value
            .toLowerCase();


    const filtered = allCompanies.filter(company => {

        const name =
            (company.nom || "").toLowerCase();

        const address =
            (company.adresse || "").toLowerCase();

        const companyDomain =
            (company.domaine || "").toLowerCase();

        const potential =
            (company.domaines_stage_potentiel || "").toLowerCase();


        const matchesSearch =
            !search ||
            name.includes(search) ||
            address.includes(search) ||
            companyDomain.includes(search) ||
            potential.includes(search);


        const matchesDomain =
            !domain ||
            companyDomain.includes(domain) ||
            potential.includes(domain);


        return matchesSearch && matchesDomain;

    });


    renderCompanies(filtered);
}


// ================= SECURITY =================

function escapeHTML(value) {

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


// ================= EVENTS =================

document
    .getElementById("searchCompany")
    .addEventListener("input", filterCompanies);


document
    .getElementById("domainFilter")
    .addEventListener("change", filterCompanies);


// ================= START =================

loadCompanies();