#!/bin/bash
# ============================================================
#  Diggy Func AWS — EC2 Setup Script
#  Run as root (or with sudo) on a fresh Ubuntu 22.04 instance
# ============================================================
set -euo pipefail

APP_DIR="/opt/diggy_func_aws"
APP_USER="diggy"
VENV_DIR="$APP_DIR/venv"
SERVICE_NAME="diggy"

echo "==> Updating system packages..."
apt-get update -y && apt-get upgrade -y

echo "==> Installing Python 3, pip, venv, and Nginx..."
apt-get install -y python3 python3-pip python3-venv nginx git

# ---------- App user ----------
if ! id "$APP_USER" &>/dev/null; then
    echo "==> Creating app user '$APP_USER'..."
    useradd --system --no-create-home --shell /bin/false "$APP_USER"
fi

# ---------- App directory ----------
echo "==> Setting up application directory at $APP_DIR..."
mkdir -p "$APP_DIR"

# Copy project files (assumes script is run from the repo root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

cp "$REPO_DIR/main.py" "$APP_DIR/"
cp "$REPO_DIR/schemas.py" "$APP_DIR/"
cp "$REPO_DIR/requirements.txt" "$APP_DIR/"
cp -r "$REPO_DIR/api" "$APP_DIR/"

# ---------- .env ----------
if [ -f "$REPO_DIR/.env" ]; then
    cp "$REPO_DIR/.env" "$APP_DIR/.env"
    echo "==> Copied .env file."
else
    echo "WARNING: No .env file found at $REPO_DIR/.env"
    echo "         Create $APP_DIR/.env with SERP_API_KEY and GROQ_API_KEY before starting the service."
fi

# ---------- Python virtual environment ----------
echo "==> Creating Python virtual environment..."
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"

# ---------- Permissions ----------
chown -R "$APP_USER":"$APP_USER" "$APP_DIR"

# ---------- systemd service ----------
echo "==> Installing systemd service..."
cp "$SCRIPT_DIR/diggy.service" /etc/systemd/system/${SERVICE_NAME}.service
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

# ---------- Nginx ----------
echo "==> Configuring Nginx..."
cp "$SCRIPT_DIR/nginx.conf" /etc/nginx/sites-available/diggy
ln -sf /etc/nginx/sites-available/diggy /etc/nginx/sites-enabled/diggy
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx
systemctl enable nginx

# ---------- Start the app ----------
echo "==> Starting Diggy service..."
systemctl start "$SERVICE_NAME"
systemctl status "$SERVICE_NAME" --no-pager

echo ""
echo "============================================"
echo "  Setup complete!"
echo "  App running at http://<your-ec2-public-ip>/summary"
echo "============================================"
