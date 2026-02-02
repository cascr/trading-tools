"""
Example Usage: PCA Rich/Cheap Analysis

Common use cases and workflows
"""

from pca_richness_analysis import PCARichnessAnalyzer
import pandas as pd

# ============================================================================
# EXAMPLE 1: Quick Analysis
# ============================================================================
print("="*70)
print("EXAMPLE 1: QUICK FULL ANALYSIS")
print("="*70)

analyzer = PCARichnessAnalyzer('PCA_Cohort_Candidates.xlsx')
analyzer.run_full_analysis()
analyzer.plot_time_series('richness_timeseries.png')
analyzer.plot_current_ranking('current_ranking.png')
analyzer.save_results('normalized_z_scores.csv')

# ============================================================================
# EXAMPLE 2: Get Specific Date Ranking
# ============================================================================
print("\n" + "="*70)
print("EXAMPLE 2: HISTORICAL RANKING (2020-03-20 - COVID crash)")
print("="*70)

analyzer = PCARichnessAnalyzer('PCA_Cohort_Candidates.xlsx')
analyzer.load_data()
analyzer.run_pca()
analyzer.calculate_residuals()

# Get ranking for specific date
covid_ranking = analyzer.get_current_ranking(as_of_date='2020-03-20')
print(covid_ranking)

# ============================================================================
# EXAMPLE 3: Monitor Specific Asset
# ============================================================================
print("\n" + "="*70)
print("EXAMPLE 3: TRACK NDX RICHNESS OVER TIME")
print("="*70)

analyzer = PCARichnessAnalyzer('PCA_Cohort_Candidates.xlsx')
analyzer.load_data()
analyzer.run_pca()
analyzer.calculate_residuals()

# Get NDX z-scores over time
ndx_richness = analyzer.normalized_z_scores['NDX Index']

print(f"Current NDX Z-Score: {ndx_richness.iloc[-1]:.2f}")
print(f"Max rich (last 2 years): {ndx_richness[-504:].max():.2f}")
print(f"Max cheap (last 2 years): {ndx_richness[-504:].min():.2f}")
print(f"Times |Z| > 2 (last year): {(abs(ndx_richness[-252:]) > 2).sum()} days")

# ============================================================================
# EXAMPLE 4: Find Best RV Opportunities Historically
# ============================================================================
print("\n" + "="*70)
print("EXAMPLE 4: LARGEST RV SPREADS (Last 2 Years)")
print("="*70)

analyzer = PCARichnessAnalyzer('PCA_Cohort_Candidates.xlsx')
analyzer.load_data()
analyzer.run_pca()
analyzer.calculate_residuals()

# Calculate credit spreads over time
credit_assets = analyzer.credit_assets
z_scores = analyzer.normalized_z_scores[credit_assets]

# Find max spread between any two credit indices each day
spreads = []
for date in z_scores[-504:].index:  # Last 2 years
    day_z = z_scores.loc[date]
    max_spread = day_z.max() - day_z.min()
    spreads.append({
        'Date': date,
        'Max Spread': max_spread,
        'Rich Asset': day_z.idxmax(),
        'Cheap Asset': day_z.idxmin()
    })

spreads_df = pd.DataFrame(spreads).sort_values('Max Spread', ascending=False)
print("\nTop 5 widest credit RV opportunities:")
print(spreads_df.head().to_string(index=False))

# ============================================================================
# EXAMPLE 5: Real-time Monitoring Setup
# ============================================================================
print("\n" + "="*70)
print("EXAMPLE 5: REAL-TIME ALERT SYSTEM")
print("="*70)

analyzer = PCARichnessAnalyzer('PCA_Cohort_Candidates.xlsx')
analyzer.load_data()
analyzer.run_pca()
analyzer.calculate_residuals()

# Check for extreme signals
current_ranking = analyzer.get_current_ranking()

print("Current Extreme Signals (|Z| > 2):")
extremes = current_ranking[abs(current_ranking['Z-Score']) > 2]
if len(extremes) > 0:
    print(extremes.to_string(index=False))
else:
    print("No extreme signals currently")

print("\nCurrent RV Opportunities (spread > 1σ):")
rv_opps = analyzer.get_rv_opportunities()
for trade_type, details in rv_opps.items():
    if details['Spread'] > 1.0:
        print(f"\n{trade_type}:")
        print(f"  SHORT {details['Short']} (Z={details['Short Z']:+.2f})")
        print(f"  LONG  {details['Long']} (Z={details['Long Z']:+.2f})")
        print(f"  Spread: {details['Spread']:.2f}σ")

# ============================================================================
# EXAMPLE 6: Export Time Series for Further Analysis
# ============================================================================
print("\n" + "="*70)
print("EXAMPLE 6: EXPORT FOR EXTERNAL ANALYSIS")
print("="*70)

analyzer = PCARichnessAnalyzer('PCA_Cohort_Candidates.xlsx')
analyzer.load_data()
analyzer.run_pca()
analyzer.calculate_residuals()

# Export last 1 year of data
recent_data = analyzer.normalized_z_scores[-252:].copy()
recent_data.to_csv('richness_last_year.csv')
print("✓ Exported last year of z-scores to richness_last_year.csv")

# Export summary statistics
summary = []
for asset in analyzer.returns.columns:
    z = analyzer.normalized_z_scores[asset]
    summary.append({
        'Asset': asset,
        'Current Z': z.iloc[-1],
        'Mean Z': z.mean(),
        'Std Z': z.std(),
        '% Time Rich (>1)': (z > 1).sum() / len(z) * 100,
        '% Time Cheap (<-1)': (z < -1).sum() / len(z) * 100,
        'Max Z': z.max(),
        'Min Z': z.min()
    })

summary_df = pd.DataFrame(summary)
summary_df.to_csv('richness_summary_stats.csv', index=False)
print("✓ Exported summary statistics to richness_summary_stats.csv")

print("\n" + "="*70)
print("ALL EXAMPLES COMPLETE")
print("="*70)
