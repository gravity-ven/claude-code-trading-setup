# ✅ SECTION VISIBILITY MANAGER - COMPLETE

**Date**: 2025-11-16
**Status**: ✅ FULLY IMPLEMENTED
**Priority**: HIGH - User Customization Feature

---

## 🎯 OBJECTIVE

**User Request**: "Give an option to remove sections/flashcards as the user chooses so that it is not shown again."

Allow users to:
1. Hide individual sections they don't want to see
2. Persist hidden sections across sessions
3. Show all hidden sections with one click
4. Fine-grained control over dashboard layout

---

## ✅ IMPLEMENTATION OVERVIEW

### Core System

**File**: `js/section_visibility_manager.js` (350+ lines)

A comprehensive section visibility management system that:
1. ✅ **Adds hide buttons** to all hideable sections
2. ✅ **Persists hidden sections** using localStorage
3. ✅ **Auto-hides sections** on page load based on preferences
4. ✅ **Floating "Show Hidden" button** to restore sections
5. ✅ **Smooth animations** for hide/show transitions

---

## 🔧 HOW IT WORKS

### Step 1: Mark Sections as Hideable

Add three data attributes to any HTML section you want to make hideable:

```html
<div class="metric-card"
     data-hideable="true"
     data-section-id="us-market-flow"
     data-section-name="US Market Flow">
    <!-- Section content -->
</div>
```

**Required Attributes**:
- `data-hideable="true"` - Enables hide functionality
- `data-section-id="unique-id"` - Unique identifier for the section
- `data-section-name="Display Name"` - Friendly name for debugging

### Step 2: Automatic Setup

On page load, the Section Visibility Manager:
1. Finds all sections with `data-hideable="true"`
2. Adds a hide button (✕) to the top-right corner
3. Loads hidden sections from localStorage
4. Auto-hides previously hidden sections
5. Shows "Show Hidden Sections" button if any sections are hidden

### Step 3: User Interaction

**To Hide a Section**:
- Click the ✕ button in the top-right corner
- Section fades out with smooth animation
- Preference saved to localStorage
- Section remains hidden on page reload

**To Show Hidden Sections**:
- Click the floating "Show Hidden Sections" button (bottom-right)
- All hidden sections fade back in
- Preferences cleared from localStorage

---

## 🎨 HIDE BUTTON STYLING

**Button Properties**:
- Position: Absolute (top-right corner)
- Size: 30px × 30px
- Shape: Circle
- Color: Spartan Red (#DC143C)
- Icon: ✕ (white)
- Opacity: 0.7 (normal), 1.0 (hover)
- Hover effect: Scale 1.1, full opacity, brighter red

**CSS**:
```css
.hide-section-btn {
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
}
```

---

## 🔄 "SHOW HIDDEN SECTIONS" BUTTON

**Floating Button (Bottom-Right)**:
- Position: Fixed (bottom: 20px, right: 20px)
- Background: Spartan Red Gradient (#8B0000 → #DC143C)
- Border: 2px solid #DC143C
- Shadow: 0 4px 12px rgba(220, 20, 60, 0.4)
- Icon: 👁️
- Text: "N Hidden Sections" (where N = count)
- Display: Only visible when sections are hidden
- Hover: Lifts up 2px with enhanced shadow

**Example**:
```
┌─────────────────────────────┐
│  👁️ 3 Hidden Sections      │
└─────────────────────────────┘
```

**Functionality**:
- Click to show all hidden sections
- Auto-hides when no sections are hidden
- Updates count in real-time

---

## 💾 LOCALSTORAGE PERSISTENCE

**Storage Key**: `spartan_hidden_sections`

**Data Format**:
```json
["composite-score", "us-market-flow", "eu-market-flow"]
```

**Persistence Logic**:
```javascript
// Save to localStorage
saveHiddenSections() {
    try {
        const hiddenArray = Array.from(this.hiddenSections);
        localStorage.setItem(this.storageKey, JSON.stringify(hiddenArray));
        console.log(`💾 Saved ${this.hiddenSections.size} hidden sections`);
    } catch (error) {
        console.error('❌ Failed to save hidden sections:', error);
    }
}

// Load from localStorage
loadHiddenSections() {
    try {
        const stored = localStorage.getItem(this.storageKey);
        if (stored) {
            const hiddenArray = JSON.parse(stored);
            this.hiddenSections = new Set(hiddenArray);
            console.log(`📋 Loaded ${this.hiddenSections.size} hidden sections`);
        }
    } catch (error) {
        console.error('❌ Failed to load hidden sections:', error);
        this.hiddenSections = new Set();
    }
}
```

**Benefits**:
- Preferences persist across browser sessions
- Survives page reloads and tab closes
- No server-side storage needed
- Instant load on page open

---

## 🎬 ANIMATIONS

### Hide Animation

**Duration**: 300ms
**Steps**:
1. Fade out: opacity 1 → 0
2. Scale down: scale 1 → 0.95
3. After animation: display = none

**Code**:
```javascript
hideSection(sectionId, save = true) {
    const sectionData = this.sections.find(s => s.id === sectionId);

    // Add smooth fade-out animation
    sectionData.element.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    sectionData.element.style.opacity = '0';
    sectionData.element.style.transform = 'scale(0.95)';

    setTimeout(() => {
        sectionData.element.style.display = 'none';
        this.hiddenSections.add(sectionId);

        if (save) {
            this.saveHiddenSections();
        }
    }, 300);
}
```

### Show Animation

**Duration**: 300ms
**Steps**:
1. display = '' (visible)
2. Start at: opacity 0, scale 0.95
3. Fade in: opacity 0 → 1
4. Scale up: scale 0.95 → 1

**Code**:
```javascript
showSection(sectionId, save = true) {
    const sectionData = this.sections.find(s => s.id === sectionId);

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
}
```

---

## 📊 HIDEABLE SECTIONS ON GLOBAL CAPITAL FLOW PAGE

### Implemented Sections

**Tab 1: Capital Flow Dashboard**

1. **Composite Score Card**
   - ID: `composite-score`
   - Name: "Market Health Composite Score"
   - Contains: Real-time composite score with 4 component scores

2. **US Market Flow**
   - ID: `us-market-flow`
   - Name: "US Market Flow"
   - Contains: S&P 500 flow metrics

3. **European Market Flow**
   - ID: `eu-market-flow`
   - Name: "European Market Flow"
   - Contains: European indices flow

4. **Asian Market Flow**
   - ID: `asia-market-flow`
   - Name: "Asian Market Flow"
   - Contains: Asian indices flow

5. **Emerging Market Flow**
   - ID: `em-market-flow`
   - Name: "Emerging Market Flow"
   - Contains: Emerging market indices

6. **Currency Flow (USD Index)**
   - ID: `currency-flow`
   - Name: "Currency Flow (USD Index)"
   - Contains: USD index metrics

7. **Commodity Flow**
   - ID: `commodity-flow`
   - Name: "Commodity Flow"
   - Contains: Gold/commodity metrics

**Total**: 7 hideable sections (can be expanded to more)

---

## 🔧 DEBUG HELPERS

### Global Functions

**Show All Hidden Sections**:
```javascript
window.showAllHiddenSections();
// Restores all hidden sections
```

**Get Hidden Sections List**:
```javascript
const hidden = window.getHiddenSections();
console.log(hidden);
// Returns: [
//     { id: 'composite-score', name: 'Market Health Composite Score' },
//     { id: 'us-market-flow', name: 'US Market Flow' }
// ]
```

**Reset All Sections**:
```javascript
window.resetAllSections();
// Shows all sections and clears localStorage
```

**Access Manager Instance**:
```javascript
const manager = window.sectionVisibilityManager;
console.log(manager.hiddenSections); // Set of hidden section IDs
console.log(manager.sections);       // Array of all section data
```

---

## 🎯 USE CASES

### For Users

**Scenario 1**: Declutter Dashboard
- User sees composite score, but focuses only on US markets
- Clicks ✕ on European, Asian, Emerging Market flow cards
- Cards fade out and disappear
- Page reloads - cards still hidden
- Dashboard now shows only US-relevant data

**Scenario 2**: Restore Hidden Sections
- User hid 5 sections yesterday
- Now wants to see them again
- Sees "👁️ 5 Hidden Sections" button in bottom-right
- Clicks button
- All 5 sections fade back in
- Button disappears

**Scenario 3**: Temporary Hide
- User hides composite score during presentation
- After presentation, clicks "Show Hidden Sections"
- Score card returns immediately

### For Developers

**Scenario 1**: Make New Section Hideable
```html
<!-- Add three data attributes -->
<div class="new-section"
     data-hideable="true"
     data-section-id="new-feature"
     data-section-name="New Feature Section">
    <!-- Content -->
</div>

<!-- That's it! Hide button automatically added on page load -->
```

**Scenario 2**: Check Hidden Sections Programmatically
```javascript
// Check if a specific section is hidden
const isHidden = window.sectionVisibilityManager.hiddenSections.has('composite-score');
console.log('Composite score hidden:', isHidden);

// Get count of hidden sections
const count = window.sectionVisibilityManager.hiddenSections.size;
console.log('Total hidden:', count);
```

**Scenario 3**: Programmatically Hide Section
```javascript
// Hide a section via JavaScript
window.sectionVisibilityManager.hideSection('us-market-flow', true);

// Show a section via JavaScript
window.sectionVisibilityManager.showSection('us-market-flow', true);
```

---

## 📋 INTEGRATION CHECKLIST

### HTML Integration

- ✅ Added `data-hideable="true"` to composite score card
- ✅ Added `data-hideable="true"` to 6 metric cards
- ✅ Each section has unique `data-section-id`
- ✅ Each section has descriptive `data-section-name`
- ✅ Script loaded in HTML: `<script src="js/section_visibility_manager.js"></script>`

### JavaScript Integration

- ✅ `section_visibility_manager.js` created (350+ lines)
- ✅ Global instance: `window.sectionVisibilityManager`
- ✅ Auto-initialization on page load
- ✅ localStorage integration
- ✅ Debug helpers available

### CSS Positioning

- ✅ Sections set to `position: relative` for hide button positioning
- ✅ Hide button positioned absolutely (top-right)
- ✅ Z-index managed to keep hide button above content

---

## 🎨 VISUAL DESIGN

### Hide Button States

```
Normal State:
┌─────────────────────────────┐
│                          ✕ ←│ (70% opacity, crimson)
│   Section Content           │
│                             │
└─────────────────────────────┘

Hover State:
┌─────────────────────────────┐
│                          ✕ ←│ (100% opacity, bright red, scaled 1.1)
│   Section Content           │
│                             │
└─────────────────────────────┘
```

### Show Hidden Button

```
Bottom-Right Corner:
                        ┌─────────────────────────┐
                        │  👁️ 3 Hidden Sections  │
                        └─────────────────────────┘
                        (Spartan red gradient, floating shadow)

On Hover:
                        ┌─────────────────────────┐
                        │  👁️ 3 Hidden Sections  │ ↑ (lifts 2px)
                        └─────────────────────────┘
                        (Enhanced shadow)
```

---

## 🔄 FUTURE ENHANCEMENTS (Optional)

### Advanced Features

1. **Per-Tab Preferences**:
   - Different hidden sections for each tab
   - Tab-specific localStorage keys
   - Independent visibility settings

2. **Section Groups**:
   - Hide entire groups of sections
   - "Hide All Market Flows" button
   - "Hide All Regional Details" button

3. **Import/Export Preferences**:
   - Export hidden sections as JSON
   - Import preferences from file
   - Share preferences with other users

4. **Undo/Redo**:
   - Undo last hide action
   - Redo hide action
   - History stack of hide/show operations

5. **Keyboard Shortcuts**:
   - Press 'H' to hide focused section
   - Press 'Shift+H' to show all hidden
   - Accessibility improvements

---

## 📊 STATISTICS

### Code Metrics

```
js/section_visibility_manager.js:  350+ lines
global_capital_flow.html:          ~50 lines added (data attributes)

Total New Code:                    ~400 lines
```

### Feature Coverage

```
Hideable Sections:                 7 sections (Capital Flow tab)
localStorage Keys Used:            1 (spartan_hidden_sections)
Animation Duration:                300ms (hide/show)
Button Types:                      2 (hide button, show hidden button)
```

### Browser Compatibility

```
localStorage:                      Supported in all modern browsers
CSS Transitions:                   Supported in all modern browsers
HTML5 Data Attributes:             Supported in all modern browsers
ES6 Classes:                       Supported in all modern browsers
```

---

## 🧪 TESTING CHECKLIST

### Manual Testing

- ✅ Open global_capital_flow.html
- ✅ Navigate to Tab 1 (Capital Flow Dashboard)
- ✅ Verify ✕ buttons appear on all hideable sections
- ✅ Click ✕ on "US Market Flow" card
- ✅ Verify card fades out and disappears
- ✅ Verify "👁️ 1 Hidden Sections" button appears (bottom-right)
- ✅ Reload page
- ✅ Verify "US Market Flow" card still hidden
- ✅ Click "Show Hidden Sections" button
- ✅ Verify card fades back in
- ✅ Verify button disappears

### Developer Console Checks

```javascript
// Check manager loaded
console.log(window.sectionVisibilityManager);
// Should return: SectionVisibilityManager {storageKey: "spartan_hidden_sections", ...}

// Get hidden sections
const hidden = window.getHiddenSections();
console.log(hidden);
// Should return: Array of hidden section objects

// Test hide function
window.sectionVisibilityManager.hideSection('composite-score', true);
// Should hide composite score card

// Test show function
window.sectionVisibilityManager.showSection('composite-score', true);
// Should show composite score card

// Reset all
window.resetAllSections();
// Should show all sections and clear localStorage
```

### localStorage Checks

```javascript
// Check what's stored
const stored = localStorage.getItem('spartan_hidden_sections');
console.log('Stored:', stored);
// Should return: ["composite-score", "us-market-flow"] (if those are hidden)

// Clear localStorage
localStorage.removeItem('spartan_hidden_sections');
// Removes all hidden section preferences

// Reload page to see all sections again
location.reload();
```

---

## 🎉 SUMMARY

The Section Visibility Manager is **fully implemented** and **operational**:

### What Was Implemented

1. ✅ **Hide buttons** added to all hideable sections
2. ✅ **localStorage persistence** for hidden sections
3. ✅ **Auto-hide on page load** based on saved preferences
4. ✅ **"Show Hidden Sections" button** to restore visibility
5. ✅ **Smooth animations** for hide/show transitions
6. ✅ **7 hideable sections** on Capital Flow tab
7. ✅ **Debug helpers** for development and testing
8. ✅ **Production-ready** error handling
9. ✅ **Spartan theme styling** throughout
10. ✅ **User customization** - full control over dashboard layout

### Key Features

- **Fine-grained control** - Hide individual sections
- **Persistent preferences** - Survives page reloads
- **One-click restore** - Show all hidden sections easily
- **Smooth UX** - Fade animations for hide/show
- **Visual feedback** - Hide button hover effects, section counts
- **Developer-friendly** - Easy to add new hideable sections

### User Experience

Users can now:
- ✅ Hide sections they don't use (declutter dashboard)
- ✅ Preferences saved automatically (no manual save needed)
- ✅ Restore sections anytime (one-click show all)
- ✅ See how many sections are hidden (live count)
- ✅ Customize dashboard to their workflow

**This gives users complete control over their dashboard layout and viewing experience.**

---

**Last Updated**: 2025-11-16
**Implementation Status**: ✅ COMPLETE AND OPERATIONAL
**User Control**: ✅ FULL CUSTOMIZATION ENABLED
**Persistence**: ✅ LOCALSTORAGE INTEGRATION WORKING
