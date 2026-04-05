#!/data/data/com.termux/files/usr/bin/bash
# ──────────────────────────────────────────────────────────────────────────────
# NeuroCLI Termux Installer
# Run: bash install_termux.sh
# ──────────────────────────────────────────────────────────────────────────────

set -e

echo ""
echo "  ███╗   ██╗███████╗██╗   ██╗██████╗  ██████╗  ██████╗██╗     ██╗"
echo "  NeuroCLI — Termux Installer"
echo ""

# Update packages
echo "[1/5] Updating pkg..."
pkg update -y && pkg upgrade -y

# Install Python + git
echo "[2/5] Installing Python & git..."
pkg install -y python git

# Upgrade pip
echo "[3/5] Upgrading pip..."
pip install --upgrade pip

# Install core dep
echo "[4/5] Installing core dependencies..."
pip install rich

# Ask which provider
echo ""
echo "Which LLM provider do you want to install?"
echo "  1) groq       (free tier, fast — RECOMMENDED for Termux)"
echo "  2) openai     (GPT-4o etc)"
echo "  3) anthropic  (Claude)"
echo "  4) gemini     (Google)"
echo "  5) all        (install all providers)"
echo "  6) none       (use Ollama local or skip)"
echo ""
read -p "Choice [1]: " CHOICE
CHOICE=${CHOICE:-1}

case $CHOICE in
  1) pip install groq ;;
  2) pip install openai ;;
  3) pip install anthropic ;;
  4) pip install google-generativeai ;;
  5) pip install groq openai anthropic google-generativeai ;;
  6) echo "Skipping provider libs." ;;
  *) echo "Invalid choice, skipping."; ;;
esac

# Optional: DuckDuckGo search
read -p "Install duckduckgo-search? [Y/n]: " DDG
DDG=${DDG:-Y}
if [[ $DDG =~ ^[Yy]$ ]]; then
  pip install duckduckgo-search
fi

# Make launcher script
echo "[5/5] Creating launcher..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create neurocli launcher in PATH
cat > "$PREFIX/bin/neurocli" << EOF
#!/data/data/com.termux/files/usr/bin/bash
cd "$SCRIPT_DIR"
python main.py "\$@"
EOF
chmod +x "$PREFIX/bin/neurocli"

echo ""
echo "✔ NeuroCLI installed! You can now run: neurocli"
echo ""
echo "Quick start:"
echo "  neurocli"
echo "  > /setkey groq YOUR_GROQ_API_KEY"
echo "  > /provider groq"
echo "  > Hello!"
echo ""
