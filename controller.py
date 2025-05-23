import socket

from definitions import *
from utils import init_default_logger
from automation import Automation, WebAutomation

from llm_server.controller import start as start_llm_server
from llm_server.controller import stop as stop_llm_server
from llm_server.definitions import LLM_SERVER_BASE_URL

from skelbiu.run import run as run_skelbiu
from spires.run import run as run_spires
#
# IMPORTANT: see example config file provided in configs/skelbiu_example.ini
# you might have the # character in your password, in which case in the
# config.ini file you can escape it like so:
# PASS = "3MYFi4^nMs#X2Z"
# and when loading the config make sure to strip the "",
# config = configparser.ConfigParser(interpolation=None)
# PASS = config['DEFAULT']['PASS'].strip('"')
#
skelbiu_automation = {
    "class": WebAutomation,
    "run_func": run_skelbiu,
    "config_fpath": Path.home() / "automation_configs" / "skelbiu" / "config.ini",
    "with_xvfb": True,
    "run_on_startup": False,
}

spires_automation = {
    "class": WebAutomation,
    "run_func": run_spires,
    "config_fpath": Path.home() / "automation_configs" / "spires" / "config.ini",
    "with_xvfb": True,
    "run_on_startup": False,
}

AUTOMATIONS = {"skelbiu": skelbiu_automation, "spires": spires_automation}

logger, logs_folder_path = init_default_logger("controller")

automations_running = {}
xvfb_display_counter = 30

llm_server_on = False


# wait for the automation to "exit gracefully"
#
# TO DO: set max wait time,
#        and kill everything if automation cant exit before that
#
# TO DO 2: this actually doesn't work as socket is closed before conn.sendall
#          so after setting max wait time, this becomes what closes socket?
#          BUT: i don't want this to hold until that -> ??????????????
#
def wait_for_stopped(automation_name: str, conn: socket.socket, logger: logging.Logger):
    automation = automations_running[automation_name]
    while not automation.stopped_event.is_set():
        time.sleep(0.1)
    del automation
    del automations_running[automation_name]
    try:
        conn.sendall(f"automation [{automation_name}] exited gracefully\n".encode())
    except:
        logger.exception("")


#
# used to start automations with run_on_startup=True and by controller when starting
# from command, in controller_start_automation()
#
def start_automation(automation_name: str, config_fpath: str):

    global xvfb_display_counter

    if not os.path.exists(config_fpath):
        logger.warning(f"config file {config_fpath} not found")
        return None

    automation = None
    if AUTOMATIONS[automation_name]["class"] == WebAutomation:
        xvfb_display = -1
        with_xvfb = AUTOMATIONS[automation_name].get("with_xvfb", False)
        if with_xvfb:
            xvfb_display = xvfb_display_counter
            xvfb_display_counter = xvfb_display_counter + 1
        automation = AUTOMATIONS[automation_name]["class"](
            name=automation_name,
            run_func=AUTOMATIONS[automation_name]["run_func"],
            config_fpath=config_fpath,
            with_xvfb=with_xvfb,
            xvfb_display=xvfb_display,
        )
    elif AUTOMATIONS[automation_name]["class"] == Automation:
        automation = AUTOMATIONS[automation_name]["class"](
            name=automation_name,
            run_func=AUTOMATIONS[automation_name]["run_func"],
            config_fpath=config_fpath,
        )

    automation.start(logger)
    automations_running[automation_name] = automation
    return automation


def controller_start_automation(
    automation_name: str, conn: socket.socket, config_fpath: str = ""
):

    if automation_name not in AUTOMATIONS:
        conn.sendall(
            f"{automation_name} not specified in AUTOMATIONS at the top of this file\n".encode()
        )
        return

    if len(config_fpath) == 0 and "config_fpath" not in AUTOMATIONS[automation_name]:
        conn.sendall(
            f"config_fpath not specified for {automation_name} in AUTOMATIONS at the top of this file\n".encode()
        )
        return

    if automation_name in automations_running:
        conn.sendall(f"{automation_name} is already running, stop it first\n".encode())
        return

    if len(config_fpath) == 0:
        config_fpath = AUTOMATIONS[automation_name]["config_fpath"]

    automation = start_automation(automation_name, config_fpath)
    if automation is not None:
        conn.sendall(
            f"Started {automation_name} with config file {config_fpath} and log directory {automation.logs_folder_path}\n".encode()
        )
    else:
        conn.sendall(
            f"{automation_name} could not start, check controller logs\n".encode()
        )


def respond_and_log(msg: str, conn: socket.socket): 
    logger.debug(f"[controller response]: {msg}")
    conn.sendall(f"{msg}\n".encode())


def handle_client(conn: socket.socket):

    global llm_server_on

    with conn:
        data = conn.recv(1024).decode().strip()
        print(f"[controller received]: {data}")
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

        if len(commands) == 2:

            # currently only allow "start/stop llm_server" and "status/stop bot_name"
            if commands[0] == "start" and commands[1] == "llm_server":            
                if llm_server_on:
                    logger.debug(f"llm server already running at url: {LLM_SERVER_BASE_URL}")
                    conn.sendall(f"llm server already running at url: {LLM_SERVER_BASE_URL}\n".encode())
                    return                               
                
                started_ok = start_llm_server(logger)       
                if started_ok:
                    llm_server_on = True
                    respond_and_log(f"llm server started url: {LLM_SERVER_BASE_URL}", conn)
                else:
                    logger.error("Could not start LLM server")
                    conn.sendall("LLM server did not start\n".encode())                         

            elif commands[0] == "stop" and commands[1] == "llm_server":            
                if not llm_server_on:
                    respond_and_log("llm server not running", conn)
                    return
                
                stopped_ok = stop_llm_server(logger)
                if stopped_ok:
                    llm_server_on = False
                    respond_and_log(f"llm server stopped", conn)
                else:
                    logger.error("Could not stop LLM server")
                    conn.sendall("LLM server could not be stopped\n".encode())                 
     

            elif commands[0] == "status" or commands[0] == "stop":
            
                automation_name = commands[1]
                
                if not automation_name in automations_running:
                    conn.sendall(f"{automation_name} is not running\n".encode())
                    return

                if commands[0] == "status":
                    # get automation status
                    logger.debug(f"get {automation_name} status")
                    conn.sendall(f"{automation_name} is running\n".encode())
                elif commands[0] == "stop":
                    # stop automation
                    logger.debug(f"stop {automation_name}")
                    automations_running[automation_name].stop_event.set()
                    conn.sendall(
                        f"stop command issued for automation [{automation_name}], will wait for graceful exit\n".encode()
                    )
                    threading.Thread(
                        target=wait_for_stopped,
                        args=(automation_name, conn, logger),
                        daemon=True,
                    ).start()

                else:
                    conn.sendall(f'Command "{data}" is not admissible\n'.encode())

            elif commands[0] == "start":
                # start automation_name (using its default config path if specified in automationS at the top of this file)
                automation_name = commands[1]
                controller_start_automation(automation_name, conn)

            else:
                conn.sendall(f'Command "{data}" is not admissible\n'.encode())

        elif len(commands) == 3:
            # currently only allow "start automation_name config_fname"
            if commands[0] != "start":
                conn.sendall(f'Command "{data}" is not admissible\n'.encode())
                return

            automation_name = commands[1]
            config_fpath = os.path.join(BASE_DIR, "configs", commands[2])
            controller_start_automation(
                automation_name, conn, config_fpath=config_fpath
            )

        else:
            conn.sendall(f'Command "{data}" is not admissible\n'.encode())


def run_server():

    logger.info("automations controller starting")

    logger.debug("starting automations with run_on_startup=True")
    for name, cfg in AUTOMATIONS.items():
        if cfg["run_on_startup"]:
            if "config_fpath" not in cfg:
                logger.warning(
                    f"config_fpath not specified for {name} in AUTOMATIONS at the top of this file"
                )
                continue
            res = start_automation(name, cfg["config_fpath"])
            if res:
                # started ok
                logger.debug(f"{name} started on startup")
            else:
                # not started, CHECK controller logs
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
