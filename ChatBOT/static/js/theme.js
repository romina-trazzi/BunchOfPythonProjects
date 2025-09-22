/**
 * Advanced Theme Management System
 * Gestisce il tema dell'applicazione con animazioni fluide e persistenza
 */

class ThemeManager {
    constructor() {
        this.themes = {
            light: {
                icon: '🌞',
                name: 'light'
            },
            dark: {
                icon: '🌙', 
                name: 'dark'
            }
        };
        
        this.currentTheme = 'light';
        this.isTransitioning = false;
        
        this.init();
    }

    init() {
        // Carica tema salvato o usa preferenze sistema
        this.currentTheme = this.getSavedTheme();
        
        // Applica tema iniziale senza animazioni
        this.applyTheme(this.currentTheme, false);
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Inizializza animazioni
        this.initializeAnimations();
        
        // Rileva cambiamenti preferenze sistema
        this.watchSystemTheme();
    }

    getSavedTheme() {
        const saved = localStorage.getItem('theme');
        if (saved && this.themes[saved]) {
            return saved;
        }
        
        // Fallback alle preferenze sistema
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        
        return 'light';
    }

    applyTheme(theme, animate = true) {
        if (this.isTransitioning) return;
        
        const themeConfig = this.themes[theme];
        if (!themeConfig) return;
        
        this.isTransitioning = animate;
        
        if (animate) {
            this.addTransitionClass();
        }
        
        // Aggiorna attributo data-theme per CSS
        document.documentElement.setAttribute('data-theme', theme);
        
        // Aggiorna legacy theme link se esiste
        this.updateLegacyThemeLink(theme);
        
        // Aggiorna toggle UI
        this.updateToggleUI(theme);
        
        // Salva preferenza
        localStorage.setItem('theme', theme);
        
        this.currentTheme = theme;
        
        // Rimuovi classe transizione dopo animazione
        if (animate) {
            setTimeout(() => {
                this.removeTransitionClass();
                this.isTransitioning = false;
            }, 300);
        }
        
        // Dispatch evento personalizzato
        this.dispatchThemeChange(theme);
    }

    updateLegacyThemeLink(theme) {
        const themeLink = document.getElementById('theme-style');
        if (themeLink) {
            themeLink.href = `/static/css/${theme}.css`;
        }
    }

    updateToggleUI(theme) {
        const themeConfig = this.themes[theme];
        
        // Aggiorna toggle checkbox se esiste
        const toggle = document.getElementById('darkToggle');
        if (toggle) {
            toggle.checked = theme === 'dark';
        }
        
        // Aggiorna icona se esiste
        const icon = document.getElementById('themeIcon');
        if (icon) {
            icon.textContent = themeConfig.icon;
            icon.style.transform = 'scale(0.8)';
            setTimeout(() => {
                icon.style.transform = 'scale(1)';
            }, 150);
        }
        
        // Aggiorna icone nel toggle custom
        this.updateCustomToggleIcons(theme);
    }

    updateCustomToggleIcons(theme) {
        const sunIcon = document.querySelector('.theme-icon.sun');
        const moonIcon = document.querySelector('.theme-icon.moon');
        
        if (sunIcon && moonIcon) {
            if (theme === 'dark') {
                sunIcon.style.opacity = '0.3';
                moonIcon.style.opacity = '1';
            } else {
                sunIcon.style.opacity = '1';
                moonIcon.style.opacity = '0.3';
            }
        }
    }

    addTransitionClass() {
        document.documentElement.classList.add('theme-transitioning');
    }

    removeTransitionClass() {
        document.documentElement.classList.remove('theme-transitioning');
    }

    setupEventListeners() {
        // Legacy toggle support
        const toggle = document.getElementById('darkToggle');
        if (toggle) {
            toggle.addEventListener('change', (e) => {
                const newTheme = e.target.checked ? 'dark' : 'light';
                this.toggleTheme(newTheme);
            });
        }
        
        // Custom toggle support
        const customToggle = document.querySelector('.theme-toggle');
        if (customToggle) {
            customToggle.addEventListener('click', () => {
                this.toggleTheme();
            });
        }
        
        // Keyboard shortcut (Ctrl/Cmd + Shift + T)
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'T') {
                e.preventDefault();
                this.toggleTheme();
            }
        });
    }

    toggleTheme(specificTheme = null) {
        if (this.isTransitioning) return;
        
        const newTheme = specificTheme || (this.currentTheme === 'dark' ? 'light' : 'dark');
        this.applyTheme(newTheme, true);
    }

    watchSystemTheme() {
        if (!window.matchMedia) return;
        
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        
        const handleSystemThemeChange = (e) => {
            // Solo se l'utente non ha una preferenza salvata
            if (!localStorage.getItem('theme')) {
                const systemTheme = e.matches ? 'dark' : 'light';
                this.applyTheme(systemTheme, true);
            }
        };
        
        // Support per browser moderni
        if (mediaQuery.addListener) {
            mediaQuery.addListener(handleSystemThemeChange);
        } else {
            mediaQuery.addEventListener('change', handleSystemThemeChange);
        }
    }

    dispatchThemeChange(theme) {
        const event = new CustomEvent('themeChanged', {
            detail: { theme, themeConfig: this.themes[theme] }
        });
        document.dispatchEvent(event);
    }

    initializeAnimations() {
        // Intersection Observer per animazioni fade-in
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, observerOptions);

        // Osserva tutti gli elementi fade-in
        document.querySelectorAll('.fade-in-up').forEach(el => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(30px)';
            el.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
            observer.observe(el);
        });

        // Effetto parallax ottimizzato
        this.initParallax();
    }

    initParallax() {
        let ticking = false;
        
        const updateParallax = () => {
            const scrolled = window.pageYOffset;
            const parallaxElements = document.querySelectorAll('.floating-element');
            
            parallaxElements.forEach((element, index) => {
                const speed = 0.3 + (index * 0.1); // Velocità diversa per ogni elemento
                const yPos = scrolled * speed;
                element.style.transform = `translate3d(0, ${yPos}px, 0)`;
            });
            
            ticking = false;
        };

        const requestParallaxUpdate = () => {
            if (!ticking) {
                requestAnimationFrame(updateParallax);
                ticking = true;
            }
        };

        // Throttled scroll listener
        window.addEventListener('scroll', requestParallaxUpdate, { passive: true });
    }

    // Metodi pubblici per API esterna
    getCurrentTheme() {
        return this.currentTheme;
    }

    setTheme(theme) {
        if (this.themes[theme]) {
            this.applyTheme(theme, true);
        }
    }

    resetToSystemTheme() {
        localStorage.removeItem('theme');
        const systemTheme = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        this.applyTheme(systemTheme, true);
    }
}

// Stili CSS aggiuntivi per le transizioni
const addThemeTransitionStyles = () => {
    const style = document.createElement('style');
    style.textContent = `
        .theme-transitioning,
        .theme-transitioning *,
        .theme-transitioning *:before,
        .theme-transitioning *:after {
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            transition-delay: 0s !important;
        }
        
        .animate-in {
            animation: slideInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1) forwards;
        }
        
        @keyframes slideInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .theme-toggle {
            user-select: none;
            -webkit-tap-highlight-color: transparent;
        }
        
        #themeIcon {
            transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .floating-element {
            will-change: transform;
        }
    `;
    document.head.appendChild(style);
};

// Inizializzazione
document.addEventListener('DOMContentLoaded', () => {
    addThemeTransitionStyles();
    
    // Crea istanza globale del theme manager
    window.themeManager = new ThemeManager();
    
    // Funzione globale per compatibilità con codice esistente
    window.toggleTheme = () => {
        window.themeManager.toggleTheme();
    };
});

// Event listener per cambiamenti di tema personalizzati
document.addEventListener('themeChanged', (e) => {
    console.log(`Tema cambiato a: ${e.detail.theme}`);
    
    // Aggiorna meta theme-color per mobile
    let metaThemeColor = document.querySelector('meta[name="theme-color"]');
    if (!metaThemeColor) {
        metaThemeColor = document.createElement('meta');
        metaThemeColor.name = 'theme-color';
        document.head.appendChild(metaThemeColor);
    }
    
    const colors = {
        light: '#ffffff',
        dark: '#0f172a'
    };
    
    metaThemeColor.content = colors[e.detail.theme];
});

// Export per moduli ES6 se necessario
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeManager;
}