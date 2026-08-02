document.addEventListener("DOMContentLoaded", () => {
    const modal = document.querySelector("#thread-modal");
    const modalPanel = modal?.querySelector(
        ".thread-modal__panel"
    );
    const modalContent = document.querySelector(
        "#thread-modal-content"
    );

    if (!modal || !modalPanel || !modalContent) {
        return;
    }

    let lastFocusedElement = null;
    let pageNeedsRefresh = false;

    function isInteractiveElement(element) {
        return Boolean(
            element.closest(
                "a, button, form, input, select, textarea, label"
            )
        );
    }

    async function openThreadModal(threadId, triggerElement) {
        lastFocusedElement = triggerElement;

        modalContent.innerHTML =
            "<p>Loading thread details...</p>";

        modal.classList.add("thread-modal--open");
        modal.setAttribute("aria-hidden", "false");
        document.body.classList.add("modal-open");

        modalPanel.focus();

        try {
            const response = await fetch(
                `/threads/${threadId}/details`,
                {
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                    },
                }
            );

            if (!response.ok) {
                throw new Error(
                    `Unable to load thread: ${response.status}`
                );
            }

            modalContent.innerHTML = await response.text();
        } catch (error) {
            console.error(error);

            modalContent.innerHTML = `
                <p>
                    The thread details could not be loaded.
                    Please try again.
                </p>
            `;
        }
    }

    function closeThreadModal() {
        if (pageNeedsRefresh) {
            window.location.reload();
            return;
        }

        modal.classList.remove("thread-modal--open");
        modal.setAttribute("aria-hidden", "true");
        document.body.classList.remove("modal-open");

        modalContent.innerHTML =
            "<p>Loading thread details...</p>";

        if (lastFocusedElement) {
            lastFocusedElement.focus();
        }
    }

    document.addEventListener("click", (event) => {
        const closeButton = event.target.closest(
            "[data-modal-close]"
        );

        if (closeButton) {
            closeThreadModal();
            return;
        }

        const card = event.target.closest(
            "[data-thread-card]"
        );

        if (!card) {
            return;
        }

        if (
            isInteractiveElement(event.target) &&
            !event.target.closest("[data-open-thread]")
        ) {
            return;
        }

        openThreadModal(
            card.dataset.threadId,
            event.target
        );
    });

    document.addEventListener("keydown", (event) => {
        if (
            event.key === "Escape" &&
            modal.classList.contains(
                "thread-modal--open"
            )
        ) {
            closeThreadModal();
            return;
        }

        const card = event.target.closest(
            "[data-thread-card]"
        );

        if (
            card &&
            (event.key === "Enter" || event.key === " ")
        ) {
            if (isInteractiveElement(event.target)) {
                return;
            }

            event.preventDefault();

            openThreadModal(
                card.dataset.threadId,
                card
            );
        }
    });

    document.addEventListener("submit", async (event) => {
        const form = event.target.closest(
            "[data-modal-status-form]"
        );

        if (!form) {
            return;
        }

        event.preventDefault();

        const submitButton = form.querySelector(
            'button[type="submit"]'
        );

        if (submitButton) {
            submitButton.disabled = true;
            submitButton.textContent = "Updating...";
        }

        try {
            const response = await fetch(
                form.action,
                {
                    method: "POST",
                    body: new FormData(form),
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                    },
                }
            );

            if (!response.ok) {
                throw new Error(
                    `Unable to update status: ${response.status}`
                );
            }

            /*
             * Reloading preserves the current URL, including
             * status filters and search queries. It also refreshes
             * counts and removes cards that no longer belong in
             * the current view.
             */
            pageNeedsRefresh = true;

            if (submitButton) {
                submitButton.disabled = false;
                submitButton.textContent = "Saved";

                setTimeout(() => {
                    submitButton.textContent = "Update status";
                }, 1500);
            }
        } catch (error) {
            console.error(error);

            if (submitButton) {
                submitButton.disabled = false;
                submitButton.textContent =
                    "Update status";
            }

            window.alert(
                "The status could not be updated."
            );
        }
    });
});