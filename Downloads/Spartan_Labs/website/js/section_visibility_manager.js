// Section Visibility Manager
// Allows users to hide/remove sections and persist preferences
// Spartan Research Station

class SectionVisibilityManager {
    constructor() {
        this.storageKey = 'spartan_hidden_sections';
        this.hiddenSections = new Set();
        this.sections = [];

        this.init();
    }

    init() {
        console.log('👁️ Initializing Section Visibility Manager...');

        // Load hidden sections from localStorage
        this.loadHiddenSections();

        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.setupSections();
            });
        } else {
            this.setupSections();
        }

        console.log('✅ Section Visibility Manager initialized');
    }

    /**
     * Load hidden sections from localStorage
     */
    loadHiddenSections() {
        try {
            const stored = localStorage.getItem(this.storageKey);
            if (stored) {
                const hiddenArray = JSON.parse(stored);
                this.hiddenSections = new Set(hiddenArray);
                console.log(`📋 Loaded ${this.hiddenSections.size} hidden sections from localStorage`);
            }
        } catch (error) {
            console.error('❌ Failed to load hidden sections:', error);
            this.hiddenSections = new Set();
        }
    }

    /**
     * Save hidden sections to localStorage
     */
    saveHiddenSections() {
        try {
            const hiddenArray = Array.from(this.hiddenSections);
            localStorage.setItem(this.storageKey, JSON.stringify(hiddenArray));
            console.log(`💾 Saved ${this.hiddenSections.size} hidden sections to localStorage`);
        } catch (error) {
            console.error('❌ Failed to save hidden sections:', error);
        }
    }

    /**
     * Setup sections with hide buttons
     */
    setupSections() {
        // Find all hideable sections
        const hideableSections = document.querySelectorAll('[data-hideable="true"]');

        if (hideableSections.length === 0) {
            console.warn('⚠️ No hideable sections found. Add data-hideable="true" to sections you want to make hideable.');
            return;
        }

        hideableSections.forEach(section => {
            const sectionId = section.getAttribute('data-section-id');

            if (!sectionId) {
                console.warn('⚠️ Hideable section missing data-section-id:', section);
                return;
            }

            // Add to sections array
            this.sections.push({
                id: sectionId,
                element: section,
                name: section.getAttribute('data-section-name') || sectionId
            });

            // Add hide button if not already present
            if (!section.querySelector('.hide-section-btn')) {
                this.addHideButton(section, sectionId);
            }

            // Hide section if it's in hidden list
            if (this.hiddenSections.has(sectionId)) {
                this.hideSection(sectionId, false); // Don't save again
            }
        });

        // Add "Show Hidden Sections" button
        this.addShowHiddenButton();

        console.log(`✅ Setup ${this.sections.length} hideable sections`);
    }

    /**
     * Add hide button to a section
     */
    addHideButton(section, sectionId) {
        const hideButton = document.createElement('button');
        hideButton.className = 'hide-section-btn';
        hideButton.innerHTML = '✕';
        hideButton.title = 'Hide this section';
        hideButton.setAttribute('aria-label', 'Hide section');

        // Style the hide button
        hideButton.style.cssText = `
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(220, 20, 60, 0.8);
            color: white;
            border: none;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            font-size: 1.2rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
            z-index: 10;
            opacity: 0.7;
        `;

        // Hover effect
        hideButton.addEventListener('mouseenter', () => {
            hideButton.style.opacity = '1';
            hideButton.style.transform = 'scale(1.1)';
            hideButton.style.background = 'rgba(220, 20, 60, 1)';
        });

        hideButton.addEventListener('mouseleave', () => {
            hideButton.style.opacity = '0.7';
            hideButton.style.transform = 'scale(1)';
            hideButton.style.background = 'rgba(220, 20, 60, 0.8)';
        });

        // Click handler
        hideButton.addEventListener('click', (e) => {
            e.stopPropagation();
            this.hideSection(sectionId, true);
        });

        // Make section position relative if not already
        const sectionPosition = window.getComputedStyle(section).position;
        if (sectionPosition === 'static') {
            section.style.position = 'relative';
        }

        // Add button to section
        section.appendChild(hideButton);
    }

    /**
     * Hide a section
     */
    hideSection(sectionId, save = true) {
        const sectionData = this.sections.find(s => s.id === sectionId);

        if (!sectionData) {
            console.error(`❌ Section not found: ${sectionId}`);
            return;
        }

        // Add smooth fade-out animation
        sectionData.element.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        sectionData.element.style.opacity = '0';
        sectionData.element.style.transform = 'scale(0.95)';

        setTimeout(() => {
            sectionData.element.style.display = 'none';

            // Add to hidden sections
            this.hiddenSections.add(sectionId);

            if (save) {
                this.saveHiddenSections();
            }

            console.log(`👁️ Hidden section: ${sectionData.name}`);

            // Update show hidden button count
            this.updateShowHiddenButton();
        }, 300);
    }

    /**
     * Show a hidden section
     */
    showSection(sectionId, save = true) {
        const sectionData = this.sections.find(s => s.id === sectionId);

        if (!sectionData) {
            console.error(`❌ Section not found: ${sectionId}`);
            return;
        }

        // Remove from hidden sections
        this.hiddenSections.delete(sectionId);

        // Show section with fade-in animation
        sectionData.element.style.display = '';
        sectionData.element.style.opacity = '0';
        sectionData.element.style.transform = 'scale(0.95)';

        setTimeout(() => {
            sectionData.element.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            sectionData.element.style.opacity = '1';
            sectionData.element.style.transform = 'scale(1)';
        }, 10);

        if (save) {
            this.saveHiddenSections();
        }

        console.log(`👁️ Shown section: ${sectionData.name}`);

        // Update show hidden button count
        this.updateShowHiddenButton();
    }

    /**
     * Show all hidden sections
     */
    showAllHiddenSections() {
        const hiddenArray = Array.from(this.hiddenSections);

        if (hiddenArray.length === 0) {
            console.log('ℹ️ No hidden sections to show');
            return;
        }

        hiddenArray.forEach(sectionId => {
            this.showSection(sectionId, false);
        });

        // Clear hidden sections
        this.hiddenSections.clear();
        this.saveHiddenSections();

        console.log(`✅ Showed all ${hiddenArray.length} hidden sections`);
    }

    /**
     * Add "Show Hidden Sections" button
     */
    addShowHiddenButton() {
        // Check if button already exists
        if (document.getElementById('show-hidden-sections-btn')) {
            return;
        }

        const buttonContainer = document.createElement('div');
        buttonContainer.id = 'show-hidden-sections-container';
        buttonContainer.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 1000;
        `;

        const button = document.createElement('button');
        button.id = 'show-hidden-sections-btn';
        button.innerHTML = `
            <span style="margin-right: 8px;">👁️</span>
            <span id="hidden-count">0</span> Hidden Sections
        `;
        button.style.cssText = `
            background: linear-gradient(135deg, #8B0000 0%, #DC143C 100%);
            color: white;
            border: 2px solid #DC143C;
            border-radius: 8px;
            padding: 12px 20px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            display: none;
            align-items: center;
            gap: 8px;
            box-shadow: 0 4px 12px rgba(220, 20, 60, 0.4);
            transition: all 0.3s ease;
        `;

        // Hover effect
        button.addEventListener('mouseenter', () => {
            button.style.transform = 'translateY(-2px)';
            button.style.boxShadow = '0 6px 16px rgba(220, 20, 60, 0.6)';
        });

        button.addEventListener('mouseleave', () => {
            button.style.transform = 'translateY(0)';
            button.style.boxShadow = '0 4px 12px rgba(220, 20, 60, 0.4)';
        });

        // Click handler
        button.addEventListener('click', () => {
            this.showAllHiddenSections();
        });

        buttonContainer.appendChild(button);
        document.body.appendChild(buttonContainer);

        // Update initial count
        this.updateShowHiddenButton();
    }

    /**
     * Update show hidden button count
     */
    updateShowHiddenButton() {
        const button = document.getElementById('show-hidden-sections-btn');
        const countSpan = document.getElementById('hidden-count');

        if (!button || !countSpan) return;

        const hiddenCount = this.hiddenSections.size;

        countSpan.textContent = hiddenCount;

        if (hiddenCount > 0) {
            button.style.display = 'flex';
        } else {
            button.style.display = 'none';
        }
    }

    /**
     * Get list of hidden sections
     */
    getHiddenSections() {
        return Array.from(this.hiddenSections).map(sectionId => {
            const sectionData = this.sections.find(s => s.id === sectionId);
            return {
                id: sectionId,
                name: sectionData ? sectionData.name : 'Unknown'
            };
        });
    }

    /**
     * Clear all hidden sections (reset)
     */
    resetAllSections() {
        this.hiddenSections.clear();
        this.saveHiddenSections();

        // Show all sections
        this.sections.forEach(sectionData => {
            sectionData.element.style.display = '';
            sectionData.element.style.opacity = '1';
            sectionData.element.style.transform = 'scale(1)';
        });

        this.updateShowHiddenButton();

        console.log('✅ Reset all sections - all visible');
    }

    /**
     * Export hidden sections list
     */
    exportHiddenSections() {
        const hiddenList = this.getHiddenSections();
        console.log('📋 Hidden Sections:', hiddenList);
        return hiddenList;
    }
}

// Initialize global instance
window.sectionVisibilityManager = new SectionVisibilityManager();

// Debug helpers
window.showAllHiddenSections = () => {
    window.sectionVisibilityManager.showAllHiddenSections();
};

window.getHiddenSections = () => {
    return window.sectionVisibilityManager.getHiddenSections();
};

window.resetAllSections = () => {
    window.sectionVisibilityManager.resetAllSections();
};

console.log('✅ Section Visibility Manager loaded successfully');
