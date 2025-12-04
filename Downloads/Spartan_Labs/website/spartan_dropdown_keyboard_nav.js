/**
 * Spartan Dropdown Keyboard Navigation
 * Provides keyboard shortcuts for dropdown menus
 */

(function() {
    'use strict';

    // Initialize keyboard navigation for dropdowns
    function initDropdownNavigation() {
        const dropdowns = document.querySelectorAll('.dropdown, [role="menu"]');

        dropdowns.forEach(dropdown => {
            dropdown.addEventListener('keydown', handleDropdownKeypress);
        });
    }

    function handleDropdownKeypress(event) {
        const key = event.key;

        switch(key) {
            case 'ArrowDown':
                event.preventDefault();
                focusNextItem(event.currentTarget);
                break;
            case 'ArrowUp':
                event.preventDefault();
                focusPreviousItem(event.currentTarget);
                break;
            case 'Escape':
                closeDropdown(event.currentTarget);
                break;
            case 'Enter':
            case ' ':
                event.preventDefault();
                selectCurrentItem(event.currentTarget);
                break;
        }
    }

    function focusNextItem(dropdown) {
        const items = Array.from(dropdown.querySelectorAll('[role="menuitem"], a, button'));
        const currentIndex = items.findIndex(item => item === document.activeElement);
        const nextIndex = (currentIndex + 1) % items.length;
        items[nextIndex]?.focus();
    }

    function focusPreviousItem(dropdown) {
        const items = Array.from(dropdown.querySelectorAll('[role="menuitem"], a, button'));
        const currentIndex = items.findIndex(item => item === document.activeElement);
        const prevIndex = currentIndex <= 0 ? items.length - 1 : currentIndex - 1;
        items[prevIndex]?.focus();
    }

    function closeDropdown(dropdown) {
        dropdown.classList.remove('open', 'active');
        dropdown.querySelector('[role="button"]')?.focus();
    }

    function selectCurrentItem(dropdown) {
        if (document.activeElement.tagName === 'A' || document.activeElement.tagName === 'BUTTON') {
            document.activeElement.click();
        }
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initDropdownNavigation);
    } else {
        initDropdownNavigation();
    }

})();
