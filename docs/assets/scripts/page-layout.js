// Component Loading Functions
function loadComponents() {
    loadHeader();
    loadFooter();
}

function loadHeader() {
    fetch('assets/components/header.html')
        .then(response => response.text())
        .then(data => {
            document.getElementById('header').innerHTML = data;
            updateHeaderState();
        })
        .catch(error => console.error('Error loading header:', error));
}

function loadFooter() {
    fetch('assets/components/footer.html')
        .then(response => response.text())
        .then(data => {
            document.getElementById('footer').innerHTML = data;
        })
        .catch(error => console.error('Error loading footer:', error));
}

function updateHeaderState() {
    // Get current page from URL
    const currentPage = getCurrentPage();

    // Update subtitle
    const subtitle = document.getElementById('page-subtitle');
    if (subtitle) {
        subtitle.textContent = getPageSubtitle(currentPage);
    }

    // Highlight current nav item
    const currentLink = document.querySelector(`[data-page="${currentPage}"]`);
    if (currentLink) {
        currentLink.classList.add('text-blue-300', 'font-bold', 'bg-slate-600', 'px-3', 'py-1', 'rounded');
    }
}

function getCurrentPage() {
    const path = window.location.pathname;
    if (path.includes('player-metrics-dashboard')) return 'metrics';
    if (path.includes('recent-tournaments')) return 'tournaments';
    return 'home';
}

function getPageSubtitle(page) {
    const subtitles = {
        'home': 'Welcome',
        'metrics': 'Player Metrics',
        'tournaments': 'Tournament History'
    };
    return subtitles[page] || 'Welcome';
}

// Initialize everything when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Load components first
    loadComponents();
});