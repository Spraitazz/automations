
SCRIPT_DIR=$(dirname "$(realpath "$0")")

sudo systemctl stop automations.service
sudo systemctl disable automations.service
sudo rm -f /etc/systemd/system/automations.service 

#delete pycache
echo "Found the following __pycache__ directories:"
echo
find . -type d -name '__pycache__'
echo
echo "Removing them"
find . -type d -name '__pycache__' -exec rm -rf {} +
echo "Done."

rm -f ~/.local/bin/automations

#remove this line from bashrc and source again
sed -i '/^export PATH="\$HOME\/.local\/bin:\$PATH"$/d' ~/.bashrc

# Read each line in env.sh
#while IFS= read -r line; do
#    # Remove lines in .bashrc that match "export $line"
#    sed -i "/^export $line$/d" ~/.bashrc
#done < $SCRIPT_DIR/env.sh

#while IFS= read -r line; do
#    sed -i "\#^export $line\$#d" ~/.bashrc
#done < "$SCRIPT_DIR/env.sh"

while IFS= read -r line; do
    eval "expanded_line=$line"
    sed -i "\#^export $expanded_line\$#d" ~/.bashrc
done < "$SCRIPT_DIR/env.sh"


source ~/.bashrc
