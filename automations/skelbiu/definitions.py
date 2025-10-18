from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

CONFIG_PATH = Path.home() / "automation_configs" / "skelbiu" / "config.ini"

BASE_URL = "https://www.skelbiu.lt"
LOGIN_URL = "https://www.skelbiu.lt/users/signin"
MY_ADS_URL = "https://www.skelbiu.lt/mano-skelbimai/"

MY_ITEMS_STORE_FPATH = BASE_DIR / "my_items.json"
