#!/bin/bash
set -e

# ============================================================
# Vido Deploy Script
# 1. Install toolchain (nvm + Node.js, pnpm, uv, yt-dlp)
# 2. Clone repository from GitHub 
# 3. Install dependencies & build frontend
# 4. Start backend server
# ============================================================

# --- Configuration ---
REPO_URL="https://github.com/Accelerating/Vido.git"   
APP_DIR="$HOME/vido"
PORT="${PORT:-8000}"

echo "=== Vido Deploy ==="
echo ""

# --- nvm + Node.js ---
echo "--- Installing nvm + Node.js ---"
export NVM_DIR="$HOME/.nvm"
if [ -s "$NVM_DIR/nvm.sh" ]; then
    echo "nvm already installed"
    \. "$NVM_DIR/nvm.sh"
else
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.4/install.sh | bash
    \. "$NVM_DIR/nvm.sh"
fi

if command -v node &>/dev/null; then
    echo "Node.js already installed: $(node --version)"
else
    nvm install 24
fi
echo "Node.js: $(node --version)"

# --- pnpm ---
echo ""
echo "--- Enabling pnpm ---"
corepack enable pnpm
echo "pnpm: $(pnpm --version)"

# --- uv ---
echo ""
echo "--- Installing uv ---"
if command -v uv &>/dev/null; then
    echo "uv already installed: $(uv --version)"
else
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    if ! grep -q '.local/bin' ~/.bashrc 2>/dev/null; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    fi
    echo "uv installed: $(uv --version)"
fi

# --- ffmpeg ---
echo ""
echo "--- Installing ffmpeg ---"
if command -v ffmpeg &>/dev/null; then
    echo "ffmpeg already installed: $(ffmpeg -version 2>&1 | head -1)"
elif command -v brew &>/dev/null; then
    brew install ffmpeg
elif command -v apt-get &>/dev/null; then
    sudo apt-get update -qq && sudo apt-get install -y -qq ffmpeg
else
    echo "WARNING: ffmpeg not found and no supported package manager detected."
    echo "Please install ffmpeg manually: https://ffmpeg.org/download.html"
fi

# --- yt-dlp ---
echo ""
echo "--- Installing yt-dlp ---"
uv tool install yt-dlp 2>/dev/null || {
    echo "yt-dlp already installed via uv tool, upgrading..."
    uv tool upgrade yt-dlp 2>/dev/null || true
}
echo "yt-dlp: $(~/.local/bin/yt-dlp --version 2>/dev/null || uvx yt-dlp --version)"

# --- Clone repo ---
echo ""
echo "--- Cloning repository ---"
if [ -d "$APP_DIR" ]; then
    echo "$APP_DIR already exists, pulling latest..."
    cd "$APP_DIR"
    git pull
else
    git clone "$REPO_URL" "$APP_DIR"
    cd "$APP_DIR"
fi

# --- Frontend ---
echo ""
echo "--- Installing frontend dependencies ---"
cd "$APP_DIR/frontend"
pnpm install

echo ""
echo "--- Building frontend ---"
pnpm build

# --- Backend ---
echo ""
echo "--- Installing backend dependencies ---"
cd "$APP_DIR/backend"
uv sync

# --- Run ---
echo ""
echo "=== Starting Vido on 0.0.0.0:$PORT ==="

LOG_FILE="$APP_DIR/backend/vido.log"
PID_FILE="$APP_DIR/backend/vido.pid"

# Kill previous instance if running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "Stopping previous instance (PID $OLD_PID)..."
        kill "$OLD_PID"
        sleep 2
    fi
fi

cd "$APP_DIR/backend"
nohup uv run uvicorn app.main:app --host 0.0.0.0 --port "$PORT" > "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"

echo "Vido started (PID $(cat $PID_FILE))"
echo "  Logs:  tail -f $LOG_FILE"
echo "  Stop:  kill $(cat $PID_FILE)"
