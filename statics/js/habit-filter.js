// Use IIFE to avoid global variables
window.HabitFilter = (function() {
    let currentFilter = null;
    let enabled = false;

    function setEnabled(value) {
        enabled = value;
    }

    function filterHabits(letter) {
        // Don't filter if disabled
        if (!enabled) {
            return;
        }

        // Toggle filter if clicking same letter
        if (currentFilter === letter) {
            currentFilter = null;
        } else {
            currentFilter = letter;
        }

        // Update button states
        document.querySelectorAll('.letter-filter-btn').forEach(btn => {
            if (btn.textContent === currentFilter) {
                btn.classList.add('active-filter');
            } else {
                btn.classList.remove('active-filter');
            }
        });

        // Filter cards
        const cards = document.querySelectorAll('.habit-card');
        cards.forEach(card => {
            if (!currentFilter) {
                // No filter, show all
                card.style.display = '';
                return;
            }

            // Check if any part of the habit name (split by ||) starts with the filter letter
            const filterLetters = card.getAttribute('data-filter-letters');
            if (filterLetters) {
                // Use the pre-computed filter letters
                const letters = filterLetters.split(',');
                if (letters.includes(currentFilter)) {
                    card.style.display = '';
                } else {
                    card.style.display = 'none';
                }
            } else {
                // Fallback to checking the full name (for backward compatibility)
                const name = card.getAttribute('data-name').toUpperCase();
                if (name.startsWith(currentFilter)) {
                    card.style.display = '';
                } else {
                    card.style.display = 'none';
                }
            }
        });
    }

    // Public API
    return {
        setEnabled: setEnabled,
        filterHabits: filterHabits
    };
})();
