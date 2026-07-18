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
    const searchInput = document.querySelector('.search-bar-modern input');
    const clearBtn = document.querySelector('.search-bar-modern .clear-btn');
    const resultsContainer = document.querySelector('.search-results-modern');

    function debounce(func, delay = 300) {
        let timer;
        return (...args) => {
            clearTimeout(timer);
            timer = setTimeout(() => func.apply(this, args), delay);
        };
    }

    if (searchInput && resultsContainer) {
        const performSearch = async (query) => {
            if (query.trim() === '') {
                resultsContainer.classList.remove('active');
                return;
            }

            const mockData = [
                { title: "Mamadou Diallo", desc: "Professeur de Mathématiques", type: "prof", icon: "fa-calculator" },
                { title: "Awa Ndoye", desc: "Étudiante en Master Physique", type: "student", icon: "fa-atom" }
            ];

            const filtered = mockData.filter(item =>
                item.title.toLowerCase().includes(query.toLowerCase()) ||
                item.desc.toLowerCase().includes(query.toLowerCase())
            );

            renderResults(filtered);
        };

        const renderResults = (results) => {
            resultsContainer.innerHTML = '';

            if (results.length === 0) {
                resultsContainer.innerHTML = `<div class="no-results">Aucun résultat trouvé</div>`;
                resultsContainer.classList.add('active');
                return;
            }

            const sectionHeader = document.createElement('div');
            sectionHeader.className = 'result-section';
            sectionHeader.textContent = 'Tuteurs disponibles';
            resultsContainer.appendChild(sectionHeader);

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

                resultItem.addEventListener('click', () => {
                    searchInput.value = item.title;
                    resultsContainer.classList.remove('active');
                });

                resultsContainer.appendChild(resultItem);
            });

            resultsContainer.classList.add('active');
        };

        searchInput.addEventListener('input', debounce((e) => {
            const value = e.target.value;

            if (value.length > 0) {
                clearBtn.classList.add('visible');
            } else {
                clearBtn.classList.remove('visible');
                resultsContainer.classList.remove('active');
            }

            performSearch(value);
        }, 250));

        clearBtn.addEventListener('click', () => {
            searchInput.value = '';
            clearBtn.classList.remove('visible');
            resultsContainer.classList.remove('active');
            searchInput.focus();
        });

        document.addEventListener('click', (e) => {
            if (!e.target.closest('.search-bar-modern') && !e.target.closest('.search-results-modern')) {
                resultsContainer.classList.remove('active');
            }
        });

        searchInput.addEventListener('focus', () => {
            if (searchInput.value.trim() !== '' && resultsContainer.children.length > 0) {
                resultsContainer.classList.add('active');
            }
        });
    }
});