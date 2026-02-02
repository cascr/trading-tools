# PCA-Based Rich/Cheap Analysis for Credit-Equity Indices

## Overview
This project uses Principal Component Analysis (PCA) to identify rich/cheap opportunities across credit and equity indices for mean-reversion trading.

## What It Does

1. **Runs PCA** on combined credit-equity cohort to extract common risk factor (PC1)
2. **Calculates residuals** - deviations of each asset from its expected relationship to PC1
3. **Generates normalized z-scores** where:
   - **Positive = RICH** (asset trading richer than PC1 relationship suggests)
   - **Negative = CHEAP** (asset trading cheaper than PC1 relationship suggests)
4. **Creates rankings** for relative value trading opportunities

## Assets Included

**Credit Indices:**
- CDX IG
- CDX HY
- ITRX MAIN
- ITRX XOVER

**Equity Indices:**
- SPX Index
- NDX Index

## Key Concept

**PC1 = Risk-Off Factor (explains 76% of variance)**
- Credit indices load +0.38 to +0.43 (spreads widen in risk-off)
- Equity indices load -0.40 to -0.42 (prices fall in risk-off)

When an asset deviates from this relationship, it creates a mean-reversion opportunity.

## Installation

```bash
pip install pandas numpy scikit-learn matplotlib seaborn openpyxl
```

## Usage

### Quick Start
```python
from pca_richness_analysis import PCARichnessAnalyzer

# Initialize and run
analyzer = PCARichnessAnalyzer('PCA_Cohort_Candidates.xlsx')
analyzer.run_full_analysis()

# Create charts
analyzer.plot_time_series('richness_timeseries.png')
analyzer.plot_current_ranking('current_ranking.png')

# Save results
analyzer.save_results('normalized_z_scores.csv')
```

### Get Current Ranking
```python
ranking = analyzer.get_current_ranking()
print(ranking)
```

### Get RV Opportunities
```python
rv_opps = analyzer.get_rv_opportunities()
for trade_type, details in rv_opps.items():
    print(f"{trade_type}: Short {details['Short']}, Long {details['Long']}")
```

### Update with New Data
```python
# Load new data
analyzer.load_data()

# Re-run analysis
analyzer.run_pca()
analyzer.calculate_residuals()

# Get latest ranking
current = analyzer.get_current_ranking()
```

## Trading Framework

**Entry Signals:**
- |Z-score| > 2: Strong mean-reversion signal
- |Z-score| > 1: Moderate signal

**Exit:**
- Z-score returns to 0 (fair value)
- Opposite extreme signal

**Position Sizing:**
- Scale position size with z-score magnitude
- Larger positions at |Z| > 2.5

**Relative Value Trades:**
1. **Within asset class**: Short richest, Long cheapest in same type (credit or equity)
2. **Pairs trading**: Trade specific pairs showing large z-score divergence

## Files

- `pca_richness_analysis.py` - Main analysis class
- `PCA_Cohort_Candidates.xlsx` - Historical price/spread data (2016-2026)
- `normalized_z_scores.csv` - Output: daily z-scores for all assets
- `richness_timeseries.png` - Output: time series visualization
- `current_ranking.png` - Output: current rich/cheap ranking

## Methodology

### 1. Cohort Validation (Pre-PCA)
Ran 5 tests to validate asset selection:
- Pairwise correlations
- Rolling correlation stability
- Granger causality (lead-lag relationships)
- Hierarchical clustering
- KMO test (PCA suitability)

Result: Combined credit-equity cohort validated with KMO = 0.845 (Meritorious)

### 2. PCA Process
1. **Standardize returns** - normalize volatility across all assets (mean=0, std=1)
2. **Run PCA** - extract principal components
3. **Calculate expected values** - Expected = Beta_to_PC1 × PC1_score
4. **Calculate residuals** - Actual - Expected
5. **Normalize residuals** - flip credit z-scores so positive = rich for all assets

### 3. Z-Score Interpretation
- **Credit**: Negative raw residual = tighter spreads = RICH → flip to positive
- **Equity**: Positive raw residual = higher prices = RICH → keep as is
- **Result**: Positive z-score = RICH for both asset classes

## Historical Performance

From 2016-2026:
- Mean-reversion signals (|Z| > 2) occur 2-4% of time per asset
- NDX shows most extreme cheap signals (2.8% of time)
- ITRX XOVER shows most rich signals (2.6% of time)

## Next Steps / Extensions

1. **Rolling window PCA** - use 60-90 day rolling window instead of static
2. **Backtest** - measure historical Sharpe of mean-reversion trades
3. **Multi-factor model** - incorporate PC2, PC3 for residual analysis
4. **Intraday analysis** - apply same framework to intraday data
5. **Alert system** - automated alerts when |Z| > 2
6. **Add more assets** - include RTY, SX5E, more credit indices

## Contact

Created by Andrew - Hedge Fund PM
Date: January 2026
