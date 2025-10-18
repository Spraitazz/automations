SCRIPT_DIR=$(dirname "$(realpath "$0")")
USER=$(whoami)

# stop and disable systemctl.service
systemctl --user stop automations.service
systemctl --user disable automations.service
rm -f /home/$USER/.config/systemd/user/automations.service
systemctl --user daemon-reload

# delete pycache
echo "Found the following __pycache__ directories:"
echo
find . -type d -name '__pycache__'
echo
echo "Removing them"
find . -type d -name '__pycache__' -exec rm -rf {} +
echo "Done."

rm -f ~/.local/bin/automations

# remove this line from bashrc and source again
sed -i '/^export PATH="\$HOME\/.local\/bin:\$PATH"$/d' ~/.bashrc

while IFS= read -r line; do
    eval "expanded_line=$line"
    sed -i "\#^export $expanded_line\$#d" ~/.bashrc
done < "$SCRIPT_DIR/env.sh"

rm -f ~/.config/systemd/user/automations.env

source ~/.bashrc
