window.spartanDataFetcher = {
    fetchQuote: async (symbol) => {
        console.log(`Mock fetch for ${symbol}`);
        return { price: 100, change: 1, changePercent: 1, fiveDayChange: 2 };
    }
};
console.log('Spartan Preloader loaded');