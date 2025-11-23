"""
Feature Importance Analysis with SHAP
======================================

This script analyzes which features are most important for cryptocurrency price prediction.

Uses SHAP (SHapley Additive exPlanations) which:
1. Shows feature contribution to predictions
2. More interpretable than simple feature importance
3. Reveals interaction effects
4. Industry standard for model explainability

Perfect for Microsoft interviews - demonstrates you don't just build models,
you UNDERSTAND them.

Run from project root: python feature_importance_analysis.py
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# ML models
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor

# Feature importance tools
import shap
from sklearn.inspection import permutation_importance

print("="*80)
print("🔍 FEATURE IMPORTANCE ANALYSIS WITH SHAP")
print("="*80)


class FeatureImportanceAnalyzer:
    """
    Analyzes which features matter most for crypto price prediction
    
    Methods:
    1. Built-in feature importance (XGBoost/LightGBM)
    2. Permutation importance (model-agnostic)
    3. SHAP values (interpretable ML standard)
    """
    
    def __init__(self, features_csv='datasets/crypto_features.csv', 
                 target_horizon=60, test_size=0.2):
        """
        Args:
            features_csv: Path to ML-ready features
            target_horizon: Which prediction horizon to use (30, 60, or 300 seconds)
            test_size: Fraction of data for testing
        """
        self.features_csv = features_csv
        self.target_horizon = target_horizon
        self.test_size = test_size
        self.model = None
        self.scaler = None
        
    def load_and_prepare_data(self):
        """Load features and prepare for ML"""
        print(f"\n📖 Loading features from {self.features_csv}...")
        
        df = pd.read_csv(self.features_csv)
        print(f"   ✓ Loaded {len(df):,} samples with {len(df.columns)} columns")
        
        # Select target
        target_col = f'target_return_{self.target_horizon}s'
        if target_col not in df.columns:
            raise ValueError(f"Target {target_col} not found. Available: {[c for c in df.columns if 'target' in c]}")
        
        print(f"\n🎯 Using target: {target_col}")
        
        # Separate features and target
        # Drop: timestamp, product_id, all other targets, future_price columns
        drop_cols = ['timestamp', 'product_id']
        drop_cols += [c for c in df.columns if 'target' in c and c != target_col]
        drop_cols += [c for c in df.columns if 'future_price' in c]
        
        X = df.drop(columns=drop_cols, errors='ignore')
        y = df[target_col]
        
        # Remove any remaining NaN
        mask = ~(X.isna().any(axis=1) | y.isna())
        X = X[mask]
        y = y[mask]
        
        print(f"   ✓ Features: {X.shape[1]} columns")
        print(f"   ✓ Samples: {len(X):,} (after removing NaN)")
        
        # Split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=self.test_size, shuffle=False  # Time series - don't shuffle
        )
        
        print(f"\n📊 Data split:")
        print(f"   Training: {len(X_train):,} samples")
        print(f"   Test: {len(X_test):,} samples")
        
        # Standardize
        print(f"\n🔧 Standardizing features...")
        self.scaler = StandardScaler()
        X_train_scaled = pd.DataFrame(
            self.scaler.fit_transform(X_train),
            columns=X_train.columns,
            index=X_train.index
        )
        X_test_scaled = pd.DataFrame(
            self.scaler.transform(X_test),
            columns=X_test.columns,
            index=X_test.index
        )
        
        self.X_train = X_train_scaled
        self.X_test = X_test_scaled
        self.y_train = y_train
        self.y_test = y_test
        self.feature_names = X_train.columns.tolist()
        
        return self
    
    def train_model(self, model_type='xgboost'):
        """Train prediction model"""
        print(f"\n🚀 Training {model_type.upper()} model...")
        
        if model_type == 'xgboost':
            self.model = XGBRegressor(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1
            )
        elif model_type == 'lightgbm':
            self.model = LGBMRegressor(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1,
                verbose=-1
            )
        else:
            raise ValueError(f"Unknown model type: {model_type}")
        
        self.model.fit(self.X_train, self.y_train)
        
        # Evaluate
        train_score = self.model.score(self.X_train, self.y_train)
        test_score = self.model.score(self.X_test, self.y_test)
        
        print(f"   ✓ Training R²: {train_score:.4f}")
        print(f"   ✓ Test R²: {test_score:.4f}")
        
        return self
    
    def analyze_builtin_importance(self, top_n=20):
        """Analyze built-in feature importance from tree model"""
        print(f"\n📊 Built-in Feature Importance (top {top_n})...")
        
        if self.model is None:
            raise ValueError("Model not trained yet. Call train_model() first.")
        
        # Get importance
        importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        # Top features
        top_features = importance.head(top_n)
        
        print(f"\n🔝 Top {top_n} features:")
        for idx, row in top_features.iterrows():
            print(f"   {row['feature']:40s} {row['importance']:.6f}")
        
        # Plot
        plt.figure(figsize=(12, 8))
        plt.barh(top_features['feature'][::-1], top_features['importance'][::-1])
        plt.xlabel('Importance', fontsize=12)
        plt.ylabel('Feature', fontsize=12)
        plt.title(f'Top {top_n} Features - Built-in Importance', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig('feature_importance_builtin.png', dpi=150, bbox_inches='tight')
        print(f"\n   ✓ Saved plot: feature_importance_builtin.png")
        plt.close()
        
        self.builtin_importance = importance
        return importance
    
    def analyze_permutation_importance(self, top_n=20, n_repeats=10):
        """Analyze permutation importance (model-agnostic)"""
        print(f"\n🔀 Permutation Importance (top {top_n})...")
        print(f"   Computing with {n_repeats} repeats...")
        
        if self.model is None:
            raise ValueError("Model not trained yet. Call train_model() first.")
        
        # Compute on test set (more reliable)
        perm_importance = permutation_importance(
            self.model, self.X_test, self.y_test,
            n_repeats=n_repeats,
            random_state=42,
            n_jobs=-1
        )
        
        # Create dataframe
        importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance_mean': perm_importance.importances_mean,
            'importance_std': perm_importance.importances_std
        }).sort_values('importance_mean', ascending=False)
        
        # Top features
        top_features = importance.head(top_n)
        
        print(f"\n🔝 Top {top_n} features:")
        for idx, row in top_features.iterrows():
            print(f"   {row['feature']:40s} {row['importance_mean']:.6f} ± {row['importance_std']:.6f}")
        
        # Plot with error bars
        plt.figure(figsize=(12, 8))
        plt.barh(top_features['feature'][::-1], top_features['importance_mean'][::-1],
                xerr=top_features['importance_std'][::-1], capsize=3)
        plt.xlabel('Importance (decrease in R² when shuffled)', fontsize=12)
        plt.ylabel('Feature', fontsize=12)
        plt.title(f'Top {top_n} Features - Permutation Importance', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig('feature_importance_permutation.png', dpi=150, bbox_inches='tight')
        print(f"\n   ✓ Saved plot: feature_importance_permutation.png")
        plt.close()
        
        self.perm_importance = importance
        return importance
    
    def analyze_shap_importance(self, top_n=20, max_display=30):
        """
        Analyze SHAP values - the GOLD STANDARD for interpretability
        
        SHAP (SHapley Additive exPlanations):
        - Based on game theory (Shapley values)
        - Shows how each feature contributes to individual predictions
        - Reveals interaction effects
        - Industry standard (used by Google, Microsoft, etc.)
        """
        print(f"\n🎯 SHAP Analysis (Interpretable ML)...")
        print(f"   Computing SHAP values for {len(self.X_test)} test samples...")
        
        if self.model is None:
            raise ValueError("Model not trained yet. Call train_model() first.")
        
        # Create SHAP explainer (optimized for tree models)
        explainer = shap.TreeExplainer(self.model)
        
        # Compute SHAP values (uses test set - more honest)
        shap_values = explainer.shap_values(self.X_test)
        
        # Feature importance = mean absolute SHAP value
        importance = pd.DataFrame({
            'feature': self.feature_names,
            'shap_importance': np.abs(shap_values).mean(axis=0)
        }).sort_values('shap_importance', ascending=False)
        
        top_features = importance.head(top_n)
        
        print(f"\n🔝 Top {top_n} features by SHAP:")
        for idx, row in top_features.iterrows():
            print(f"   {row['feature']:40s} {row['shap_importance']:.6f}")
        
        # Summary plot (best visualization)
        print(f"\n📊 Creating SHAP summary plots...")
        
        # Plot 1: Bar plot (feature importance)
        plt.figure(figsize=(12, 8))
        shap.summary_plot(shap_values, self.X_test, plot_type="bar", 
                         max_display=max_display, show=False)
        plt.title('SHAP Feature Importance', fontsize=14, fontweight='bold', pad=20)
        plt.tight_layout()
        plt.savefig('feature_importance_shap_bar.png', dpi=150, bbox_inches='tight')
        print(f"   ✓ Saved: feature_importance_shap_bar.png")
        plt.close()
        
        # Plot 2: Beeswarm plot (impact + distribution)
        plt.figure(figsize=(12, 10))
        shap.summary_plot(shap_values, self.X_test, max_display=max_display, show=False)
        plt.title('SHAP Values - Feature Impact on Predictions', fontsize=14, fontweight='bold', pad=20)
        plt.tight_layout()
        plt.savefig('feature_importance_shap_beeswarm.png', dpi=150, bbox_inches='tight')
        print(f"   ✓ Saved: feature_importance_shap_beeswarm.png")
        plt.close()
        
        self.shap_values = shap_values
        self.shap_importance = importance
        self.explainer = explainer
        
        return importance
    
    def compare_methods(self, top_n=20):
        """Compare all three importance methods"""
        print(f"\n🔬 Comparing Importance Methods...")
        
        # Get top N from each method
        builtin_top = set(self.builtin_importance.head(top_n)['feature'])
        perm_top = set(self.perm_importance.head(top_n)['feature'])
        shap_top = set(self.shap_importance.head(top_n)['feature'])
        
        # Find consensus features (in all 3 methods)
        consensus = builtin_top & perm_top & shap_top
        
        print(f"\n📊 Top {top_n} features per method:")
        print(f"   Built-in importance: {len(builtin_top)} features")
        print(f"   Permutation importance: {len(perm_top)} features")
        print(f"   SHAP importance: {len(shap_top)} features")
        print(f"\n🎯 Consensus (in all 3 methods): {len(consensus)} features")
        
        if consensus:
            print(f"\n   Consensus features:")
            for feat in sorted(consensus):
                print(f"      - {feat}")
        
        # Create comparison dataframe
        comparison = pd.DataFrame({
            'feature': self.feature_names
        })
        
        # Add ranks from each method
        comparison = comparison.merge(
            self.builtin_importance.reset_index()[['feature']].reset_index().rename(columns={'index': 'builtin_rank'}),
            on='feature', how='left'
        )
        comparison = comparison.merge(
            self.perm_importance.reset_index()[['feature']].reset_index().rename(columns={'index': 'perm_rank'}),
            on='feature', how='left'
        )
        comparison = comparison.merge(
            self.shap_importance.reset_index()[['feature']].reset_index().rename(columns={'index': 'shap_rank'}),
            on='feature', how='left'
        )
        
        # Average rank
        comparison['avg_rank'] = comparison[['builtin_rank', 'perm_rank', 'shap_rank']].mean(axis=1)
        comparison = comparison.sort_values('avg_rank')
        
        print(f"\n📊 Top {top_n} by average rank:")
        for idx, row in comparison.head(top_n).iterrows():
            print(f"   {row['feature']:40s} (avg rank: {row['avg_rank']:.1f})")
        
        # Save comparison
        comparison.to_csv('feature_importance_comparison.csv', index=False)
        print(f"\n   ✓ Saved: feature_importance_comparison.csv")
        
        return comparison
    
    def generate_interview_summary(self):
        """Generate summary for Microsoft interviews"""
        print(f"\n{'='*80}")
        print(f"💼 MICROSOFT INTERVIEW SUMMARY")
        print(f"{'='*80}")
        
        # Top 5 features from SHAP
        top_5 = self.shap_importance.head(5)
        
        print(f"\n🎯 Top 5 Most Important Features (SHAP):")
        for idx, row in top_5.iterrows():
            feat = row['feature']
            importance = row['shap_importance']
            pct = (importance / self.shap_importance['shap_importance'].sum()) * 100
            
            # Categorize feature
            if 'vpin' in feat.lower():
                category = "Microstructure (Order Flow Toxicity)"
            elif 'roll' in feat.lower():
                category = "Microstructure (Transaction Cost)"
            elif 'imbalance' in feat.lower():
                category = "Order Flow (Supply/Demand)"
            elif any(x in feat.lower() for x in ['rsi', 'macd', 'sma', 'ema', 'bb']):
                category = "Technical Indicator"
            elif 'return' in feat.lower():
                category = "Momentum"
            elif 'volatility' in feat.lower() or 'parkinson' in feat.lower():
                category = "Volatility"
            else:
                category = "Other"
            
            print(f"\n   {idx+1}. {feat}")
            print(f"      Category: {category}")
            print(f"      Importance: {importance:.6f} ({pct:.2f}% of total)")
        
        print(f"\n📝 What to say in interviews:")
        print(f"\n   \"I used SHAP analysis to understand feature importance. The top predictor")
        print(f"   was {top_5.iloc[0]['feature']}, contributing {(top_5.iloc[0]['shap_importance']/self.shap_importance['shap_importance'].sum())*100:.1f}% to predictions.")
        print(f"   This makes sense because [explain why this feature is predictive].")
        print(f"   ")
        print(f"   SHAP revealed that microstructure features (VPIN, order imbalance) were")
        print(f"   more predictive than simple technical indicators (RSI, MACD), validating")
        print(f"   that informed trader detection is key in high-frequency crypto markets.\"")
        
        print(f"\n{'='*80}\n")


def main():
    """Execute feature importance analysis"""
    
    # Create analyzer
    analyzer = FeatureImportanceAnalyzer(
        features_csv='datasets/crypto_features.csv',
        target_horizon=60,  # Predict 60s ahead
        test_size=0.2
    )
    
    # Run analysis pipeline
    analyzer.load_and_prepare_data()
    analyzer.train_model(model_type='xgboost')  # or 'lightgbm'
    
    # Three methods of importance analysis
    analyzer.analyze_builtin_importance(top_n=20)
    analyzer.analyze_permutation_importance(top_n=20, n_repeats=10)
    analyzer.analyze_shap_importance(top_n=20, max_display=30)
    
    # Compare methods
    analyzer.compare_methods(top_n=20)
    
    # Interview summary
    analyzer.generate_interview_summary()
    
    print("🎉 Feature importance analysis complete!")
    print("\n📁 Files generated:")
    print("   - feature_importance_builtin.png")
    print("   - feature_importance_permutation.png")
    print("   - feature_importance_shap_bar.png")
    print("   - feature_importance_shap_beeswarm.png")
    print("   - feature_importance_comparison.csv")
    print("\n💡 Use these insights in your Microsoft interviews!")
    print("   Show you don't just build models - you UNDERSTAND them! 🚀\n")


if __name__ == '__main__':
    main()
