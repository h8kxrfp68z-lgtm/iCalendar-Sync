#!/bin/bash
# Installation script for iCalendar Sync skill

set -e

SKILL_NAME="icalendar-sync"
SKILL_DIR="$HOME/.openclaw/skills/$SKILL_NAME"

echo "🚀 Installing iCalendar Sync for OpenClaw..."
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
echo "✓ Python $python_version detected"

# Create skill directory
mkdir -p "$SKILL_DIR"
echo "✓ Created skill directory: $SKILL_DIR"

# Copy files
echo "📦 Copying skill files..."
cp -r src/ requirements.txt skill.yaml setup.py README.md LICENSE "$SKILL_DIR/"

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r "$SKILL_DIR/requirements.txt"

# Create CLI alias
echo "🔗 Creating CLI command..."
mkdir -p "$HOME/.local/bin"
cat > "$HOME/.local/bin/icalendar-sync" << 'EOF'
#!/bin/bash
export PYTHONPATH="$HOME/.openclaw/skills/icalendar-sync/src:$PYTHONPATH"
[ -f ~/.openclaw/.env ] && source ~/.openclaw/.env
python3 "$HOME/.openclaw/skills/icalendar-sync/src/icalendar_sync/calendar.py" "$@"
EOF
chmod +x "$HOME/.local/bin/icalendar-sync"

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "  1. Run: icalendar-sync setup"
echo "  2. Enter your iCloud credentials"
echo "  3. Test: icalendar-sync list"
echo ""