# Scanner Implementation Template

## Standard Architecture for All Pattern Scanners

Every scanner tab MUST follow this architecture for consistent UX:

### 1. Progress Overlay (Shared Across All Scanners)

**Already implemented globally** - No changes needed per scanner.

```css
.progress-overlay {
    position: fixed;
    top: 0;
    background: rgba(10, 22, 40, 0.70);  /* Semi-transparent */
    backdrop-filter: blur(2px);
    align-items: flex-start;  /* Top positioning */
    padding-top: 80px;
}
```

**Behavior**:
- Shows at top of page
- Semi-transparent so users see results populating below
- Updates in real-time with batch progress
- Shows running count of patterns found

### 2. Real-Time Results Streaming (Per Scanner)

Each scanner MUST render results immediately when found:

```javascript
async function scanBatch(batch) {
    const promises = batch.map(ticker => scanSymbol(ticker));
    const results = await Promise.all(promises);

    // CRITICAL: Render immediately when pattern found
    results.forEach(result => {
        if (result && result.pattern) {
            allResults.push(result);

            // Real-time updates (REQUIRED)
            filterAndRenderResults();
            updateStats();
        }
    });
}
```

### 3. Results Table Structure (Per Scanner)

Each scanner tab should have:

```html
<!-- Statistics Section -->
<div class="stats">
    <div class="stat-card">
        <div class="stat-label">Total Patterns</div>
        <div class="stat-value" id="totalPatterns">0</div>
    </div>
    <!-- Add more stat cards as needed -->
</div>

<!-- Results Table -->
<div class="results-section">
    <table class="results-table">
        <thead>
            <tr>
                <th data-sort="symbol">Symbol</th>
                <th data-sort="name">Name</th>
                <th data-sort="pattern">Pattern</th>
                <th data-sort="signal">Signal</th>
                <!-- Add columns specific to scanner type -->
            </tr>
        </thead>
        <tbody id="resultsBody">
            <tr>
                <td colspan="10" class="no-results">
                    Click "Scan All Markets" to start detecting patterns
                </td>
            </tr>
        </tbody>
    </table>
</div>
```

### 4. Scan Button Pattern

```html
<button class="scan-btn" id="scanBtn">
    🔍 Scan All Markets
</button>
```

### 5. Progress Updates Pattern

```javascript
function startScan() {
    // Show overlay
    document.getElementById('progressOverlay').classList.add('active');

    // Update progress as scanning
    updateProgress(
        progress,
        `Scanning batch ${i + 1} of ${totalBatches}`,
        `Processed ${end} / ${tickers.length} symbols | Found ${allResults.length} patterns`
    );

    // Hide overlay when complete
    document.getElementById('progressOverlay').classList.remove('active');
}
```

## Example: Adding a Momentum Scanner

### Step 1: Add Tab Button

```html
<button class="tab-button" data-tab="momentum-scanner">Momentum Scanner</button>
```

### Step 2: Add Tab Content

```html
<div id="momentum-scanner" class="tab-content">
    <div class="controls">
        <!-- Filters specific to momentum -->
        <button class="scan-btn" id="momentumScanBtn">🔍 Scan For Momentum</button>
    </div>

    <div class="stats">
        <div class="stat-card">
            <div class="stat-label">High Momentum</div>
            <div class="stat-value" id="momentumTotal">0</div>
        </div>
    </div>

    <div class="results-section">
        <table class="results-table">
            <thead>
                <tr>
                    <th>Symbol</th>
                    <th>Momentum Score</th>
                    <th>Volume Surge</th>
                    <!-- Momentum-specific columns -->
                </tr>
            </thead>
            <tbody id="momentumResultsBody">
                <tr>
                    <td colspan="5" class="no-results">
                        Click "Scan For Momentum" to start
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</div>
```

### Step 3: Implement Scanning Logic

```javascript
async function startMomentumScan() {
    if (isMomentumScanning) return;
    isMomentumScanning = true;

    document.getElementById('momentumScanBtn').disabled = true;
    document.getElementById('progressOverlay').classList.add('active');
    momentumResults = [];

    const tickers = await fetchAllTickers();
    const batchSize = 50;
    const totalBatches = Math.ceil(tickers.length / batchSize);

    for (let i = 0; i < totalBatches; i++) {
        const batch = tickers.slice(i * batchSize, (i + 1) * batchSize);

        updateProgress(
            10 + ((i + 1) / totalBatches) * 85,
            `Scanning batch ${i + 1} of ${totalBatches}`,
            `Found ${momentumResults.length} high momentum stocks`
        );

        await scanMomentumBatch(batch);
        await sleep(1000); // Rate limiting
    }

    document.getElementById('progressOverlay').classList.remove('active');
    document.getElementById('momentumScanBtn').disabled = false;
    isMomentumScanning = false;
}

async function scanMomentumBatch(batch) {
    const results = await Promise.all(batch.map(ticker => analyzeMomentum(ticker)));

    // REAL-TIME STREAMING: Render immediately
    results.forEach(result => {
        if (result && result.momentumScore > 70) {
            momentumResults.push(result);
            renderMomentumResults();  // Update table immediately
            updateMomentumStats();     // Update stats immediately
        }
    });
}

async function analyzeMomentum(ticker) {
    // Implement momentum calculation logic
    const data = await fetchHistoricalData(ticker.ticker);

    // Calculate momentum score (0-100)
    const momentumScore = calculateMomentumScore(data);

    if (momentumScore > 70) {
        return {
            symbol: ticker.ticker,
            name: ticker.name,
            momentumScore: momentumScore,
            volumeSurge: calculateVolumeSurge(data),
            // Other momentum-specific metrics
        };
    }

    return null;
}
```

## Scanner Types to Implement

1. **W/M Pattern Scanner** ✅ COMPLETE
   - Double bottom (W) and double top (M) detection
   - Real-time streaming implemented
   - 44,000+ symbols supported

2. **Momentum Scanner** (Template above)
   - RSI, MACD, momentum indicators
   - High volume surges
   - Price acceleration

3. **Breakout Scanner**
   - 52-week highs/lows
   - Support/resistance breaks
   - Volume confirmation

4. **Volume Scanner**
   - Unusual volume spikes
   - Volume price correlation
   - Accumulation/distribution

5. **RSI Scanner**
   - Overbought (>70)
   - Oversold (<30)
   - Divergence detection

6. **MACD Scanner**
   - Bullish/bearish crossovers
   - Histogram analysis
   - Signal line crosses

7. **Bollinger Bands Scanner**
   - Band squeezes
   - Price outside bands
   - Band walk patterns

8. **Moving Average Scanner**
   - Golden/death crosses
   - 50/200 day crossovers
   - Price above/below MA

## Critical Rules for ALL Scanners

1. ✅ **Real-time streaming** - Results appear immediately
2. ✅ **Semi-transparent overlay** - Users see results populating
3. ✅ **Progress at top** - Not centered, at top of page
4. ✅ **Batch processing** - 50 symbols per batch with rate limiting
5. ✅ **PostgreSQL symbols** - Use `/api/db/polygon-symbols` endpoint
6. ✅ **OTC exclusion** - Filter `WHERE type != 'OS'`
7. ✅ **Error handling** - Silent failures for individual symbols
8. ✅ **Stats updates** - Real-time counter updates
9. ✅ **Sortable tables** - Click headers to sort
10. ✅ **Filter buttons** - Asset type filters (stocks, ETFs, etc.)

## Files to Modify

When adding a new scanner:

1. **nano_banana_scanner.html**
   - Add tab button in `.tab-nav`
   - Add tab content in `<div id="new-scanner" class="tab-content">`
   - Add scanning logic in `<script>` section

2. **No new files needed** - All scanners in one file

## Performance Considerations

- Batch size: 50 symbols
- Rate limit: 1 second between batches
- Total scan time: ~15 minutes for 21,000 symbols
- Real-time updates: Every 50 symbols (~1 second intervals)

## User Experience

**Before scan**: Empty table with "Click to scan" message
**During scan**:
- Progress overlay at top shows batch X of Y
- Results table populates in real-time below
- Stats counters update with each batch
**After scan**:
- Full results table
- Progress overlay disappears
- Scan button re-enabled

---

**Last Updated**: December 30, 2025
**Standard**: All scanners MUST follow this pattern
**Status**: Template ready for implementation
