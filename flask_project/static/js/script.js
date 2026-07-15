// Menu mobile (burger) : ouverture/fermeture du panneau de navigation
function toggleMobile() {
    const menu = document.getElementById('mobile-menu');
    const overlay = document.getElementById('mobile-overlay');
    if (!menu || !overlay) return;

    if (menu.style.display === 'flex') {
        closeMobile();
        return;
    }

    overlay.style.display = 'block';
    menu.style.display = 'flex';
    requestAnimationFrame(() => { menu.style.transform = 'translateX(0)'; });
}

function closeMobile() {
    const menu = document.getElementById('mobile-menu');
    const overlay = document.getElementById('mobile-overlay');
    if (!menu || !overlay) return;

    menu.style.transform = 'translateX(100%)';
    overlay.style.display = 'none';
    setTimeout(() => { menu.style.display = 'none'; }, 300);
}

document.addEventListener('DOMContentLoaded', () => {
    // 1. Sélection des éléments du DOM
    const searchInput = document.querySelector('.search-bar-modern input');
    const clearBtn = document.querySelector('.search-bar-modern .clear-btn');
    const resultsContainer = document.querySelector('.search-results-modern');

    if (!searchInput || !resultsContainer) return; // Sécurité si les éléments n'existent pas sur la page

    // 2. Fonction de Debounce pour la performance
    function debounce(func, delay = 300) {
        let timer;
        return (...args) => {
            clearTimeout(timer);
            timer = setTimeout(() => func.apply(this, args), delay);
        };
    }

    // 3. Logique de recherche (Simulée ici, remplace par un fetch() si besoin)
    const performSearch = async (query) => {
        if (query.trim() === '') {
            resultsContainer.classList.remove('active');
            return;
        }

        // Exemple de structure de données correspondant à ton CSS
        // En production, tu feras : const response = await fetch(`/api/search?q=${query}`); const data = await response.json();
        const mockData = [
            { title: "Mamadou Diallo", desc: "Professeur de Mathématiques", type: "prof", icon: "fa-calculator" },
            { title: "Awa Ndoye", desc: "Étudiante en Master Physique", type: "student", icon: "fa-atom" }
        ];

        // Filtrage de démonstration
        const filtered = mockData.filter(item => 
            item.title.toLowerCase().includes(query.toLowerCase()) || 
            item.desc.toLowerCase().includes(query.toLowerCase())
        );

        renderResults(filtered);
    };

    // 4. Rendu des résultats en injectant le HTML qui match ton CSS
    const renderResults = (results) => {
        resultsContainer.innerHTML = ''; // On vide les anciens résultats

        if (results.length === 0) {
            resultsContainer.innerHTML = `<div class="no-results">Aucun résultat trouvé</div>`;
            resultsContainer.classList.add('active');
            return;
        }

        // Section "Tuteurs" par exemple
        const sectionHeader = document.createElement('div');
        sectionHeader.className = 'result-section';
        sectionHeader.textContent = 'Tuteurs disponibles';
        resultsContainer.appendChild(sectionHeader);

        // Ajout des éléments
        results.forEach(item => {
            const itemTypeClass = item.type === 'prof' ? 'tutor-type-prof' : 'tutor-type-student';
            const itemTypeText = item.type === 'prof' ? 'Prof' : 'Étudiant';

            const resultItem = document.createElement('div');
            resultItem.className = 'search-result-item-modern';
            resultItem.innerHTML = `
                <div class="result-icon"><i class="fas ${item.icon}"></i></div>
                <div class="result-info">
                    <div class="result-title">${item.title}</div>
                    <div class="result-desc">${item.desc}</div>
                </div>
                <span class="result-tag ${itemTypeClass}">${itemTypeText}</span>
            `;

            // Action lors du clic sur un résultat
            resultItem.addEventListener('click', () => {
                searchInput.value = item.title;
                resultsContainer.classList.remove('active');
                // Redirection ou action ici (ex: window.location.href = `/tuteur/${item.id}`)
            });

            resultsContainer.appendChild(resultItem);
        });

        resultsContainer.classList.add('active');
    };

    // 5. Écouteurs d'événements (Event Listeners)

    // Écoute de la saisie avec debounce
    searchInput.addEventListener('input', debounce((e) => {
        const value = e.target.value;
        
        // Gestion du bouton "Clear" (X)
        if (value.length > 0) {
            clearBtn.classList.add('visible');
        } else {
            clearBtn.classList.remove('visible');
            resultsContainer.classList.remove('active');
        }

        performSearch(value);
    }, 250)); // 250ms d'attente avant de lancer la recherche

    // Clic sur le bouton de réinitialisation (Clear)
    clearBtn.addEventListener('click', () => {
        searchInput.value = '';
        clearBtn.classList.remove('visible');
        resultsContainer.classList.remove('active');
        searchInput.focus();
    });

    // Fermer les résultats si on clique en dehors de la barre de recherche
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-bar-modern') && !e.target.closest('.search-results-modern')) {
            resultsContainer.classList.remove('active');
        }
    });

    // Réafficher les résultats si l'input récupère le focus et n'est pas vide
    searchInput.addEventListener('focus', () => {
        if (searchInput.value.trim() !== '' && resultsContainer.children.length > 0) {
            resultsContainer.classList.add('active');
        }
    });
});