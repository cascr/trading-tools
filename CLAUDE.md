# CLAUDE.md - Project Context for AI Assistance

## Project Overview

**Project:** PCA Rich/Cheap Analysis for Credit-Equity Indices
**Purpose:** Identify rich/cheap opportunities across credit and equity indices for mean-reversion trading
**Target Platform:** Bloomberg BQNT (Bloomberg Quant environment)

### Current Implementation
- **PCARichnessAnalyzer class** in `pca_richness_analysis.py`
- PCA extracts PC1 (risk-off factor, ~73% variance explained)
- Z-scores normalized: positive = RICH, negative = CHEAP for all assets
- Generates rankings and RV trade opportunities

### Assets (8 total)
**Credit:** CDX IG, CDX HY, ITRX MAIN, ITRX XOVER
**Equity:** SPX Index, NDX Index, RTY Index, SX5E Index

### Development Priorities
1. Rolling window PCA (replace static PCA)
2. Backtest framework (measure historical Sharpe)
3. Alert system (|Z| > 2 triggers)

## User Context

- **Role:** Portfolio Manager
- **Coding Experience:** None - explain all code decisions in plain English
- **Goal:** Understand both the code AND the financial concepts as we build

When writing code or explanations:
- Assume no prior programming knowledge
- Explain WHY we make each decision, not just WHAT we're doing
- Connect code concepts to trading/finance analogies when helpful

## Platform Constraints (Bloomberg BQNT)

- **Language:** Python only
- **Environment:** Sandboxed - limited external packages
- **Available:** pandas, numpy, scipy, matplotlib (standard BQNT stack)
- **Data Access:** Bloomberg API via `bql` and `bqplot`
- **No:** pip install, internet access, file system writes outside workspace

## Core Analysis Concepts

### 1. PCA (Principal Component Analysis)
- Extracts common factors driving all assets together
- PC1 = "risk-off factor" (~73% of variance)
- Credit loads positive (spreads widen in risk-off)
- Equity loads negative (prices fall in risk-off)

### 2. Residuals & Z-Scores
- Residual = how much asset deviated from PC1 expectation
- Z-score = residual in standard deviation units
- |Z| > 2 = statistically unusual (strong signal)

### 3. Normalized Z-Score Convention
- **Positive = RICH** (asset expensive vs peers)
- **Negative = CHEAP** (asset cheap vs peers)
- Credit z-scores flipped so convention is consistent

### 4. Relative Value (RV) Trades
- Long the cheapest, short the richest
- Can be within asset class (credit vs credit) or cross-asset
- Mean-reversion expectation: z-scores converge to zero

## Coding Standards

### Readability First
```python
# GOOD: Clear and explicit
credit_spread_change = today_spread - yesterday_spread

# AVOID: Cryptic abbreviations
cs_chg = t_spd - y_spd
```

### Heavy Commenting
```python
# Calculate the rolling beta between CDX and SPX
# Beta tells us: "For every 1% SPX moves, CDX moves by X basis points"
# We use 60 trading days (~3 months) as our lookback window
rolling_beta = calculate_rolling_beta(cdx_changes, spx_returns, window=60)
```

### Explain Financial Concepts in Code
```python
# Z-score: How many standard deviations from the mean?
# Example: z-score of +2 means the signal is 2 std devs above average
#          This is statistically unusual (happens ~2.5% of the time)
z_score = (current_value - mean) / standard_deviation
```

### Function Documentation
Every function should have:
1. One-line description of what it does
2. Explanation of each parameter
3. What it returns and how to interpret it
4. Example usage when helpful

## Key Financial Terms Reference

| Term | Meaning |
|------|---------|
| CDX | Credit Default Swap Index (basket of corporate credit risk) |
| CDX IG | Investment Grade CDX (higher quality companies) |
| CDX HY | High Yield CDX (lower quality, higher spread) |
| ITRX | iTraxx - European credit indices |
| Spread | Credit spread in basis points (bps); 100 bps = 1% |
| SPX | S&P 500 Index |
| NDX | Nasdaq 100 Index |
| RTY | Russell 2000 Index (small caps) |
| SX5E | Euro Stoxx 50 Index |
| PCA | Principal Component Analysis - extracts common factors |
| PC1 | First principal component (explains most variance) |
| Loading | How much an asset moves with a PC (like beta) |
| Residual | Actual minus expected (deviation from PC1 relationship) |
| Z-Score | Standard deviations from mean; ±2 = strong signal |
| Rich/Cheap | Expensive/Inexpensive relative to model fair value |
| RV Trade | Relative Value - long cheap, short rich |

## File Organization

```
trading-tools/
├── CLAUDE.md                    # Project context for AI assistance
├── pca_richness_analysis.py     # Main analysis class
├── examples.py                  # 6 example use cases
├── PCA_Cohort_Candidates.xlsx   # Historical data (2016-2026)
├── requirements.txt             # Python dependencies
├── README.md                    # Project documentation
├── CLAUDE_CODE_GUIDE.md         # Development transition guide
└── READY_FOR_CLAUDE_CODE.md     # Project summary
```

## Typical Workflow

1. **Load Data** - Read prices/spreads from Excel (or Bloomberg API)
2. **Calculate Returns** - Daily percentage changes for all assets
3. **Run PCA** - Standardize returns, extract PC1, get loadings
4. **Calculate Residuals** - Actual vs expected (based on PC1)
5. **Generate Z-Scores** - Normalize residuals, flip credit signs
6. **Rank Assets** - Sort by z-score (most negative = cheapest)
7. **Identify RV Trades** - Pair richest with cheapest

## Workflow Instructions

### Before Leaving Your Computer
Save and push all changes to GitHub:
```bash
git add .
git commit -m "Describe what you changed"
git push
```

### When Switching Locations
Pull latest changes from GitHub:
```bash
git pull
```

### Office Setup (First Time)
Clone the repository to get started:
```bash
git clone https://github.com/cascr/trading-tools.git
```

## Notes for Claude

- Always test code mentally for BQNT compatibility before suggesting
- Prefer explicit over clever - PM needs to understand and modify later
- When uncertain about BQNT capabilities, note it and offer alternatives
- Break complex operations into small, named steps
- Include print statements for debugging during development
