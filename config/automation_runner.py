import configparser
from pathlib import Path

XVFB_DISPLAY_WIDTH = 2560
XVFB_DISPLAY_HEIGHT = 1600

# Example config file can be found in
# examples/automation_runner.ini
CONFIG_PATH = Path.home() / "automation_configs" / "automation_runner" / "config.ini"
config_file = configparser.ConfigParser(interpolation=None)
config_file.read(CONFIG_PATH)
default_config = config_file["DEFAULT"]

APP_EMAIL = default_config["APP_EMAIL"].strip()
GMAIL_APP_PASS = default_config["GMAIL_APP_PASS"].strip()
UNHANDLED_EXCEPTION_EMAIL = default_config["UNHANDLED_EXCEPTION_EMAIL"].strip()
