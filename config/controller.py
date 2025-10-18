from pathlib import Path

import automations.skelbiu.definitions as skelbiu_definitions
import automations.skelbiu.automation as skelbiu_automation

CONFIG_PATH = Path(__file__).resolve()

skelbiu = {
    "class": skelbiu_automation.SkelbiuAutomation,
    "config_path": skelbiu_definitions.CONFIG_PATH,
    "in_xvfb_display": False,
    "run_on_startup": False,
}

AUTOMATIONS = {
    "skelbiu": skelbiu,
}
