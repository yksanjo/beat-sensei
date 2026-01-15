#!/bin/bash
# Beat-Sensei Installer
# One-liner: curl -fsSL https://raw.githubusercontent.com/yksanjo/beat-sensei/main/install.sh | bash

set -e

echo ""
echo "  ____  _____    _  _____   ____  _____ _   _ ____  _____ ___ "
echo " | __ )| ____|  / \|_   _| / ___|| ____| \ | / ___|| ____|_ _|"
echo " |  _ \|  _|   / _ \ | |   \___ \|  _| |  \| \___ \|  _|  | | "
echo " | |_) | |___ / ___ \| |    ___) | |___| |\  |___) | |___ | | "
echo " |____/|_____/_/   \_\_|   |____/|_____|_| \_|____/|_____|___|"
echo ""
echo " Your AI Sample Master - Hip-Hop Edition"
echo " ========================================="
echo ""

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    echo "Install Python from https://python.org or via homebrew: brew install python"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Found Python $PYTHON_VERSION"

# Set install directory
INSTALL_DIR="${HOME}/.beat-sensei"
REPO_URL="https://github.com/yksanjo/beat-sensei.git"

# Clone or update repository
if [ -d "$INSTALL_DIR" ]; then
    # Check if it's the correct repo
    cd "$INSTALL_DIR"
    CURRENT_REMOTE=$(git remote get-url origin 2>/dev/null || echo "")

    if [ "$CURRENT_REMOTE" = "$REPO_URL" ]; then
        echo "Updating existing installation..."
        git pull origin main
    else
        echo "Found old/incorrect installation, reinstalling..."
        cd ..
        rm -rf "$INSTALL_DIR"
        git clone "$REPO_URL" "$INSTALL_DIR"
        cd "$INSTALL_DIR"
    fi
else
    echo "Installing Beat-Sensei..."
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# Create virtual environment
echo "Setting up virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip -q
pip install -e . -q

# Create symlink for easy access
BEAT_SENSEI_BIN="${HOME}/.local/bin/beat-sensei"
mkdir -p "${HOME}/.local/bin"

cat > "$BEAT_SENSEI_BIN" << 'WRAPPER'
#!/bin/bash
source "${HOME}/.beat-sensei/venv/bin/activate"
python -m beat_sensei.cli "$@"
WRAPPER

chmod +x "$BEAT_SENSEI_BIN"

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":${HOME}/.local/bin:"* ]]; then
    echo ""
    echo "Add this to your shell profile (~/.zshrc or ~/.bashrc):"
    echo ""
    echo '  export PATH="$HOME/.local/bin:$PATH"'
    echo ""
    echo "Then restart your terminal or run: source ~/.zshrc"
fi

echo ""
echo "Installation complete!"
echo ""
echo "Quick Start:"
echo "  1. Set up Supabase:          export SUPABASE_URL=your_url"
echo "  2. Set up API key:           export SUPABASE_ANON_KEY=your_key"
echo "  3. Start finding sounds:     beat-sensei"
echo ""
echo "Upload your samples:"
echo "  python scripts/upload_samples.py /path/to/your/samples"
echo ""

# Ask if user wants to download samples now
read -p "Download free sample packs now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    "$BEAT_SENSEI_BIN" download all
fi

echo ""
echo "Let's make some heat!"
echo ""
