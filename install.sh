#!/usr/bin/env bash
# instagram-cli Installation Script

# Exit immediately if a command exits with a non-zero status
set -e

# Configuration
APP_NAME="insta-cli"
SRC_DIR="src"
REQ_FILE="requirements.txt"

# Default installation mode: user-level (no sudo required)
INSTALL_MODE="user"
INSTALL_DIR="$HOME/.local/share/instagram-cli"
BIN_DIR="$HOME/.local/bin"

# Help message
show_help() {
    echo "Usage: ./install.sh [options]"
    echo ""
    echo "Options:"
    echo "  --system    Install system-wide (requires sudo; installs to /usr/local)"
    echo "  --user      Install for current user only (default; installs to ~/.local)"
    echo "  --help      Show this help message"
    echo ""
}

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --system)
            INSTALL_MODE="system"
            INSTALL_DIR="/usr/local/share/instagram-cli"
            BIN_DIR="/usr/local/bin"
            shift
            ;;
        --user)
            INSTALL_MODE="user"
            INSTALL_DIR="$HOME/.local/share/instagram-cli"
            BIN_DIR="$HOME/.local/bin"
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown argument: $1"
            show_help
            exit 1
            ;;
    esac
done

echo "=================================================="
echo "Installing instagram-cli ($INSTALL_MODE mode)..."
echo "=================================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if python3-venv is installed (on Debian/Ubuntu systems)
if ! python3 -c "import venv" &> /dev/null; then
    echo "Error: python3-venv package is missing."
    if command -v apt-get &> /dev/null; then
        echo "Please install it by running: sudo apt-get install python3-venv"
    else
        echo "Please install Python virtual environment support for your OS."
    fi
    exit 1
fi

# Ensure target directories exist
echo "Creating installation directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"

# Copy source files
echo "Copying source code to $INSTALL_DIR..."
# Clean copy: delete old src if exists in target dir
if [ -d "$INSTALL_DIR/$SRC_DIR" ]; then
    rm -rf "$INSTALL_DIR/$SRC_DIR"
fi
cp -r "$SRC_DIR" "$INSTALL_DIR/"
cp "$REQ_FILE" "$INSTALL_DIR/"

# Copy optional ascii.txt if it exists
if [ -f "ascii.txt" ]; then
    cp "ascii.txt" "$INSTALL_DIR/"
fi

# Create virtual environment
echo "Setting up Python virtual environment..."
python3 -m venv "$INSTALL_DIR/venv"

# Install dependencies inside virtual environment
echo "Installing dependencies..."
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

# Create the wrapper runner script
echo "Creating command launcher at $BIN_DIR/$APP_NAME..."
cat << 'LAUNCHER' > "$BIN_DIR/$APP_NAME"
#!/usr/bin/env bash
# Wrapper command for instagram-cli
export PYTHONPATH="INSTALL_DIR_PLACEHOLDER"
exec "INSTALL_DIR_PLACEHOLDER/venv/bin/python3" -m src.cli "$@"
LAUNCHER

# Replace placeholder with actual path
# Using different delimiter to handle slashes in path
sed -i "s|INSTALL_DIR_PLACEHOLDER|$INSTALL_DIR|g" "$BIN_DIR/$APP_NAME"

# Make wrapper script executable
chmod +x "$BIN_DIR/$APP_NAME"

echo "=================================================="
echo "Installation complete!"
echo "=================================================="
echo "You can now run the program by typing: $APP_NAME"
echo ""

# Check if the bin directory is in user's PATH
if [[ "$INSTALL_MODE" == "user" ]]; then
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        echo "⚠️  WARNING: $BIN_DIR is not in your system PATH."
        echo "To run '$APP_NAME' from anywhere, add this line to your ~/.bashrc or ~/.zshrc file:"
        echo "  export PATH=\"\$PATH:$BIN_DIR\""
        echo "Then reload the shell: source ~/.bashrc"
    fi
fi
