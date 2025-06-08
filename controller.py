import socket

from definitions import *
from utils import init_default_logger
from web_automation import WebAutomation

from skelbiu.automation import SkelbiuAutomation

#
# See example config file provided in configs/skelbiu_example.ini
# you might have the # character in your password, in which case in the
# config.ini file you can escape it like so:
# PASS = "3MYFi4^nMs#X2Z"
# and when loading the config make sure to strip the "",
# config = configparser.ConfigParser(interpolation=None)
# PASS = config['DEFAULT']['PASS'].strip('"')
#

SOCKET_PATH = os.environ.get("AUTOMATIONS_SOCKET_PATH", None)
if SOCKET_PATH is None:
    print(
        "AUTOMATIONS_SOCKET_PATH environment variable was not set by systemd.service,\
 did you forget to source ~/.bashrc after running ./setup.sh?"
    )
    exit(0)

logger, _ = init_default_logger("controller")
automations_running = {}
xvfb_display_counter = 30

#
# Define your automations below
#
skelbiu_automation = {
    "class": SkelbiuAutomation,
    "config_fpath": Path.home() / "automation_configs" / "skelbiu" / "config.ini",
    "own_xvfb_display": True,
    "run_on_startup": False,
}

AUTOMATIONS = {
    "skelbiu": skelbiu_automation    
}


def respond_and_log(msg: str, conn: socket.socket):
    logger.debug(f"[controller response]: {msg}")
    conn.sendall(f"{msg}\n".encode())


def init_automation(automation_name: str, config_fpath: str) -> WebAutomation:
    """Initialise the automation instance, returning a reference to the instance."""

    global xvfb_display_counter

    if not os.path.exists(config_fpath):
        logger.warning(f"config file {config_fpath} not found")
        return None

    xvfb_display = -1
    own_xvfb_display = AUTOMATIONS[automation_name].get("own_xvfb_display", False)
    if own_xvfb_display:
        xvfb_display = xvfb_display_counter
        xvfb_display_counter = xvfb_display_counter + 1
    automation = AUTOMATIONS[automation_name]["class"](
        config_fpath=config_fpath,
        own_xvfb_display=own_xvfb_display,
        xvfb_display=xvfb_display,
    )
    return automation


def start_automation(automation_name: str, conn: socket.socket, config_fpath: str = ""):
    """Controller calls this high-level function to start a given automation."""

    if automation_name not in AUTOMATIONS:
        conn.sendall(
            f"{automation_name} not specified in AUTOMATIONS at the top of this file\n".encode()
        )
        return

    if automation_name in automations_running:
        conn.sendall(f"{automation_name} is already running, stop it first\n".encode())
        return

    if len(config_fpath) == 0 and "config_fpath" not in AUTOMATIONS[automation_name]:
        conn.sendall(
            f"config_fpath not specified for {automation_name} in AUTOMATIONS at the top of this file\n".encode()
        )
        return

    if len(config_fpath) == 0:
        config_fpath = AUTOMATIONS[automation_name]["config_fpath"]

    automation = init_automation(automation_name, config_fpath)
    if automation is not None:
        automation.start(logger)
        automations_running[automation_name] = automation

        response = (
            f"Started {automation_name} with config file {config_fpath} and "
            f"log directory {automation.logs_folder_path}\n"
        )
        conn.sendall(response.encode())
    else:
        conn.sendall(
            f"{automation_name} could not start, check controller logs\n".encode()
        )


def stop_automation(automation_name: str, conn: socket.socket):
    """Wait for automation to exit gracefully and clean up."""

    if not automation_name in automations_running:
        respond_and_log(f"{automation_name} is not running", conn)
        return

    #
    # TODO: set max wait time and kill everything if automation cant exit before that
    # TODO: this actually doesn't work as socket is closed before conn.sendall
    #
    def wait_for_stopped(automation_name: str):
        automation = automations_running[automation_name]
        while not automation.stopped_event.is_set():
            time.sleep(0.1)
        del automation
        del automations_running[automation_name]

    automations_running[automation_name].stop_event.set()

    threading.Thread(
        target=wait_for_stopped,
        args=(automation_name,),
        daemon=True,
    ).start()

    respond_and_log(
        f"stop command issued for automation [{automation_name}], exiting gracefully",
        conn,
    )


def handle_client(conn: socket.socket):
    """Act on admissible messages received from the socket client.
    The admissible messages are one of the following:

    automations list
    automations start {automation_name}
    automations stop {automation_name}
    """

    global llm_server_on

    with conn:

        data = conn.recv(1024).decode().strip()
        logger.debug(f"[controller received]: {data}")
        commands = data.split(" ")

        if len(commands) == 1:

            if commands[0] == "list":
                message = ["automations currently running:\n"]
                message += [f"{name}\n" for name in automations_running.keys()]
                message += ["\nautomations defined in controller.py:\n"]
                message += [f"{name}\n" for name in AUTOMATIONS.keys()]
                conn.sendall("".join(message).encode())
                return
            else:
                conn.sendall(f'Command "{data}" is not admissible\n'.encode())
                return

        elif len(commands) == 2:           

            if commands[0] == "stop":
                automation_name = commands[1]
                stop_automation(automation_name, conn)

            elif commands[0] == "start":
                automation_name = commands[1]
                start_automation(automation_name, conn)

            else:
                conn.sendall(f'Command "{data}" is not admissible\n'.encode())

        else:
            conn.sendall(f'Command "{data}" is not admissible\n'.encode())


def run_server():
    """Start automations with run_on_startup=True and listen to messages
    sent by socket client, responding on receiving."""

    logger.info("automations controller starting")

    logger.debug("starting automations with run_on_startup=True")
    for name, cfg in AUTOMATIONS.items():
        if cfg["run_on_startup"]:
            if "config_fpath" not in cfg:
                logger.warning(
                    f"config_fpath not specified for {name} in AUTOMATIONS at the top of this file"
                )
                continue
            automation = init_automation(name, cfg["config_fpath"])
            if automation is not None:
                automation.start(logger)
                automations_running[name] = automation
                logger.debug(f"{name} started on startup")
            else:
                logger.debug(
                    f"{name} could not start on startup, check controller logs"
                )

    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(SOCKET_PATH)
        server.listen(1)
        print(f"[controller] Listening on {SOCKET_PATH}", flush=True)
        while True:
            conn, _ = server.accept()
            threading.Thread(target=handle_client, args=(conn,), daemon=True).start()


if __name__ == "__main__":
    run_server()
