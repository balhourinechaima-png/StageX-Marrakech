const API_NOTIFICATIONS = "http://127.0.0.1:5000/api/notifications";

async function chargerNotifications() {
    const container = document.getElementById("notificationsContainer");
    const message = document.getElementById("notificationsMessage");

    container.innerHTML = "";
    message.textContent = "Chargement...";

    try {
        const response = await fetch(API_NOTIFICATIONS, {
            credentials: "include"
        });

        if (response.status === 401) {
            window.location.href = "connexion.html";
            return;
        }

        const notifications = await response.json();

        if (!response.ok) {
            throw new Error(notifications.error || "Erreur de chargement");
        }

        message.textContent = "";

        if (notifications.length === 0) {
            container.innerHTML = "<p>Aucune notification pour le moment.</p>";
            return;
        }

        notifications.forEach(notification => {
            const card = document.createElement("div");
            card.className = "notification-card";

            const titre = document.createElement("h3");
            titre.textContent = notification.titre;

            const contenu = document.createElement("p");
            contenu.textContent = notification.message;

            const date = document.createElement("small");
            date.textContent = notification.date_creation;

            card.append(titre, contenu, date);

            if (notification.lu === 0) {
                card.classList.add("notification-non-lue");

                const bouton = document.createElement("button");
                bouton.textContent = "Marquer comme lu";

                bouton.addEventListener("click", () => {
                    marquerCommeLu(notification.id);
                });

                card.appendChild(bouton);
            } else {
                const statut = document.createElement("span");
                statut.textContent = "Lu";
                card.appendChild(statut);
            }

            container.appendChild(card);
        });

    } catch (error) {
        message.textContent = error.message;
    }
}

async function marquerCommeLu(id) {
    try {
        const response = await fetch(
            `${API_NOTIFICATIONS}/${id}/lu`,
            {
                method: "PATCH",
                credentials: "include"
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Erreur");
        }

        await chargerNotifications();

    } catch (error) {
        alert(error.message);
    }
}

chargerNotifications();