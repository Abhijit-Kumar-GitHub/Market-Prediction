# 📈 Cryptocurrency Market Prediction using Machine Learning

A comprehensive predictive analytics project analyzing high-frequency cryptocurrency market data using supervised and unsupervised learning techniques.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Project Overview

This project implements a **two-stage machine learning pipeline** to predict cryptocurrency price movements:

1. **Stage 1 (Unsupervised):** Identify market regimes (bullish, bearish, neutral) using clustering
2. **Stage 2 (Supervised):** Predict price changes and direction using regime-aware models

**Key Achievements:**
- ✅ Collected **2 weeks** of real-time Level 2 order book data from Coinbase
- ✅ Engineered **20+ features** from high-frequency market microstructure data
- ✅ Trained and compared **6 machine learning models** (3 supervised, 3 unsupervised)
- ✅ Achieved **XX% accuracy** in predicting 60-second price movements

## 📊 Dataset

### Data Collection
- **Source:** Coinbase Advanced Trade WebSocket API
- **Instruments:** BTC-USD, ETH-USD
- **Duration:** 14 days continuous collection
- **Granularity:** Sub-second (real-time)
- **Data Types:**
  - Level 2 Order Book (bid/ask depth, quantities)
  - Ticker Data (price, volume, 24h statistics)

### Dataset Statistics
```
Total Records:        X,XXX,XXX
Level 2 Updates:      X,XXX,XXX
Ticker Updates:       XXX,XXX
Features Engineered:  25
Training Samples:     XXX,XXX
Test Samples:         XX,XXX
```

## 🔧 Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Data Collection Layer                     │
│  (data_collector.py - WebSocket → JSONL files)              │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                 Feature Engineering Layer                   │
│  (feature_engineer.py - Order Book → ML Features)           │
│  • Order Book Imbalance  • Spread Analysis                  │
│  • Market Depth          • Volatility Metrics               │
│  • Price Momentum        • Volume Trends                    │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│              Unsupervised Learning (Stage 1)                │
│  • K-Means Clustering    → Market Regime Detection          │
│  • Hierarchical Clustering → Regime Validation              │
│  • Association Rules     → Pattern Discovery                │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│               Supervised Learning (Stage 2)                 │
│  Regression:                  Classification:               │
│  • Linear Regression          • Logistic Regression         │
│  • Polynomial Regression      • Decision Trees              │
│  • SVR                        • SVM                         │
│  • Neural Network (MLP)       • Random Forest               │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│                    Model Evaluation                          │
│  • Cross-validation  • Confusion Matrix  • Feature Importance│
└──────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Installation
```bash
# Clone repository
git clone https://github.com/yourusername/MarketPrediction.git
cd MarketPrediction

# Install dependencies
pip install -r requirements.txt
```

### Data Collection
```bash
# Start 24/7 data collection
python run_collector_24x7.py

# Or run single session
python data_collector.py
```

### Feature Engineering
```bash
# Process raw data into ML features
python feature_engineer.py

# Output: crypto_features.csv
```

### Model Training
```bash
# Run full pipeline
python train_models.py

# Or run specific models
python models/regression_models.py
python models/classification_models.py
python models/clustering_models.py
```

### Evaluation & Visualization
```bash
# Launch Jupyter notebook
jupyter notebook notebooks/model_comparison.ipynb
```

## 📁 Project Structure

```
MarketPrediction/
│
├── data_collector.py           # Real-time data collection
├── feature_engineer.py         # Feature extraction pipeline
├── run_collector_24x7.py       # Robust data collection runner
├── requirements.txt            # Dependencies
│
├── crypto_data_jsonl/          # Raw data (JSONL format)
│   ├── level2_YYYYMMDD.txt
│   └── ticker_YYYYMMDD.txt
│
├── processed_data/             # Engineered features
│   ├── crypto_features.csv
│   └── train_test_split/
│
├── models/                     # Model implementations
│   ├── regression_models.py    # Linear, Polynomial, SVR
│   ├── classification_models.py # Logistic, Decision Tree, SVM
│   ├── clustering_models.py    # K-Means, Hierarchical
│   ├── neural_networks.py      # MLP, RNN
│   └── model_comparison.py     # Cross-validation & metrics
│
├── notebooks/                  # Jupyter notebooks
│   ├── 01_exploratory_analysis.ipynb
│   ├── 02_feature_engineering.ipynb
│   ├── 03_supervised_models.ipynb
│   ├── 04_unsupervised_models.ipynb
│   └── 05_model_comparison.ipynb
│
├── results/                    # Model outputs
│   ├── metrics/
│   ├── plots/
│   └── saved_models/
│
├── docs/                       # Documentation
│   ├── technical_report.pdf
│   ├── presentation.pptx
│   └── methodology.md
│
└── tests/                      # Unit tests
    └── test_feature_engineer.py
```

## 🧪 Methodology

### Feature Engineering

**Order Book Features:**
- `best_bid`, `best_ask`: Top of book prices
- `mid_price`: `(best_bid + best_ask) / 2`
- `spread`: Bid-ask spread in $ and %
- `order_imbalance`: `(bid_volume - ask_volume) / total_volume`
- `depth_bid/ask_0.1%`: Volume within 0.1% of mid-price

**Market Microstructure:**
- `volume_ratio`: Current vs. rolling average
- `price_momentum`: Rate of price change
- `volatility`: Rolling standard deviation
- `trade_intensity`: Frequency of order book updates

**Target Variables:**
- **Regression:** `price_change_60s` (% change in 60 seconds)
- **Classification:** `direction` (Up/Down/Flat based on ±0.05% threshold)

### Model Selection Rationale

| Model | Purpose | Why Chosen |
|-------|---------|------------|
| **Linear Regression** | Baseline price prediction | Simple, interpretable |
| **Polynomial Regression** | Non-linear price dynamics | Captures market curves |
| **Logistic Regression** | Direction classification | Fast, probabilistic |
| **Decision Tree** | Rule-based trading signals | Interpretable thresholds |
| **SVM** | Complex boundary detection | Handles high-dim features |
| **K-Means** | Market regime detection | Unsupervised segmentation |
| **Hierarchical Clustering** | Regime validation | Dendogram analysis |
| **Neural Network (MLP)** | Deep feature learning | State-of-the-art performance |

## 📈 Results

### Model Performance Comparison

| Model | MAE | RMSE | R² | Accuracy | F1-Score |
|-------|-----|------|----|---------:|----------|
| Linear Regression | X.XX | X.XX | 0.XX | - | - |
| Polynomial Reg. | X.XX | X.XX | 0.XX | - | - |
| SVR | X.XX | X.XX | 0.XX | - | - |
| Logistic Regression | - | - | - | XX.X% | 0.XX |
| Decision Tree | - | - | - | XX.X% | 0.XX |
| SVM | - | - | - | XX.X% | 0.XX |
| MLP | X.XX | X.XX | 0.XX | XX.X% | 0.XX |

### Key Findings

1. **Market Regimes Identified:**
   - 🟢 **Cluster 0 (Bullish):** High bid volume, positive momentum
   - 🔴 **Cluster 1 (Bearish):** High ask volume, negative momentum
   - ⚪ **Cluster 2 (Neutral):** Balanced book, low volatility

2. **Most Predictive Features:**
   - Order Book Imbalance (OBI)
   - Spread percentage
   - Volume ratio
   - Price momentum

3. **Best Performing Model:**
   - **[Model Name]** achieved **XX%** accuracy in predicting 60-second movements
   - **[Regime-aware model]** improved accuracy by **X%** over baseline

### Visualizations

- Feature correlation heatmap
- Cluster visualization (PCA 2D projection)
- Confusion matrices
- Feature importance plots
- Actual vs. Predicted price charts
- Regime transition matrix

## 🎓 Academic Context

This project was developed as part of **Predictive Analytics** coursework, covering:

- ✅ Data Preprocessing & Feature Engineering
- ✅ Supervised Learning: Regression & Classification
- ✅ Unsupervised Learning: Clustering & Pattern Detection
- ✅ Dimensionality Reduction: PCA
- ✅ Neural Networks: MLP, RNN
- ✅ Model Evaluation: Cross-validation, Bias-Variance Trade-off

## 🔮 Future Enhancements

- [ ] **Real-time prediction API** using Flask/FastAPI
- [ ] **Recurrent Neural Networks** for sequence modeling
- [ ] **Reinforcement Learning** for trading strategy optimization
- [ ] **Multi-asset correlation** analysis (BTC, ETH, altcoins)
- [ ] **Sentiment analysis** integration (Twitter, news)
- [ ] **Backtesting framework** with trading simulation

## 📚 Technologies Used

- **Languages:** Python 3.8+
- **Data Collection:** WebSocket, JSON
- **Data Processing:** Pandas, NumPy
- **Machine Learning:** Scikit-learn, TensorFlow/Keras
- **Visualization:** Matplotlib, Seaborn, Plotly
- **Development:** Jupyter Notebook, Git

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

## 👤 Author

**[Your Name]**
- 🎓 [Lovely Professional University]
- 📧 [abhijitabhi127@gmail.com]
- 💼 [LinkedIn](https://www.linkedin.com/in/farspawn/)
- 🐙 [GitHub](https://github.com/Abhijit-Kumar-GitHub)

## 🙏 Acknowledgments

- Coinbase for providing the Advanced Trade WebSocket API
- Course Instructor: Mrs. Aashima
- Data collection infrastructure: Access to Nvidia lab (GDX 1000 Xenon Server), courtesy of LPU.

---

⭐ **If you found this project useful, please consider giving it a star!**

📝 **Citation:**
```bibtex
@misc{prediction_on_crypto,
  author = {Abhijit},
  title = {Cryptocurrency Market Prediction using Machine Learning},
  year = {2025},
  publisher = {GitHub},
  url = {https://github.com/}
}
```
