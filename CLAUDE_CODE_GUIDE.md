# Transition Guide: Moving to Claude Code

## What's Included

This project package contains everything you need to continue development in Claude Code:

```
project/
├── pca_richness_analysis.py    # Main analysis class
├── examples.py                  # Example usage scripts
├── README.md                    # Full documentation
├── requirements.txt             # Python dependencies
├── PCA_Cohort_Candidates.xlsx  # Historical data (2016-2026)
└── CLAUDE_CODE_GUIDE.md        # This file
```

## Quick Start in Claude Code

1. **Upload all files to Claude Code**
   - The entire project is self-contained
   - All dependencies listed in requirements.txt

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the analysis**
   ```bash
   python pca_richness_analysis.py
   ```

4. **Or explore examples**
   ```bash
   python examples.py
   ```

## What We Built

### Core Functionality
- **PCARichnessAnalyzer class**: Main analysis engine
  - `load_data()`: Load Excel data
  - `run_pca()`: Run PCA and extract PC1 factor
  - `calculate_residuals()`: Calculate z-scores
  - `get_current_ranking()`: Get rich/cheap ranking
  - `get_rv_opportunities()`: Identify RV trades
  - `plot_time_series()`: Visualize historical z-scores
  - `plot_current_ranking()`: Current positioning chart

### Key Design Decisions

1. **Normalized Z-Scores**: 
   - Credit z-scores flipped so positive = rich for ALL assets
   - Makes interpretation consistent across credit and equity

2. **Volatility Normalization**:
   - All returns standardized (mean=0, std=1) before PCA
   - Ensures high-vol assets (NDX) don't dominate low-vol assets (CDX)

3. **PC1 = Risk-Off Factor**:
   - Explains 76% of variance
   - Credit loads positive, equity loads negative
   - Perfect for credit-equity basis trading

## Common Extensions for Claude Code

### 1. Rolling Window PCA
Currently using static PCA. To adapt to regime changes:

```python
def rolling_pca(self, window=60):
    """Run PCA on rolling window"""
    # Implementation needed
    pass
```

### 2. Backtesting Framework
Test historical performance of z-score signals:

```python
def backtest_strategy(self, entry_z=2, exit_z=0):
    """Backtest mean-reversion strategy"""
    # Implementation needed
    pass
```

### 3. Add More Assets
Currently: CDX IG, CDX HY, ITRX MAIN, ITRX XOVER, SPX, NDX

Consider adding:
- RTY Index (small caps)
- SX5E Index (Europe)
- More credit indices
- CDX HY sub-indices

To add assets, just include them in the Excel file.

### 4. Intraday Analysis
Current analysis uses daily data. For 2-3 week trades, consider:

```python
def load_intraday_data(self, frequency='1H'):
    """Load hourly/minute data for intraday signals"""
    # Implementation needed
    pass
```

### 5. Alert System
Build automated monitoring:

```python
def check_alerts(self, threshold=2):
    """Check for extreme z-scores and send alerts"""
    extremes = []
    for asset in self.normalized_z_scores.columns:
        z = self.normalized_z_scores[asset].iloc[-1]
        if abs(z) > threshold:
            extremes.append((asset, z))
    return extremes
```

### 6. Multi-Factor Model
Currently only using PC1. To use PC2, PC3:

```python
def multi_factor_residuals(self, n_components=3):
    """Calculate residuals using multiple PCs"""
    # Implementation needed
    pass
```

## Data Updates

To update with new data:

1. **Option A: Add to existing Excel file**
   - Append new rows to PCA_Cohort_Candidates.xlsx
   - Re-run analysis

2. **Option B: Load from Bloomberg/API**
   ```python
   def load_from_bloomberg(self, tickers, start_date, end_date):
       """Load data directly from Bloomberg API"""
       # Implementation needed
       pass
   ```

## Key Formulas Reference

**Z-Score Calculation:**
```
1. Standardize returns: (return - mean) / std_dev
2. Run PCA → get PC1 scores and betas
3. Expected = beta × PC1_score
4. Residual = Actual - Expected
5. Z-score = (Residual - mean) / std_dev
6. Normalize: flip credit z-scores (×-1)
```

**Trading Signals:**
```
|Z| > 2  → Strong mean-reversion signal
|Z| > 1  → Moderate signal
|Z| < 1  → Fair value
```

## Testing in Claude Code

After uploading, verify everything works:

```bash
# Test 1: Basic analysis
python -c "from pca_richness_analysis import PCARichnessAnalyzer; \
           a = PCARichnessAnalyzer('PCA_Cohort_Candidates.xlsx'); \
           a.run_full_analysis()"

# Test 2: Get current ranking
python -c "from pca_richness_analysis import PCARichnessAnalyzer; \
           a = PCARichnessAnalyzer('PCA_Cohort_Candidates.xlsx'); \
           a.load_data(); a.run_pca(); a.calculate_residuals(); \
           print(a.get_current_ranking())"

# Test 3: Run all examples
python examples.py
```

## Questions to Explore in Claude Code

1. **Optimal window length for rolling PCA?**
   - Test 30, 60, 90, 120 day windows
   - Measure Sharpe ratio of signals

2. **Which PC1 beta is most stable?**
   - Plot betas over time
   - Identify assets with regime-dependent loadings

3. **Correlation between z-scores and forward returns?**
   - Does high z-score predict mean-reversion?
   - What's the decay pattern?

4. **Best asset pairs for RV?**
   - CDX IG vs HY?
   - SPX vs NDX?
   - Cross-asset (CDX vs SPX)?

5. **Intraday vs daily signals?**
   - Do signals persist intraday?
   - Better Sharpe with intraday execution?

## Claude Code Advantages

Use Claude Code to:
- Rapidly iterate on backtests
- Test multiple parameter combinations
- Build automated monitoring scripts
- Create interactive dashboards
- Integrate with live data feeds
- Deploy production trading signals

## Next Development Priorities

Recommended order:

1. ✓ **Done**: Static PCA framework
2. **Next**: Rolling window PCA (60-day)
3. **Then**: Simple backtest (enter at |Z|>2, exit at 0)
4. **Then**: Optimize entry/exit thresholds
5. **Then**: Add intraday data
6. **Finally**: Live monitoring system

## Contact Info

Created by: Andrew (Hedge Fund PM)
Date: January 2026
Project: Credit-Equity PCA Rich/Cheap Analysis

Ready to continue development in Claude Code!
