// Habit filtering for the edit/add page
window.HabitEditFilter = (function() {
    let filterTimeout = null;

    function filterHabits(searchTerm) {
        // Clear any pending filter operation
        if (filterTimeout) {
            clearTimeout(filterTimeout);
        }

        // Debounce the filtering to avoid too many DOM updates
        filterTimeout = setTimeout(() => {
            const normalizedSearch = searchTerm.toLowerCase().trim();
            const cards = document.querySelectorAll('.habit-edit-card');
            
            cards.forEach(card => {
                if (!normalizedSearch) {
                    // Show all cards if search is empty
                    card.style.display = '';
                    return;
                }

                // Get the habit name from the data attribute
                const habitName = card.getAttribute('data-habit-name');
                if (!habitName) {
                    // If no name attribute, try to get from the input field
                    const nameInput = card.querySelector('input[type="text"]');
                    if (nameInput && nameInput.value.toLowerCase().includes(normalizedSearch)) {
                        card.style.display = '';
                    } else {
                        card.style.display = 'none';
                    }
                } else if (habitName.toLowerCase().includes(normalizedSearch)) {
                    card.style.display = '';
                } else {
                    card.style.display = 'none';
                }
            });

            // Update result count
            updateResultCount();
        }, 150); // 150ms debounce delay
    }

    function updateResultCount() {
        const cards = document.querySelectorAll('.habit-edit-card');
        const visibleCards = Array.from(cards).filter(card => card.style.display !== 'none');
        const countElement = document.getElementById('habit-filter-count');
        
        if (countElement) {
            if (visibleCards.length === cards.length) {
                countElement.textContent = `Showing all ${cards.length} habits`;
            } else {
                countElement.textContent = `Showing ${visibleCards.length} of ${cards.length} habits`;
            }
        }
    }

    function clearFilter() {
        const input = document.getElementById('habit-filter-input');
        if (input) {
            input.value = '';
            filterHabits('');
        }
    }

    // Initialize on page load
    document.addEventListener('DOMContentLoaded', function() {
        const input = document.getElementById('habit-filter-input');
        if (input) {
            // Add event listener for real-time filtering
            input.addEventListener('input', function(e) {
                filterHabits(e.target.value);
            });

            // Add clear button functionality
            const clearBtn = document.getElementById('habit-filter-clear');
            if (clearBtn) {
                clearBtn.addEventListener('click', clearFilter);
            }
        }
    });

    // Public API
    return {
        filterHabits: filterHabits,
        clearFilter: clearFilter
    };
})();