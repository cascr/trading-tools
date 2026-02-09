"""
PCA-Based Rich/Cheap Analysis for Credit and Equity Indices

This script runs PCA on a combined cohort of credit and equity indices to:
1. Identify the common risk factor (PC1)
2. Calculate residuals (actual vs expected based on PC1)
3. Generate normalized z-scores where positive = rich, negative = cheap
4. Create rich/cheap rankings for mean-reversion trading

Author: Andrew
Date: 2026-01-30
"""

import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime


class PCARichnessAnalyzer:
    """PCA-based rich/cheap analysis for credit-equity indices"""
    
    def __init__(self, data_path):
        """
        Initialize analyzer with data file
        
        Parameters:
        -----------
        data_path : str
            Path to Excel file with price/spread data
        """
        self.data_path = data_path
        self.df = None
        self.returns = None
        self.pca_model = None
        self.scaler = None
        self.loadings = None
        self.pca_scores = None
        self.normalized_z_scores = None
        
        # Asset classifications
        self.credit_assets = ['CDX IG', 'CDX HY', 'ITRX MAIN', 'ITRX XOVER']
        self.equity_assets = ['SPX Index', 'NDX Index']
        
    def load_data(self):
        """Load and prepare data"""
        print("Loading data...")
        self.df = pd.read_excel(self.data_path)
        self.df.rename(columns={'Unnamed: 0': 'Date'}, inplace=True)
        self.df.set_index('Date', inplace=True)
        
        # Calculate returns
        self.returns = self.df.pct_change().dropna()

        # Clean data: replace infinity with NaN, then drop rows with NaN
        # This handles division-by-zero cases (e.g., price went to/from 0)
        self.returns = self.returns.replace([np.inf, -np.inf], np.nan).dropna()

        print(f"[OK] Loaded {len(self.returns)} days from {self.returns.index[0].date()} to {self.returns.index[-1].date()}")
        
    def run_pca(self):
        """Run PCA on the data"""
        print("\nRunning PCA...")
        
        # Standardize data (normalize volatility across assets)
        self.scaler = StandardScaler()
        data_scaled = self.scaler.fit_transform(self.returns)
        
        # Fit PCA
        self.pca_model = PCA()
        self.pca_scores = self.pca_model.fit_transform(data_scaled)
        
        # Get loadings (betas to each PC)
        self.loadings = pd.DataFrame(
            self.pca_model.components_.T,
            columns=[f'PC{i+1}' for i in range(len(self.returns.columns))],
            index=self.returns.columns
        )
        
        # Print variance explained
        print(f"[OK] PC1 explains {self.pca_model.explained_variance_ratio_[0]:.1%} of variance")
        
        # Interpret PC1
        credit_loading = self.loadings.loc[self.credit_assets, 'PC1'].mean()
        equity_loading = self.loadings.loc[self.equity_assets, 'PC1'].mean()
        
        if credit_loading > 0 and equity_loading < 0:
            print(f"[OK] PC1 = RISK-OFF FACTOR (credit widens when equity falls)")
        else:
            print(f"[OK] PC1 interpretation: Credit avg={credit_loading:+.3f}, Equity avg={equity_loading:+.3f}")
            
    def calculate_residuals(self):
        """Calculate expected values and residuals from PC1"""
        print("\nCalculating residuals...")
        
        # Standardize returns
        data_scaled = self.scaler.transform(self.returns)
        
        # Calculate expected and residual for each asset
        results = pd.DataFrame(index=self.returns.index)
        
        for asset in self.returns.columns:
            beta = self.loadings.loc[asset, 'PC1']
            pc1 = self.pca_scores[:, 0]
            
            # Expected = beta * PC1
            expected = beta * pc1
            
            # Actual (standardized)
            actual = data_scaled[:, self.returns.columns.get_loc(asset)]
            
            # Residual
            residual = actual - expected
            
            # Z-score of residual
            z_score = (residual - np.mean(residual)) / np.std(residual)
            
            results[f'{asset}_zscore'] = z_score
            
        # Normalize z-scores: flip credit so positive = rich for all
        self.normalized_z_scores = pd.DataFrame(index=results.index)
        
        for asset in self.returns.columns:
            if asset in self.credit_assets:
                # Credit: flip sign (tighter spreads = negative residual → flip to positive)
                self.normalized_z_scores[asset] = -results[f'{asset}_zscore']
            else:
                # Equity: keep as is (higher prices = positive residual = positive z)
                self.normalized_z_scores[asset] = results[f'{asset}_zscore']
                
        print(f"[OK] Residuals calculated and normalized")
        
    def get_current_ranking(self, as_of_date=None):
        """
        Get current rich/cheap ranking
        
        Parameters:
        -----------
        as_of_date : str or datetime, optional
            Date to get ranking for. If None, uses most recent date.
            
        Returns:
        --------
        DataFrame with ranking
        """
        if as_of_date is None:
            as_of_date = self.normalized_z_scores.index[-1]
        
        ranking = []
        for asset in self.returns.columns:
            z = self.normalized_z_scores.loc[as_of_date, asset]
            
            if abs(z) > 2:
                signal = "VERY RICH" if z > 2 else "VERY CHEAP"
            elif abs(z) > 1:
                signal = "Rich" if z > 1 else "Cheap"
            else:
                signal = "Fair"
            
            ranking.append({
                'Asset': asset,
                'Type': 'Credit' if asset in self.credit_assets else 'Equity',
                'Z-Score': z,
                'Signal': signal
            })
        
        ranking_df = pd.DataFrame(ranking)
        ranking_df = ranking_df.sort_values('Z-Score', ascending=False)
        ranking_df['Rank'] = range(1, len(ranking_df) + 1)
        
        return ranking_df[['Rank', 'Asset', 'Type', 'Z-Score', 'Signal']]
    
    def get_rv_opportunities(self, as_of_date=None):
        """Get current RV trade opportunities"""
        ranking = self.get_current_ranking(as_of_date)
        
        opportunities = {}
        
        # Credit RV
        credit_ranking = ranking[ranking['Type'] == 'Credit'].sort_values('Z-Score', ascending=False)
        if len(credit_ranking) > 1:
            richest = credit_ranking.iloc[0]
            cheapest = credit_ranking.iloc[-1]
            opportunities['Credit RV'] = {
                'Short': richest['Asset'],
                'Short Z': richest['Z-Score'],
                'Long': cheapest['Asset'],
                'Long Z': cheapest['Z-Score'],
                'Spread': richest['Z-Score'] - cheapest['Z-Score']
            }
        
        # Equity RV
        equity_ranking = ranking[ranking['Type'] == 'Equity'].sort_values('Z-Score', ascending=False)
        if len(equity_ranking) > 1:
            richest = equity_ranking.iloc[0]
            cheapest = equity_ranking.iloc[-1]
            opportunities['Equity RV'] = {
                'Short': richest['Asset'],
                'Short Z': richest['Z-Score'],
                'Long': cheapest['Asset'],
                'Long Z': cheapest['Z-Score'],
                'Spread': richest['Z-Score'] - cheapest['Z-Score']
            }
            
        return opportunities
    
    def plot_time_series(self, save_path='richness_timeseries.png'):
        """Plot time series of normalized z-scores"""
        fig, axes = plt.subplots(2, 1, figsize=(14, 10))
        
        # Credit panel
        ax1 = axes[0]
        for asset in self.credit_assets:
            ax1.plot(self.normalized_z_scores.index, self.normalized_z_scores[asset], 
                    label=asset, linewidth=1.5)
        
        ax1.axhline(y=2, color='r', linestyle='--', linewidth=1, alpha=0.5)
        ax1.axhline(y=-2, color='g', linestyle='--', linewidth=1, alpha=0.5)
        ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5, alpha=0.3)
        ax1.fill_between(self.normalized_z_scores.index, 1, 2, alpha=0.1, color='red')
        ax1.fill_between(self.normalized_z_scores.index, -2, -1, alpha=0.1, color='green')
        ax1.set_ylabel('Z-Score (Positive=Rich)', fontsize=11)
        ax1.set_title('Credit Indices: Rich/Cheap Over Time', fontsize=12, fontweight='bold')
        ax1.legend(loc='best', fontsize=9)
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(-4, 4)
        
        # Equity panel
        ax2 = axes[1]
        for asset in self.equity_assets:
            ax2.plot(self.normalized_z_scores.index, self.normalized_z_scores[asset], 
                    label=asset, linewidth=1.5)
        
        ax2.axhline(y=2, color='r', linestyle='--', linewidth=1, alpha=0.5)
        ax2.axhline(y=-2, color='g', linestyle='--', linewidth=1, alpha=0.5)
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5, alpha=0.3)
        ax2.fill_between(self.normalized_z_scores.index, 1, 2, alpha=0.1, color='red')
        ax2.fill_between(self.normalized_z_scores.index, -2, -1, alpha=0.1, color='green')
        ax2.set_ylabel('Z-Score (Positive=Rich)', fontsize=11)
        ax2.set_xlabel('Date', fontsize=11)
        ax2.set_title('Equity Indices: Rich/Cheap Over Time', fontsize=12, fontweight='bold')
        ax2.legend(loc='best', fontsize=9)
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(-4, 4)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"[OK] Time series chart saved to {save_path}")
        
    def plot_current_ranking(self, save_path='current_ranking.png', as_of_date=None):
        """Plot current rich/cheap ranking"""
        ranking = self.get_current_ranking(as_of_date)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        colors = ['darkred' if z > 2 else 'red' if z > 1 else 
                 'darkgreen' if z < -2 else 'green' if z < -1 else 'gray' 
                 for z in ranking['Z-Score']]
        
        ax.barh(ranking['Asset'], ranking['Z-Score'], color=colors, alpha=0.7, edgecolor='black')
        
        ax.axvline(x=2, color='darkred', linestyle='--', linewidth=1, alpha=0.5)
        ax.axvline(x=-2, color='darkgreen', linestyle='--', linewidth=1, alpha=0.5)
        ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
        
        date_str = self.normalized_z_scores.index[-1].date() if as_of_date is None else as_of_date
        ax.set_xlabel('Z-Score (Positive=Rich, Negative=Cheap)', fontsize=11)
        ax.set_title(f'Rich/Cheap Ranking as of {date_str}', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')
        ax.set_xlim(-3, 3)
        
        # Add value labels
        for i, row in ranking.iterrows():
            z = row['Z-Score']
            ax.text(z + 0.15 if z > 0 else z - 0.15, row['Rank']-1, f'{z:.2f}', 
                   va='center', ha='left' if z > 0 else 'right', fontsize=9)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"[OK] Current ranking chart saved to {save_path}")
        
    def save_results(self, output_path='pca_results.csv'):
        """Save normalized z-scores to CSV"""
        self.normalized_z_scores.to_csv(output_path)
        print(f"[OK] Results saved to {output_path}")
        
    def run_full_analysis(self):
        """Run complete analysis pipeline"""
        self.load_data()
        self.run_pca()
        self.calculate_residuals()
        
        # Print current ranking
        print("\n" + "="*70)
        print("CURRENT RICH/CHEAP RANKING")
        print("="*70)
        print(self.get_current_ranking().to_string(index=False))
        
        # Print RV opportunities
        print("\n" + "="*70)
        print("RELATIVE VALUE OPPORTUNITIES")
        print("="*70)
        rv_opps = self.get_rv_opportunities()
        for trade_type, details in rv_opps.items():
            print(f"\n{trade_type} (Spread = {details['Spread']:.2f} std):")
            print(f"  SHORT {details['Short']:15} (Z = {details['Short Z']:+.2f})")
            print(f"  LONG  {details['Long']:15} (Z = {details['Long Z']:+.2f})")
        
        return self


# Example usage
if __name__ == "__main__":
    # Initialize analyzer
    analyzer = PCARichnessAnalyzer('PCA_Cohort_Candidates.xlsx')
    
    # Run full analysis
    analyzer.run_full_analysis()
    
    # Create visualizations
    analyzer.plot_time_series('richness_timeseries.png')
    analyzer.plot_current_ranking('current_ranking.png')
    
    # Save results
    analyzer.save_results('normalized_z_scores.csv')
    
    print("\n[OK] Analysis complete!")
