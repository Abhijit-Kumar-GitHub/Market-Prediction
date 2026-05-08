# Clustering Best Practices for Financial Market Data

## 🎯 Critical Insight: Feature Selection for Market Regime Clustering

### The Problem: Scale Dominance in Distance-Based Clustering

When performing K-Means or other distance-based clustering on financial market data, **the choice of features is more important than the algorithm itself**.

#### ❌ Common Mistake: Mixing Absolute and Relative Features

```python
# BAD EXAMPLE - DO NOT DO THIS
features = [
    'mid_price',        # ~$95,000 (absolute)
    'spread_bps',       # ~0.15 (relative)
    'bid_volume_l5',    # ~450.0 (absolute)
    'imbalance_l5',     # ~0.05 (ratio)
]

# After standardization:
# mid_price std: ~$618
# spread_bps std: ~0.15
# Variance ratio: 4,120x difference!
```

**Why this fails:**
1. K-Means uses **Euclidean distance**: `d = √(Σ(xi - yi)²)`
2. High-variance features **dominate** the distance calculation
3. Even after standardization, the underlying variance structure remains
4. Result: Clusters form around **price levels** ($94K vs $96K), not **market regimes**

#### ✅ Correct Approach: Scale-Invariant Features Only

```python
# GOOD EXAMPLE - USE THIS
features = [
    # Spread features (percentage-based)
    'spread_bps',              # (ask - bid) / mid * 10000
    'spread_position',         # Relative position in 20-period range
    'spread_zscore',           # Z-score vs rolling mean
    'spread_volatility',       # Rolling std of spread
    
    # Order flow (ratio/normalized)
    'imbalance_l5',            # (bid_vol - ask_vol) / total
    'imbalance_volatility',    # Volatility of imbalance
    'imbalance_momentum',      # Change in imbalance
    
    # Price dynamics (percentage returns)
    'price_momentum_10',       # pct_change(10)
    'price_volatility_10',     # Rolling std of returns
    
    # Volume (ratio-based)
    'volume_ratio',            # current / moving average
    'volume_momentum_10',      # Momentum in volume
    
    # Liquidity (ratio-based)
    'depth_ratio',             # bid_depth / ask_depth
    'price_impact_total',      # Impact per unit
]
```

**Why this works:**
1. All features measure **relative changes** or **ratios**
2. Comparable scales across all features
3. Captures **market regimes** (patterns), not price levels
4. Standardization is effective when scales are already comparable

---

## 📊 What Are Market Regimes?

Market regimes are **distinct market states** characterized by:

### 1. **Volatility Regimes**
- **High Volatility**: Large price swings, uncertainty
- **Low Volatility**: Stable prices, predictable
- **Measured by**: `price_volatility_10`, `spread_volatility`

### 2. **Momentum Regimes**
- **Trending Up**: Persistent buying pressure
- **Trending Down**: Persistent selling pressure
- **Ranging**: No clear direction
- **Measured by**: `price_momentum_10`, `trade_flow_momentum`

### 3. **Liquidity Regimes**
- **Liquid**: Tight spreads, deep order book
- **Illiquid**: Wide spreads, thin order book
- **Measured by**: `spread_bps`, `depth_ratio`, `price_impact_total`

### 4. **Order Flow Regimes**
- **Buyer Dominated**: Positive imbalance
- **Seller Dominated**: Negative imbalance
- **Balanced**: Neutral imbalance
- **Measured by**: `imbalance_l5`, `trade_direction`, `vpin_proxy`

**Key Point**: These are all **relative** characteristics, independent of absolute price levels!

---

## 🔬 Mathematical Explanation

### Why Standardization Isn't Enough

Many believe that standardizing features (z-score normalization) solves the scale problem:

```python
X_standardized = (X - μ) / σ  # Mean=0, Std=1 for all features
```

**This is partially true**, but misses a critical point:

#### Example: Bitcoin Price Clustering

**Scenario 1: Price levels ($94K vs $96K)**
```
mid_price: [94000, 94500, 95000, 95500, 96000]
std(mid_price) = 618

After standardization → all values spread across [-1.6, +1.6]
```

**Scenario 2: Spread regime (0.14% vs 0.16%)**
```
spread_bps: [0.14, 0.145, 0.15, 0.155, 0.16]
std(spread_bps) = 0.0063

After standardization → all values spread across [-1.6, +1.6]
```

**The Problem:**
- Both features now have std=1 after standardization ✓
- BUT: Original variance ratio was 618 / 0.0063 = 98,095x
- In K-Means distance calculation:
  ```
  d² = (mid_price_std)² + (spread_bps_std)²
     = 1² + 1² = 2
  ```
- Looks equal, but the **signal-to-noise ratio** differs by 98,000x!

### The Correct Solution

Use features where the **underlying signal** is comparable:

```python
# Both features measure relative changes
price_momentum_10 = mid_price.pct_change(10)    # -0.002 to +0.002
spread_momentum = spread_bps.pct_change(10)     # -0.15 to +0.15

# Similar scales in original space
# → Similar signal strength after standardization
# → Both contribute meaningfully to clustering
```

---

## 📈 Expected Results

### Before Fix (Absolute Features Included)

```
CLUSTER DISTRIBUTION:
Cluster 0: 137,279 samples (100.0%) ← Everything in one cluster!
Cluster 1: 9 samples (0.0%)
Cluster 2: 16 samples (0.0%)

SILHOUETTE SCORE: 0.98 ← Too high = no real separation

INTERPRETATION:
- Clustering failed to find meaningful regimes
- All data collapsed into single cluster
- Outliers: Only extreme events (flash crashes, etc.)
```

### After Fix (Relative Features Only)

```
CLUSTER DISTRIBUTION:
Cluster 0 (High Volatility):    35,000 samples (25%)
Cluster 1 (Trending):           48,000 samples (35%)
Cluster 2 (Consolidation):      54,000 samples (40%)

SILHOUETTE SCORE: 0.42 ← Realistic separation

INTERPRETATION:
- Three distinct market regimes identified
- Balanced distribution (~25-40% each)
- Clusters represent genuine market states
```

---

## 🛠️ Implementation Guidelines

### Step 1: Define Regime-Appropriate Features

Create a **whitelist** of relative features:

```python
REGIME_FEATURES = [
    # Spread features (percentage)
    'spread_bps', 'spread_position', 'spread_zscore', 'spread_volatility',
    
    # Order flow (ratio)
    'imbalance_l5', 'imbalance_volatility', 'imbalance_momentum',
    
    # Price dynamics (percentage)
    'price_momentum_5', 'price_momentum_10', 'price_volatility_10',
    
    # Volume (ratio)
    'volume_ratio', 'volume_momentum_10',
    
    # Liquidity (ratio)
    'depth_ratio', 'price_impact_total',
    
    # Microstructure (derived)
    'vpin_proxy', 'effective_spread_bps', 'trade_direction'
]
```

### Step 2: Create a Blacklist of Absolute Features

Explicitly exclude features that capture levels, not patterns:

```python
ABSOLUTE_FEATURES_BLACKLIST = [
    # Price levels
    'mid_price', 'best_bid', 'best_ask', 'weighted_mid',
    
    # Volume levels
    'bid_volume_l5', 'ask_volume_l5', 'total_bid_qty', 'total_ask_qty',
    
    # Absolute spreads (use spread_bps instead)
    'spread',  # Absolute spread in dollars
    
    # Raw depths (use depth_ratio instead)
    'total_bid_depth', 'total_ask_depth',
]
```

### Step 3: Validate Feature Selection

```python
def validate_clustering_features(df, feature_cols):
    """Ensure all features are scale-invariant."""
    
    stats = []
    for col in feature_cols:
        stats.append({
            'feature': col,
            'std': df[col].std(),
            'range': df[col].max() - df[col].min()
        })
    
    stats_df = pd.DataFrame(stats).sort_values('std', ascending=False)
    
    # Check variance ratio
    max_std = stats_df['std'].max()
    min_std = stats_df['std'].min()
    variance_ratio = max_std / min_std
    
    print(f"Variance ratio: {variance_ratio:.1f}x")
    
    if variance_ratio > 1000:
        print("❌ FAIL: Very high variance ratio!")
        print("   Likely mixing absolute and relative features.")
        print(f"   Max std feature: {stats_df.iloc[0]['feature']}")
        print(f"   Min std feature: {stats_df.iloc[-1]['feature']}")
        return False
    elif variance_ratio > 100:
        print("⚠️  WARNING: High variance ratio.")
        print("   Some features may dominate clustering.")
        return True
    else:
        print("✅ PASS: Features have comparable scales.")
        return True
```

### Step 4: Interpret Clusters as Regimes

After clustering, characterize regimes using **multiple dimensions**:

```python
def characterize_regimes(df, cluster_col='cluster'):
    """Multi-dimensional regime interpretation."""
    
    regime_stats = df.groupby(cluster_col).agg({
        'price_volatility_10': 'mean',    # Volatility dimension
        'price_momentum_10': 'mean',      # Momentum dimension
        'spread_bps': 'mean',             # Liquidity dimension
        'imbalance_l5': 'mean',           # Order flow dimension
        'vpin_proxy': 'mean'              # Informed trading dimension
    })
    
    # Classify each cluster
    for cluster in regime_stats.index:
        characteristics = []
        
        # Volatility
        vol = regime_stats.loc[cluster, 'price_volatility_10']
        if vol > regime_stats['price_volatility_10'].quantile(0.66):
            characteristics.append('HighVol')
        elif vol < regime_stats['price_volatility_10'].quantile(0.33):
            characteristics.append('LowVol')
        
        # Momentum
        mom = regime_stats.loc[cluster, 'price_momentum_10']
        if mom > 0.0001:
            characteristics.append('Bullish')
        elif mom < -0.0001:
            characteristics.append('Bearish')
        else:
            characteristics.append('Neutral')
        
        # Liquidity
        spread = regime_stats.loc[cluster, 'spread_bps']
        if spread > regime_stats['spread_bps'].quantile(0.66):
            characteristics.append('Illiquid')
        
        print(f"Cluster {cluster}: {' + '.join(characteristics)}")
```

---

## 📚 References

1. **Market Microstructure Theory**
   - O'Hara, M. (1995). Market Microstructure Theory
   - Focus on relative measures (spreads, imbalances, impacts)

2. **Volatility Regimes**
   - Hamilton, J.D. (1989). Regime-switching models
   - Volatility clustering in relative terms

3. **Order Flow Analysis**
   - Easley, D., et al. (2012). The Volume Clock
   - VPIN and order flow imbalance as relative measures

4. **Clustering Financial Data**
   - Nystrup, P., et al. (2018). Regime-based asset allocation
   - Emphasis on normalized financial ratios

---

## ✅ Checklist for Clustering Financial Data

Before running K-Means or other distance-based clustering:

- [ ] All features are relative (percentages, ratios, or normalized)
- [ ] No absolute price levels (mid_price, best_bid, etc.)
- [ ] No absolute volumes (bid_volume_l5, ask_volume_l5, etc.)
- [ ] Variance ratio (max_std / min_std) < 1000x
- [ ] Feature correlation matrix checked (avoid redundancy)
- [ ] Silhouette score realistic (0.3-0.6, not 0.9+)
- [ ] Cluster sizes balanced (not 100% in one cluster)
- [ ] Regimes interpretable using multiple dimensions

---

**Last Updated**: December 2025  
**Author**: Market Prediction Project  
**Notebook**: `04_unsupervised_clustering.ipynb`
