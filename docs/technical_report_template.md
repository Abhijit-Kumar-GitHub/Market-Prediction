# Cryptocurrency Market Prediction using Machine Learning
## Technical Report

**Author:** [Your Name]  
**Course:** Predictive Analytics  
**Institution:** [Your University]  
**Date:** [Submission Date]  

---

## Abstract

This report presents a comprehensive machine learning approach to predicting cryptocurrency price movements using high-frequency market microstructure data. We collected 14 days of real-time Level 2 order book data from Coinbase, engineered 25 features, and implemented a two-stage prediction pipeline combining unsupervised regime detection with supervised price prediction. Our results demonstrate that [Key Finding], with the best model achieving [XX%] accuracy in predicting 60-second price movements.

**Keywords:** Machine Learning, Cryptocurrency, Market Prediction, Order Book, Clustering, Classification

---

## Table of Contents

1. Introduction
2. Literature Review
3. Data Collection & Preparation
4. Methodology
5. Experimental Setup
6. Results & Analysis
7. Discussion
8. Conclusion & Future Work
9. References
10. Appendix

---

## 1. Introduction

### 1.1 Background

Cryptocurrency markets operate 24/7 with high volatility and provide unprecedented access to granular market data. Unlike traditional financial markets, crypto exchanges offer real-time Level 2 order book data to retail participants, enabling sophisticated market microstructure analysis.

### 1.2 Problem Statement

**Primary Research Question:**  
Can machine learning models trained on order book microstructure data predict short-term (60-second) price movements in cryptocurrency markets?

**Sub-questions:**
1. What market regimes exist in cryptocurrency trading?
2. Which features are most predictive of price changes?
3. How do different ML algorithms compare in this task?

### 1.3 Objectives

1. **Data Acquisition:** Collect 2 weeks of continuous Level 2 order book data
2. **Feature Engineering:** Extract meaningful features from raw order book updates
3. **Unsupervised Analysis:** Identify and characterize market regimes
4. **Supervised Modeling:** Train regression and classification models
5. **Model Comparison:** Evaluate 6+ models using rigorous metrics
6. **Interpretability:** Understand which features drive predictions

### 1.4 Significance

- **Academic:** Demonstrates application of full ML pipeline (Units I-VI)
- **Practical:** Real-world data and high-frequency trading relevance
- **Technical:** Combines multiple ML paradigms in novel two-stage approach

---

## 2. Literature Review

### 2.1 Market Microstructure Theory

Order book dynamics reveal supply/demand imbalances. Key concepts:
- **Bid-Ask Spread:** Transaction cost indicator
- **Order Book Imbalance (OBI):** Predictive of short-term price movements [cite studies]
- **Market Depth:** Liquidity measurement

### 2.2 Machine Learning in Finance

**Supervised Learning:**
- Linear models provide interpretable baselines
- Decision trees capture non-linear thresholds
- SVMs excel with high-dimensional financial features
- Neural networks: recent success in HFT [cite studies]

**Unsupervised Learning:**
- K-means for market regime detection [cite studies]
- Hierarchical clustering for regime validation
- Association rules for pattern mining in trading data

### 2.3 Cryptocurrency-Specific Research

[Summarize 3-5 recent papers on crypto prediction, especially those using order book data]

### 2.4 Research Gap

Most studies focus on OHLCV (bar) data; fewer exploit full order book depth. This study contributes by:
1. Using sub-second granularity
2. Combining unsupervised regime detection with supervised prediction
3. Comparing 6+ models systematically

---

## 3. Data Collection & Preparation

### 3.1 Data Source

**API:** Coinbase Advanced Trade WebSocket  
**Channels:**
- `ticker`: Price, volume, 24h statistics
- `level2`: Order book depth (bid/ask levels and quantities)

**Instruments:** BTC-USD, ETH-USD  
**Duration:** 14 days (YYYY-MM-DD to YYYY-MM-DD)  
**Collection Method:** Custom Python WebSocket client (`data_collector.py`)

### 3.2 Raw Data Statistics

| Metric | Value |
|--------|-------|
| Total Level 2 Updates | X,XXX,XXX |
| Total Ticker Updates | XXX,XXX |
| Average Updates/Second (BTC) | XX.X |
| Average Updates/Second (ETH) | XX.X |
| Total File Size | XX.X GB |
| Collection Uptime | 99.X% |

### 3.3 Data Preprocessing

**Step 1: Order Book Reconstruction**
- Parse JSONL files line-by-line
- Maintain in-memory order book state
- Handle updates (new_quantity=0 → remove level)

**Step 2: Snapshot Creation**
- Sample order book every 1 second
- Extract top 10 bid/ask levels

**Step 3: Feature Engineering** (see Section 3.4)

**Step 4: Target Variable Creation**
- Align with ticker data using `pd.merge_asof`
- Create forward-looking targets (T+60s)

**Step 5: Data Cleaning**
- Remove outliers (±3 sigma)
- Handle missing values (forward-fill)
- Remove incomplete rows (no future data)

### 3.4 Feature Engineering

| Feature Category | Features | Rationale |
|-----------------|----------|-----------|
| **Price** | `best_bid`, `best_ask`, `mid_price` | Core market state |
| **Spread** | `spread_absolute`, `spread_pct` | Transaction cost proxy |
| **Volume** | `bid_volume`, `ask_volume`, `total_volume` | Liquidity measurement |
| **Imbalance** | `order_imbalance` = (Vbid - Vask) / Vtotal | Directional pressure |
| **Depth** | `depth_0.1pct`, `depth_0.5pct` | Near-price liquidity |
| **Momentum** | `price_change_1min`, `price_change_5min` | Trend indicators |
| **Volatility** | `rolling_std_1min`, `rolling_std_5min` | Risk measurement |
| **Ticker** | `volume_24h`, `price_pct_chg_24h` | Market context |

**Total Features:** 25

### 3.5 Train-Test Split

- **Training Set:** Days 1-10 (70%)
- **Validation Set:** Days 11-12 (15%)
- **Test Set:** Days 13-14 (15%)

**Rationale:** Time-series split (no shuffling) to prevent look-ahead bias.

---

## 4. Methodology

### 4.1 Overall Pipeline

```
Raw Data → Preprocessing → Feature Engineering → Train/Val/Test Split
    ↓
Stage 1: Unsupervised Learning (Regime Detection)
    ↓
Stage 2: Supervised Learning (Price Prediction)
    ↓
Model Evaluation & Comparison
```

### 4.2 Stage 1: Unsupervised Learning

#### 4.2.1 K-Means Clustering

**Objective:** Identify market regimes

**Algorithm:**
1. Select features: `[order_imbalance, spread_pct, volatility, price_momentum]`
2. Standardize features (Z-score normalization)
3. Apply K-Means with k=3 (bullish, bearish, neutral)
4. Use Elbow Method to validate k

**Output:** Cluster labels as new feature `regime`

#### 4.2.2 Hierarchical Clustering

**Objective:** Validate K-Means results

**Method:** Agglomerative clustering with Ward linkage  
**Analysis:** Dendrogram visualization

#### 4.2.3 Association Rules

**Objective:** Discover patterns leading to price movements

**Method:**
1. Discretize features into bins (High/Medium/Low)
2. Create "transactions" (each second = transaction)
3. Apply Apriori algorithm
4. Extract rules with confidence > 70%

**Example Rule:** `{OBI_High, Spread_Wide} → {Price_Up}` (confidence: 75%)

### 4.3 Stage 2: Supervised Learning

#### 4.3.1 Regression Models

**Target:** `price_change_60s` (continuous, in %)

**Models:**

**1. Simple Linear Regression**
```
price_change = β₀ + β₁ * order_imbalance + ε
```
- **Purpose:** Baseline, test single feature
- **Evaluation:** MAE, RMSE, R²

**2. Multiple Linear Regression**
```
price_change = β₀ + Σ(βᵢ * featureᵢ) + ε
```
- **Purpose:** Multi-feature baseline
- **Features:** All 25 features
- **Regularization:** None (OLS)

**3. Polynomial Regression**
```
price_change = β₀ + β₁x + β₂x² + β₃x³ + ε
```
- **Degree:** 2 and 3 tested
- **Features:** Top 5 features by correlation
- **Purpose:** Capture non-linear relationships

**4. Support Vector Regression (SVR)**
- **Kernel:** RBF (Radial Basis Function)
- **Hyperparameters:** Grid search for C, gamma
- **Purpose:** Non-linear, robust to outliers

**5. Neural Network (MLP Regressor)**
- **Architecture:** [25] → [64] → [32] → [16] → [1]
- **Activation:** ReLU (hidden), Linear (output)
- **Optimizer:** Adam, lr=0.001
- **Epochs:** 100 with early stopping

#### 4.3.2 Classification Models

**Target:** `direction` ∈ {Up, Down, Flat}
- Up: price_change > +0.05%
- Down: price_change < -0.05%
- Flat: -0.05% ≤ price_change ≤ +0.05%

**Models:**

**1. Logistic Regression**
- **Type:** Multinomial (3 classes)
- **Regularization:** L2 penalty
- **Purpose:** Probabilistic baseline

**2. Decision Tree Classifier**
- **Max Depth:** Tuned via cross-validation
- **Criterion:** Gini impurity
- **Purpose:** Interpretable rules

**3. Support Vector Machine (SVM)**
- **Kernel:** RBF
- **Hyperparameters:** Grid search C, gamma
- **Purpose:** Complex boundary detection

**4. Random Forest**
- **Estimators:** 100 trees
- **Purpose:** Ensemble method, feature importance

**5. Neural Network (MLP Classifier)**
- **Architecture:** [25] → [64] → [32] → [3]
- **Activation:** ReLU → Softmax
- **Purpose:** Deep learning baseline

#### 4.3.3 Regime-Aware Models

**Hypothesis:** Models perform better when conditioned on market regime.

**Method:**
1. Add `regime` as categorical feature (one-hot encoded)
2. Train separate models per regime
3. Compare performance vs. regime-agnostic models

### 4.4 Model Evaluation

#### Regression Metrics
- **MAE:** Mean Absolute Error
- **RMSE:** Root Mean Squared Error
- **R² Score:** Explained variance
- **Direction Accuracy:** % correct sign prediction

#### Classification Metrics
- **Accuracy:** Overall correct predictions
- **Precision, Recall, F1-Score:** Per-class and weighted average
- **Confusion Matrix:** Visualization of errors
- **ROC-AUC:** For probabilistic models

#### Cross-Validation
- **Method:** Time-series cross-validation (5 folds)
- **Purpose:** Assess generalization, avoid overfitting

---

## 5. Experimental Setup

### 5.1 Hardware & Software

- **OS:** Windows 10 / Linux
- **CPU:** [Your CPU]
- **RAM:** [Your RAM]
- **Python:** 3.8+
- **Libraries:** scikit-learn 1.0, pandas 1.3, numpy 1.21

### 5.2 Hyperparameter Tuning

| Model | Hyperparameters | Search Method |
|-------|----------------|---------------|
| SVR | C, gamma | Grid Search (5-fold CV) |
| SVM | C, gamma | Grid Search (5-fold CV) |
| Decision Tree | max_depth, min_samples_split | Grid Search |
| Random Forest | n_estimators, max_depth | Random Search |
| MLP | hidden_layers, learning_rate | Manual tuning |

### 5.3 Reproducibility

- **Random Seed:** 42 (all models)
- **Code:** Available at [GitHub URL]
- **Data:** Available upon request (50GB compressed)

---

## 6. Results & Analysis

### 6.1 Exploratory Data Analysis

#### 6.1.1 Feature Distributions
[Include histograms/box plots showing feature distributions]

**Key Observations:**
- Order imbalance is normally distributed around 0
- Spread shows right-skewed distribution
- Volatility spikes during high-activity periods

#### 6.1.2 Feature Correlations
[Include correlation heatmap]

**Top Correlations with Target:**
1. `order_imbalance`: r = 0.XX
2. `price_momentum_1min`: r = 0.XX
3. `spread_pct`: r = -0.XX

### 6.2 Unsupervised Learning Results

#### 6.2.1 K-Means Clustering

**Optimal k:** 3 (validated by Elbow Method, Silhouette Score = 0.XX)

**Cluster Characteristics:**

| Cluster | Size | Interpretation | Key Features |
|---------|------|----------------|--------------|
| 0 | XX% | **Bullish** | High OBI (+), Rising prices |
| 1 | XX% | **Bearish** | High OBI (-), Falling prices |
| 2 | XX% | **Neutral** | Balanced OBI, Low volatility |

[Include PCA scatter plot showing clusters]

#### 6.2.2 Association Rules

**Top 5 Rules:**

| Rule | Support | Confidence | Lift |
|------|---------|------------|------|
| {OBI_High, Spread_Low} → {Price_Up} | 0.XX | 0.75 | 2.1 |
| {OBI_Low, Volume_High} → {Price_Down} | 0.XX | 0.72 | 1.9 |
| ... | ... | ... | ... |

### 6.3 Supervised Learning Results

#### 6.3.1 Regression Performance

| Model | MAE | RMSE | R² | Dir. Acc. |
|-------|-----|------|----|-----------|
| Simple Linear | X.XXX | X.XXX | 0.XX | XX.X% |
| Multiple Linear | X.XXX | X.XXX | 0.XX | XX.X% |
| Polynomial (deg=2) | X.XXX | X.XXX | 0.XX | XX.X% |
| SVR | X.XXX | X.XXX | 0.XX | XX.X% |
| MLP | X.XXX | X.XXX | 0.XX | XX.X% |

**Best Model:** [Model Name] (R² = 0.XX)

[Include Actual vs. Predicted scatter plot]

#### 6.3.2 Classification Performance

| Model | Accuracy | Precision | Recall | F1-Score |
|-------|----------|-----------|--------|----------|
| Logistic Regression | XX.X% | 0.XX | 0.XX | 0.XX |
| Decision Tree | XX.X% | 0.XX | 0.XX | 0.XX |
| SVM | XX.X% | 0.XX | 0.XX | 0.XX |
| Random Forest | XX.X% | 0.XX | 0.XX | 0.XX |
| MLP | XX.X% | 0.XX | 0.XX | 0.XX |

**Best Model:** [Model Name] (Accuracy = XX.X%)

[Include confusion matrices for top 2 models]

#### 6.3.3 Feature Importance

**Top 10 Features (Random Forest):**

1. `order_imbalance` (importance: 0.XX)
2. `price_momentum_1min` (0.XX)
3. `spread_pct` (0.XX)
4. `depth_0.1pct` (0.XX)
5. ...

[Include feature importance bar chart]

### 6.4 Regime-Aware Model Comparison

| Model Type | Baseline Acc. | Regime-Aware Acc. | Improvement |
|------------|--------------|-------------------|-------------|
| Logistic Reg. | XX.X% | XX.X% | +X.X% |
| SVM | XX.X% | XX.X% | +X.X% |
| MLP | XX.X% | XX.X% | +X.X% |

**Finding:** Regime-aware models improve accuracy by average of X.X%

### 6.5 Error Analysis

**Common Misclassifications:**
1. **Flat → Up/Down:** During regime transitions (XX% of errors)
2. **Up ↔ Down:** During high volatility periods (XX% of errors)

**Time-of-Day Analysis:**
- Highest accuracy: [Time window] (XX.X%)
- Lowest accuracy: [Time window] (XX.X%)
- Hypothesis: Liquidity/volume differences

---

## 7. Discussion

### 7.1 Key Findings

1. **Order book imbalance is the strongest single predictor** of short-term price movements
2. **Market regimes exist and are detectable** through unsupervised learning
3. **Non-linear models (SVM, MLP) outperform linear baselines** by X-XX%
4. **Regime-aware models improve accuracy** by incorporating market context

### 7.2 Interpretation

**Why does OBI work?**
- Economic intuition: Imbalanced supply/demand drives prices
- High bid volume → buyers willing to absorb offers → price rises
- Confirmed by association rules: OBI_High → Price_Up (75% confidence)

**Regime detection value:**
- Different regimes exhibit different price dynamics
- "One-size-fits-all" models miss regime-specific patterns
- Future work: Online regime detection for adaptive trading

### 7.3 Limitations

1. **Short prediction horizon (60s):** May not be profitable after transaction costs
2. **Market impact not modeled:** Our predictions assume passive observation
3. **Limited to 2 assets:** Generalization to other cryptos unknown
4. **No macroeconomic features:** News, sentiment, correlations excluded
5. **Survivorship bias:** Data from bull market period (Oct 2025)

### 7.4 Comparison to Literature

[Compare your results to 2-3 similar papers]

Our R² of 0.XX is comparable to [Study A] (0.XX) and outperforms [Study B] (0.XX).

---

## 8. Conclusion & Future Work

### 8.1 Summary

This project successfully demonstrated a two-stage machine learning pipeline for cryptocurrency price prediction:
1. Collected 14 days of high-frequency order book data
2. Engineered 25 predictive features
3. Identified 3 market regimes via clustering
4. Trained 6+ supervised models achieving up to XX% accuracy
5. Validated regime-aware modeling improves performance

### 8.2 Contributions

- **Methodological:** Novel two-stage unsupervised → supervised approach
- **Empirical:** Comprehensive model comparison on real HFT data
- **Practical:** Feature engineering pipeline for order book data

### 8.3 Future Work

**Short-term (Feasible Extensions):**
1. **More assets:** Test on 10+ cryptocurrencies
2. **Longer horizons:** Predict 5-minute, 15-minute movements
3. **Online learning:** Update models as new data arrives
4. **Ensemble methods:** Combine top models via stacking

**Long-term (Research Directions):**
1. **Reinforcement Learning:** Train trading agent in simulated environment
2. **Sentiment integration:** Add Twitter/Reddit sentiment features
3. **Multi-modal learning:** Combine order book + news + sentiment
4. **Causal inference:** Identify causal relationships vs. correlations
5. **Adversarial robustness:** Test against market manipulation

---

## 9. References

[Format according to your university's citation style]

1. [Author, Year] - Order book dynamics paper
2. [Author, Year] - ML in finance survey
3. [Author, Year] - Cryptocurrency prediction study
4. Coinbase API Documentation
5. Scikit-learn Documentation
6. [Add 10-15 academic references]

---

## 10. Appendix

### A. Feature Definitions

[Detailed mathematical definitions of all 25 features]

### B. Model Hyperparameters

[Final hyperparameters for all models]

### C. Code Snippets

[Key code sections, properly commented]

### D. Additional Visualizations

[Extra plots not included in main text]

### E. Raw Data Sample

[Example of raw JSONL format]

---

**Word Count:** ~4,000-5,000 words  
**Figures/Tables:** 15-20  
**References:** 15-20 citations

