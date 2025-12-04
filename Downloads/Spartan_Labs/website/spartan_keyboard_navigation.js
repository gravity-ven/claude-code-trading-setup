/**
 * Spartan Keyboard Navigation
 * Global keyboard shortcuts for navigation
 */

(function() {
    'use strict';

    const shortcuts = {
        'h': () => window.location.href = '/index.html',  // Home
        'g': () => window.location.href = '/global_capital_flow_swing_trading.html',  // Global
        'e': () => window.location.href = '/elite_trading_strategies.html',  // Elite
        'd': () => window.location.href = '/daily_planet.html',  // Daily
        'b': () => window.location.href = '/barometers.html',  // Barometers
        '/': () => document.querySelector('input[type="search"], input[type="text"]')?.focus(),  // Search
        '?': () => showKeyboardHelp()  // Help
    };

    function handleGlobalKeypress(event) {
        // Ignore if typing in input field
        if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
            return;
        }

        // Ignore if modifier keys pressed
        if (event.ctrlKey || event.altKey || event.metaKey) {
            return;
        }

        const key = event.key.toLowerCase();
        const handler = shortcuts[key];

        if (handler) {
            event.preventDefault();
            handler();
        }
    }

    function showKeyboardHelp() {
        const helpText = `
Keyboard Shortcuts:
• h - Home
• g - Global Capital Flow
• e - Elite Trading Strategies
• d - Daily Planet
• b - Economic Barometers
• / - Focus search
• ? - Show this help
• Esc - Close dialogs
• Arrow keys - Navigate dropdowns
        `.trim();

        if (window.confirm(helpText + '\n\nClose this dialog?')) {
            return;
        }
    }

    // Add global keyboard event listener
    document.addEventListener('keydown', handleGlobalKeypress);

    // Escape key closes modals/dialogs
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal, .dialog, .popup').forEach(el => {
                el.style.display = 'none';
                el.classList.remove('active', 'open');
            });
        }
    });

    console.log('Spartan Keyboard Navigation loaded. Press "?" for help.');

})();
