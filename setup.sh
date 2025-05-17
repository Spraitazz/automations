#
# set up user service
#
SERVICE_NAME="automations"
CONDA_ENV_NAME="web_automations"

USER=$(whoami)

SERVICE_FILE="/home/$USER/.config/systemd/user/$SERVICE_NAME.service"
SCRIPT_DIR=$(dirname "$(realpath "$0")")
COMMUNICATOR_SERVER="$SCRIPT_DIR/controller.py"

# Check conda env exists
CONDA_ENV_PATH=$(conda info --envs | awk -v env="$CONDA_ENV_NAME" '$1 == env { print $NF }')
if [ -z "$CONDA_ENV_PATH" ]; then
  echo "Error: Conda environment '$CONDA_ENV_NAME' not found."
  # If the script is being sourced, return; otherwise, exit
  (return 0 2>/dev/null) && return 1 || exit 1
fi

mkdir -p ~/.local/bin
chmod +x automations
cp automations ~/.local/bin/
TMP='export PATH="$HOME/.local/bin:$PATH"'
grep -qxF "$TMP" ~/.bashrc || echo "$TMP" >> ~/.bashrc


# Read each line in env.sh and append it to .bashrc
# evaluating expressions
while IFS= read -r line; do
    eval "echo export $line" >> ~/.bashrc
done < "$SCRIPT_DIR/env.sh"

source ~/.bashrc

# expand variables in env.sh and output to ~/.config/systemd/user/automations.env
envsubst < "$SCRIPT_DIR/env.sh" > ~/.config/systemd/user/automations.env

#
# TO DO: check if service file exists, stop here and ask user to run "./cleanup.sh"
#
# output service file
if [ ! -f "$SERVICE_FILE" ]; then
  cat <<EOF | tee "$SERVICE_FILE"
[Unit]
Description=automations controller 
After=network-online.target
Wants=network-online.target

[Service]
Restart=on-failure 
Type=simple
RuntimeDirectory=$SERVICE_NAME
RuntimeDirectoryMode=0755
EnvironmentFile=%h/.config/systemd/user/automations.env
ExecStart=$CONDA_ENV_PATH/bin/python3 $COMMUNICATOR_SERVER

[Install]
WantedBy=default.target
EOF
  echo "Service file ($SERVICE_FILE) created."
else
  echo "Service file ($SERVICE_FILE) already exists. Skipping creation."
fi

# Step 4: Reload systemd and enable the service
systemctl --user daemon-reload        
systemctl --user enable $SERVICE_NAME.service 
systemctl --user start $SERVICE_NAME.service  

echo "automations service has been created, enabled, and started."
echo "Please run 'source ~/.bashrc' or restart your terminal to apply PATH changes."



