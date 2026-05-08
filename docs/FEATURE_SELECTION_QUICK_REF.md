# Feature Selection Quick Reference - Market Regime Clustering

## 🎯 The Core Principle

> **Market regimes are PATTERNS (volatility states, liquidity conditions), NOT LEVELS (price values).**
> 
> **Use ONLY relative/ratio/percentage features for regime discovery.**

---

## ✅ GOOD Features (Use These)

| Feature Type | Examples | Why It Works |
|-------------|----------|--------------|
| **Spreads (%)** | `spread_bps`, `spread_position`, `spread_zscore` | Measures liquidity regime (tight vs wide) |
| **Order Flow (ratio)** | `imbalance_l5`, `depth_ratio`, `level_imbalance` | Captures buying/selling pressure |
| **Momentum (%)** | `price_momentum_10`, `trade_flow_momentum` | Identifies trending vs ranging |
| **Volatility (%)** | `price_volatility_10`, `imbalance_volatility` | Measures risk regime |
| **Volume (ratio)** | `volume_ratio`, `volume_momentum_10` | Activity level relative to baseline |
| **Impacts (basis)** | `price_impact_total`, `effective_spread_bps` | Transaction cost regime |
| **Microstructure** | `vpin_proxy`, `trade_direction` | Informed trading patterns |

**Common Pattern**: `(X / Y)`, `X.pct_change()`, `(X - mean) / std`, or inherently normalized

---

## ❌ BAD Features (Never Use These for Clustering)

| Feature Type | Examples | Why It Fails |
|-------------|----------|--------------|
| **Absolute Prices** | `mid_price`, `best_bid`, `best_ask` | Captures price level ($94K vs $96K), not regime |
| **Absolute Volumes** | `bid_volume_l5`, `ask_volume_l5` | Varies 1000x, dominates distance |
| **Total Quantities** | `total_bid_qty`, `total_ask_qty` | Absolute scale, not relative |
| **Raw Spread ($)** | `spread` (in dollars) | Use `spread_bps` (percentage) instead |
| **Raw Depths** | `total_bid_depth`, `total_ask_depth` | Use `depth_ratio` instead |

**Common Pattern**: Any feature measured in **dollars**, **BTC**, or **raw counts**

---

## 🔬 The Math Behind It

### Why Standardization Alone Isn't Enough

```python
# Two features, both standardized (mean=0, std=1):
feature_A = (mid_price - μ) / σ     # σ_original = $618
feature_B = (spread_bps - μ) / σ   # σ_original = 0.15

# K-Means distance for two samples:
d² = (A₁ - A₂)² + (B₁ - B₂)²

# If A changes by 0.1σ and B changes by 0.1σ:
d² = (0.1)² + (0.1)² = 0.02

# BUT: In original space
A changed by 0.1 × $618 = $61.80
B changed by 0.1 × 0.15 = 0.015 bps

# $61.80 price move vs 0.015 bps spread change
# → Both weighted equally in clustering!
# → Price levels dominate regime discovery
```

### With Relative Features Only

```python
# Both features measure relative changes:
feature_A = price_momentum_10    # σ_original = 0.0018 (0.18%)
feature_B = spread_bps           # σ_original = 0.15 (15 bps)

# After standardization:
# Similar variance scales in original space
# → Similar signal strength in regime patterns
# → Both contribute meaningfully to clustering
```

---

## 📊 Validation Checklist

Run these checks **before** clustering:

### 1. Variance Ratio Test
```python
max_std = df[features].std().max()
min_std = df[features].std().min()
ratio = max_std / min_std

✅ ratio < 100:  Good! Features have comparable scales
⚠️  ratio < 1000: Acceptable, but review outliers
❌ ratio > 1000: FAIL - likely mixing absolute/relative
```

### 2. Feature Type Audit
```python
for col in features:
    # Check if feature name suggests absolute value
    if any(word in col for word in ['price', 'volume', 'qty', 'depth', 'bid', 'ask']):
        if not any(word in col for word in ['_bps', '_ratio', '_momentum', '_pct', 'imbalance']):
            print(f"⚠️  {col} - Possible absolute feature")
```

### 3. Silhouette Score Reality Check
```python
silhouette_score = ...  # After clustering

✅ 0.30 - 0.60: Good separation, meaningful regimes
⚠️  0.20 - 0.30: Weak separation, review features
❌ < 0.20:      Poor separation, clusters overlap
❌ > 0.80:      Too perfect - likely one dominant cluster
```

### 4. Cluster Balance Check
```python
cluster_pcts = df['cluster'].value_counts(normalize=True) * 100

✅ Each cluster 15-50%:  Balanced, meaningful regimes
⚠️  One cluster > 70%:   Feature dominance issue
❌ One cluster > 90%:    FAIL - clustering collapsed
```

---

## 🎓 Key Learnings

### Why This Matters for Your Project

1. **Feature Engineering (Stage 3)** ✅ Excellent!
   - Created both absolute AND relative features
   - Absolute: For understanding data (`mid_price`)
   - Relative: For modeling (`spread_bps`, `imbalance_l5`)

2. **Clustering (Stage 4)** ⚠️ Feature Selection Critical
   - **Problem**: Originally used ALL numeric features
   - **Issue**: Mixed absolute (price) with relative (spread_bps)
   - **Result**: Clustering by price level, not regime
   - **Fix**: Filter to ONLY relative features

3. **Supervised Models (Stage 5)** ℹ️ Different Rules
   - Can use BOTH absolute and relative features
   - Gradient boosting handles mixed scales well
   - Target is specific prediction, not pattern discovery

### The Mental Model

```
CLUSTERING (Unsupervised)
Goal: Discover patterns
Constraint: All features must capture patterns, not levels
Solution: Relative features only

REGRESSION (Supervised)
Goal: Predict specific outcome
Constraint: None (algorithm handles mixed scales)
Solution: Use all predictive features
```

---

## 💡 Quick Decision Tree

```
Are you doing CLUSTERING to discover regimes?
│
├─ YES → Use ONLY relative features
│         (spread_bps, imbalance_l5, momentum, ratios)
│
└─ NO → Are you doing SUPERVISED prediction?
         │
         └─ YES → Use ALL informative features
                   (absolute + relative, let model select)
```

---

## 📁 Where to Find This in Your Project

```
notebooks/
├── 03_feature_engineering.ipynb   ✅ Creates both absolute & relative
├── 04_unsupervised_clustering.ipynb  🔧 Filter to relative only
└── 05_supervised_models.ipynb     ℹ️ Can use all features

docs/
├── CLUSTERING_BEST_PRACTICES.md   📖 Full explanation
└── FEATURE_SELECTION_QUICK_REF.md 📋 This document
```

---

## 🚀 One-Minute Implementation

```python
# In 04_unsupervised_clustering.ipynb, replace:

# ❌ OLD (includes absolute features)
numeric_cols = [c for c in df.columns 
                if df[c].dtype in ['float32', 'float64']]

# ✅ NEW (relative features only)
REGIME_FEATURES = [
    'spread_bps', 'imbalance_l5', 'price_momentum_10',
    'price_volatility_10', 'volume_ratio', 'depth_ratio',
    'vpin_proxy', 'trade_flow_momentum', 'spread_position',
    # ... add more relative features from your data
]
numeric_cols = [c for c in REGIME_FEATURES if c in df.columns]

# Verify no absolute features leaked
BLACKLIST = ['mid_price', 'best_bid', 'best_ask', 'bid_volume_l5', 
             'ask_volume_l5', 'total_bid_qty', 'total_ask_qty']
numeric_cols = [c for c in numeric_cols if c not in BLACKLIST]
```

**Expected improvement:**
- Cluster distribution: 100%/0%/0% → 25%/35%/40%
- Silhouette score: 0.98 → 0.35-0.55
- Interpretability: Price levels → Market regimes

---

**TL;DR**: For clustering financial data, **features should measure "how" not "how much"** - use percentages/ratios/normalized values, never absolute prices or volumes.

---

## 🚨 IMPORTANT UPDATE: When Clustering Still Fails

Even with perfect feature selection, you might see:

```
Cluster 0: 99.98% of data ❌
Cluster 1: 0.01%
Cluster 2: 0.01%
Silhouette: 0.98 (too high = no separation)
```

**Root Cause**: Your data is too **homogeneous** - no natural clusters exist!

This happens when:
- ✅ You collected data during a **stable market period** (no regime changes)
- ✅ High **autocorrelation** (0.88) - market state persists
- ✅ Low **coefficient of variation** (CV < 0.1) - features don't vary much

**This is NOT a failure** - your data genuinely doesn't have distinct regimes!

### The Solution: Rule-Based Regime Classification

Instead of forcing K-Means on homogeneous data, define regimes using domain knowledge:

```python
# Calculate rolling volatility
df['rolling_vol'] = df['price_volatility_10'].rolling(60).mean()

# Define regime thresholds (33rd and 67th percentiles)
low_threshold = df['rolling_vol'].quantile(0.33)
high_threshold = df['rolling_vol'].quantile(0.67)

# Classify regimes
df['regime'] = 'Medium_Vol'
df.loc[df['rolling_vol'] < low_threshold, 'regime'] = 'Low_Vol'
df.loc[df['rolling_vol'] > high_threshold, 'regime'] = 'High_Vol'

# Result: Balanced 33%/33%/33% by design ✅
```

**Benefits**:
- ✅ Always produces balanced regimes
- ✅ More interpretable (volatility is intuitive)
- ✅ Stable over time (no sensitivity to random initialization)
- ✅ Better for downstream models (consistent regime definitions)

### For Interviews

**❌ DON'T SAY**: "My clustering failed, I don't know why."

**✅ DO SAY**: "I applied K-Means clustering to discover market regimes. The silhouette analysis revealed the data was too homogeneous during this 16-day stable period (autocorrelation coefficient = 0.88). I then implemented a **volatility-based regime classification** using rolling windows, which produced three balanced groups. This approach was more appropriate for the continuous nature of the data and provided more interpretable, stable regimes for downstream prediction models."

**This shows**:
- 🎓 You understand when algorithms are appropriate
- 🎓 You can diagnose issues scientifically
- 🎓 You adapt methodology based on data characteristics
- 🎓 You prioritize interpretability and stability

---

See `notebooks/04_unsupervised_clustering.ipynb` Section 4b for full implementation.
