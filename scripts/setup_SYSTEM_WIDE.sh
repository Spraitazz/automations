
SERVICE_NAME="automations"

CONDA_ENV_NAME="web_automations"

USER=$(whoami)

#"global" service - by default starts before login
#SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
#user service
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


#
#TO DO: move this below to env.sh and change the .bashrc added line to 'source env.sh' (add comment above?)
#
TMP='export PATH="$HOME/.local/bin:$PATH"'


mkdir -p ~/.local/bin
chmod +x automations
cp automations ~/.local/bin/
grep -qxF "$TMP" ~/.bashrc || echo "$TMP" >> ~/.bashrc

#
# Read each line in env.sh and append it to .bashrc
#
#while IFS= read -r line; do
#    echo "export $line" >> ~/.bashrc
#done < $SCRIPT_DIR/env.sh
#
while IFS= read -r line; do
    eval "echo export $line" >> ~/.bashrc
done < "$SCRIPT_DIR/env.sh"



source ~/.bashrc

#
# TO DO: check if service file exists, stop here and ask user to run "./cleanup.sh"
#
# for "global" service 
#Environment: SOCKET_PATH=/run/$SERVICE_NAME/comms.sock
# for user service:
#             SOCKET_PATH=$XDG_RUNTIME_DIR/automations/comms.sock
#
# /etc/systemd/system/automations.service
if [ ! -f "$SERVICE_FILE" ]; then
  cat <<EOF | sudo tee "$SERVICE_FILE"
[Unit]
Description=automations controller 
After=default.target

[Service]
Restart=on-failure 
Type=simple
User=$USER
Group=$USER
RuntimeDirectory=$SERVICE_NAME
RuntimeDirectoryMode=0755
EnvironmentFile=$SCRIPT_DIR/env.sh
ExecStart=$CONDA_ENV_PATH/bin/python3 $COMMUNICATOR_SERVER

[Install]
WantedBy=default.target
EOF
  echo "Service file ($SERVICE_FILE) created."
else
  echo "Service file ($SERVICE_FILE) already exists. Skipping creation."
fi

# Step 4: Reload systemd and enable the service
#sudo systemctl daemon-reload
#sudo systemctl enable $SERVICE_NAME.service
#sudo systemctl start $SERVICE_NAME.service
systemctl --user daemon-reload        # Refresh user service definitions
systemctl --user enable $SERVICE_NAME.service # Enable at user login
systemctl --user start $SERVICE_NAME.service  # Start immediately


echo "automations service has been created, enabled, and started."
echo "Please run 'source ~/.bashrc' or restart your terminal to apply PATH changes."





