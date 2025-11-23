#!/bin/bash
# GPU Setup Script for NVIDIA DGX-A100
# Run this on the server: bash setup_gpu.sh

echo "🚀 Setting up GPU environment for MarketPrediction"
echo "=================================================="

# Check if we're in a virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "❌ No virtual environment detected!"
    echo "Please activate your venv first: source venv/bin/activate"
    exit 1
fi

echo "✅ Virtual environment active: $VIRTUAL_ENV"

# Install base requirements
echo ""
echo "📦 Installing base requirements..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Base requirements installation failed!"
    exit 1
fi

echo "✅ Base requirements installed"

# Try to install GPU packages
echo ""
echo "🎮 Installing GPU packages (RAPIDS cuDF + cuPy)..."
echo "Note: This might take a few minutes..."

# Use conda if available (recommended for RAPIDS)
if command -v conda &> /dev/null; then
    echo "✅ Conda detected - using conda for RAPIDS installation"
    echo ""
    echo "Run these commands manually:"
    echo "  conda install -c rapidsai -c conda-forge -c nvidia cudf=25.02 cuml=25.02 cupy cudatoolkit=12.0"
    echo ""
    echo "Or create a fresh conda environment:"
    echo "  conda create -n rapids-market python=3.12"
    echo "  conda activate rapids-market"
    echo "  conda install -c rapidsai -c conda-forge -c nvidia cudf=25.02 cuml=25.02 cupy cudatoolkit=12.0"
    echo "  pip install -r requirements.txt"
else
    # Try pip installation
    echo "⚠️  Conda not found - trying pip installation..."
    pip install -r requirements_gpu.txt
    
    if [ $? -ne 0 ]; then
        echo ""
        echo "❌ GPU packages installation failed!"
        echo ""
        echo "💡 Recommended solution: Use conda instead of pip for RAPIDS"
        echo ""
        echo "Steps:"
        echo "1. Install miniconda if not already installed:"
        echo "   wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
        echo "   bash Miniconda3-latest-Linux-x86_64.sh"
        echo ""
        echo "2. Create conda environment:"
        echo "   conda create -n rapids-market python=3.12"
        echo "   conda activate rapids-market"
        echo ""
        echo "3. Install RAPIDS:"
        echo "   conda install -c rapidsai -c conda-forge -c nvidia cudf=25.02 cuml=25.02 cupy cudatoolkit=12.0"
        echo ""
        echo "4. Install base requirements:"
        echo "   pip install -r requirements.txt"
        echo ""
        exit 1
    fi
fi

# Verify GPU installation
echo ""
echo "🧪 Verifying GPU installation..."
python -c "
import sys
try:
    import cudf
    print('✅ cuDF imported successfully')
    print(f'   Version: {cudf.__version__}')
except ImportError as e:
    print(f'❌ cuDF import failed: {e}')
    sys.exit(1)

try:
    import cupy as cp
    print('✅ cuPy imported successfully')
    print(f'   Version: {cp.__version__}')
    
    # Test GPU
    arr = cp.array([1, 2, 3])
    print('✅ GPU test successful')
    print(f'   GPU Device: {cp.cuda.Device()}')
except ImportError as e:
    print(f'❌ cuPy import failed: {e}')
    sys.exit(1)
except Exception as e:
    print(f'❌ GPU test failed: {e}')
    sys.exit(1)

print()
print('🎉 GPU environment setup complete!')
"

if [ $? -eq 0 ]; then
    echo ""
    echo "=================================================="
    echo "✅ GPU Setup Complete!"
    echo "=================================================="
    echo ""
    echo "You can now run:"
    echo "  python data_pipeline/stage2_orderbook_builder_GPU.py --all"
    echo "  python data_pipeline/stage3_ml_features_GPU.py"
    echo ""
    echo "Or open the notebook with GPU kernel:"
    echo "  jupyter notebook data_exploration.ipynb"
    echo ""
else
    echo ""
    echo "❌ Setup incomplete - see errors above"
    exit 1
fi
