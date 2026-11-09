/* =========================================================
   STAGEX MARRAKECH
   MAIN JAVASCRIPT
========================================================= */


/* =========================================================
   SEARCH
========================================================= */

const searchButton =
    document.getElementById("searchButton");

const searchInput =
    document.getElementById("heroSearch");


function performSearch() {

    if (!searchInput) {
        return;
    }

    const value =
        searchInput.value.trim();

    if (value === "") {

        searchInput.focus();

        return;
    }

    console.log(
        "Recherche StageX :",
        value
    );

    const offers =
        document.getElementById("offers");

    if (offers) {

        offers.scrollIntoView({
            behavior: "smooth"
        });

    }
}


if (searchButton) {

    searchButton.addEventListener(
        "click",
        performSearch
    );

}


if (searchInput) {

    searchInput.addEventListener(
        "keydown",
        function (event) {

            if (event.key === "Enter") {

                performSearch();

            }

        }
    );

}


/* =========================================================
   NAVBAR
========================================================= */

const navbar =
    document.querySelector(".navbar");


window.addEventListener(
    "scroll",
    function () {

        if (!navbar) {
            return;
        }

        if (window.scrollY > 40) {

            navbar.classList.add(
                "scrolled"
            );

        } else {

            navbar.classList.remove(
                "scrolled"
            );

        }

    }
);


/* =========================================================
   SCROLL REVEAL
========================================================= */

const revealElements =
    document.querySelectorAll(
        ".stats-section, " +
        ".intro-section, " +
        ".feature-card, " +
        ".offers-section, " +
        ".offer-card, " +
        ".ai-section, " +
        ".final-cta"
    );


revealElements.forEach(
    function (element) {

        element.classList.add(
            "reveal"
        );

    }
);


const revealObserver =
    new IntersectionObserver(
        function (entries) {

            entries.forEach(
                function (entry) {

                    if (
                        entry.isIntersecting
                    ) {

                        entry.target.classList.add(
                            "visible"
                        );

                        revealObserver.unobserve(
                            entry.target
                        );

                    }

                }
            );

        },
        {
            threshold: 0.12
        }
    );


revealElements.forEach(
    function (element) {

        revealObserver.observe(
            element
        );

    }
);


/* =========================================================
   OFFER BUTTONS
========================================================= */

const offerButtons =
    document.querySelectorAll(
        ".offer-bottom button"
    );


offerButtons.forEach(
    function (button) {

        button.addEventListener(
            "click",
            function () {

                console.log(
                    "Ouverture de l'offre"
                );

            }
        );

    }
);


/* =========================================================
   SMALL OFFER HOVER
========================================================= */

const smallOffers =
    document.querySelectorAll(
        ".small-offer"
    );


smallOffers.forEach(
    function (card) {

        card.addEventListener(
            "mouseenter",
            function () {

                card.style.cursor =
                    "pointer";

            }
        );

    }
);


/* =========================================================
   SMOOTH LINKS
========================================================= */

const links =
    document.querySelectorAll(
        'a[href^="#"]'
    );


links.forEach(
    function (link) {

        link.addEventListener(
            "click",
            function (event) {

                const targetId =
                    link.getAttribute(
                        "href"
                    );

                if (
                    !targetId ||
                    targetId === "#"
                ) {

                    return;

                }

                const target =
                    document.querySelector(
                        targetId
                    );

                if (!target) {

                    return;

                }

                event.preventDefault();

                target.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });

            }
        );

    }
);


/* =========================================================
   CONSOLE
========================================================= */

console.log(
    "STAGEX Marrakech loaded successfully."
);