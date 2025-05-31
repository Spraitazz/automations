from skelbiu.definitions import *


def load_config(automation: WebAutomation):
    config = {}
    configfile = configparser.ConfigParser(interpolation=None)
    configfile.read(automation.config_fpath)
    config["EMAIL"] = configfile["DEFAULT"]["EMAIL"].strip().strip('"')
    config["PASS"] = configfile["DEFAULT"]["PASS"].strip().strip('"')
    config["MIN_SLEEP_S"] = float(configfile["DEFAULT"]["MIN_SLEEP_S"])
    config["MAX_SLEEP_S"] = float(configfile["DEFAULT"]["MAX_SLEEP_S"])
    automation.set_config(config)


def check_need_renew(stored_items: dict) -> bool:
    """
    Check if I need to go on site, I go if either:

    1. Any of my items have a last updated date > 25h ago
    2. Any of my items have an unknown last updated date
    """

    check_renew = False
    if len(stored_items) == 0:
        check_renew = True
    else:
        now = datetime.now()
        for item_id_str, last_updated_str in stored_items.items():
            if len(last_updated_str) < 2:
                check_renew = True
                break
            datetime_last_updated = datetime.fromisoformat(last_updated_str)
            if (now - datetime_last_updated).total_seconds() > 90000.0:
                check_renew = True
                break
    return check_renew


#
# TO DO: ideally return ItemStore, as values are not just str, but datetime in iso format
#
def load_item_store() -> dict[str, str]:
    """
    Load my item store, items for which I have a record already when each item
    was last renewed, from MY_ITEMS_STORE_FPATH, currently a json formatted dict
    defined in skelbiu.definitions
    """

    stored_items = {}
    with open(MY_ITEMS_STORE_FPATH, "r", encoding="utf-8") as f:
        try:
            stored_items = json.load(f)
        except:
            # no items stored yet
            pass
    return stored_items


def update_item_store(automation: WebAutomation, stored_items: dict, result: dict):
    """
    Update my items based on return result of calling renew_ads(), passed as
    result arg, as well as my stored_items loaded in run.py
    """

    stored_items_cur = {}
    for item_id, status_dict in result.items():
        if status_dict["status"] == "renewed":
            stored_items_cur[item_id] = status_dict["last_renewed"]
            automation.logger.debug(
                f"updating item {item_id} renewed last: {status_dict['last_renewed']}"
            )
        else:
            # was already renewed
            if item_id in stored_items:
                stored_items_cur[item_id] = stored_items[item_id]
            else:
                stored_items_cur[item_id] = "-"

    automation.logger.debug(
        f"will write stored_items_cur: {stored_items_cur} to {MY_ITEMS_STORE_FPATH}"
    )
    with open(MY_ITEMS_STORE_FPATH, "w", encoding="utf-8") as f:
        json.dump(stored_items_cur, f)
