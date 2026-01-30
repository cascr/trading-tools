# CLAUDE.md - Project Context for AI Assistance

## Project Overview

**Project:** Credit-Equity Relative Value Trading Tool
**Purpose:** Analyze relationships between CDX (credit default swap indices) and Equity Indices (SPX, etc.) for macro credit trading decisions
**Target Platform:** Bloomberg BQNT (Bloomberg Quant environment)

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

## Core Analysis Focus Areas

### 1. Spread Beta
- Relationship between credit spread changes and equity index moves
- How much does CDX move for a 1% move in SPX?

### 2. Duration Neutrality
- Adjusting for interest rate sensitivity
- Isolating pure credit risk from rates risk

### 3. Regression Residuals
- What's the "fair value" of credit given equity levels?
- Identify when credit is rich/cheap vs equity

### 4. Volatility-Adjusted Signals
- Normalize signals by recent volatility (e.g., z-scores)
- Avoid false signals in high-vol environments

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
| Spread | Credit spread in basis points (bps); 100 bps = 1% |
| SPX | S&P 500 Index |
| Beta | Sensitivity/relationship coefficient |
| DV01 | Dollar value of 1 basis point move |
| Rich/Cheap | Expensive/Inexpensive relative to model fair value |

## File Organization (Planned)

```
trading-tools/
├── CLAUDE.md           # This file - project context
├── data_fetchers/      # Bloomberg data retrieval
├── analytics/          # Core calculations (beta, regression, etc.)
├── signals/            # Trading signal generation
├── visualization/      # Charts and dashboards
└── notebooks/          # BQNT analysis notebooks
```

## Typical Workflow

1. **Fetch Data** - Pull CDX spreads and equity index levels from Bloomberg
2. **Clean & Align** - Match timestamps, handle holidays, fill gaps
3. **Calculate Metrics** - Beta, regression residuals, z-scores
4. **Generate Signals** - Identify rich/cheap opportunities
5. **Visualize** - Charts showing relationships and current positioning

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
