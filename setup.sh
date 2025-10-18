#!/usr/bin/env bash

SERVICE_NAME="automations"
VENV_DIR=".venv"

SCRIPT_DIR=$(dirname "$(realpath "$0")")

AUTOMATIONS_SERVICE_SCRIPT="core.service"
ENV_FILE="$SCRIPT_DIR/env.sh"
COMMUNICATION_CLIENT_BINARY="$SCRIPT_DIR/bin/communication_client"

SYSTEMD_USER_SERVICE_PATH="$HOME/.config/systemd/user"
SYSTEMD_SERVICE_FILE="$SYSTEMD_USER_SERVICE_PATH/$SERVICE_NAME.service"
SYSTEMD_ENV_FILE="$SYSTEMD_USER_SERVICE_PATH/$SERVICE_NAME.env"

# Check if service file already exists
if [ -f "$SYSTEMD_SERVICE_FILE" ]; then
  echo "Service file ($SYSTEMD_SERVICE_FILE) already exists."
  echo "Please run ./cleanup.sh before re-running this script."
  exit 1
fi

# Check uv installation
if ! command -v uv &>/dev/null; then
  echo "Error: uv not found. Please install it first:"
  echo "  pip install uv"
  exit 1
fi

# Ensure virtual environment exists
if [ ! -d "$SCRIPT_DIR/$VENV_DIR" ]; then
  echo "Creating virtual environment with uv..."
  cd "$SCRIPT_DIR" || exit 1
  uv venv "$VENV_DIR"
  echo "Syncing dependencies..."
  uv sync
else
  echo "Existing virtual environment detected at $SCRIPT_DIR/$VENV_DIR"
fi

# Add communication (sockets) client binary to local binaries
mkdir -p ~/.local/bin
chmod +x "$COMMUNICATION_CLIENT_BINARY"
cp "$COMMUNICATION_CLIENT_BINARY" ~/.local/bin/automations

# Make sure local binaries directory is in PATH (append to .bashrc if missing)
TMP='export PATH="$HOME/.local/bin:$PATH"'
grep -qxF "$TMP" ~/.bashrc || echo "$TMP" >> ~/.bashrc

# For communication client, need the socket path env var for the user too
# Read each line in env.sh and append it to .bashrc (evaluating expressions)
while IFS= read -r line; do
    eval "echo export $line" >> ~/.bashrc
done < "$SCRIPT_DIR/env.sh"

source ~/.bashrc

# Expand variables in env.sh and output to SYSTEMD_ENV_FILE
mkdir -p "$(dirname "$SYSTEMD_ENV_FILE")"
envsubst < "$ENV_FILE" > "$SYSTEMD_ENV_FILE"

# Output systemd service file
if [ ! -f "$SYSTEMD_SERVICE_FILE" ]; then
  cat <<EOF | tee "$SYSTEMD_SERVICE_FILE"
[Unit]
Description=automations controller
After=network-online.target
Wants=network-online.target

[Service]
Restart=on-failure
Type=simple
RuntimeDirectory=$SERVICE_NAME
RuntimeDirectoryMode=0755
EnvironmentFile=$SYSTEMD_ENV_FILE
ExecStart=$SCRIPT_DIR/$VENV_DIR/bin/python3 -m $AUTOMATIONS_SERVICE_SCRIPT
WorkingDirectory=$SCRIPT_DIR

[Install]
WantedBy=default.target
EOF
  echo "Service file ($SYSTEMD_SERVICE_FILE) created."
else
  echo "Service file ($SYSTEMD_SERVICE_FILE) already exists. Skipping creation."
fi

# Reload systemd and enable the service
systemctl --user daemon-reload
systemctl --user enable "$SERVICE_NAME.service"
systemctl --user start "$SERVICE_NAME.service"

echo
echo "automations service has been created, enabled, and started."
echo "Please run 'source ~/.bashrc' or restart your terminal to apply PATH changes."