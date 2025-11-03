import threading
import time
from queue import Queue

from core.automation_runner import AutomationRunner
from config.controller import CONFIG_PATH, AUTOMATIONS
from core.utils import init_default_logger


class Controller:
    """
    The automations controller controls multiple AutomationRunner
    instances, one per unique automation.
    """

    def __init__(self):
        logger, logs_dir = init_default_logger("controller")
        logger.info("automations controller started")
        self.logger = logger

        self.message_queue = Queue()

        self.xvfb_display_counter_lock = threading.Lock()
        self.xvfb_display_counter = 30
        self.automation_runners = {}

    def get_automations_info(self) -> str:
        """Get information about running and defined automations."""
        message = ["\nautomations currently running:\n"]
        message += ["------------------------------------------------------\n"]
        message += [f"{name}\n" for name in self.automation_runners.keys()]
        message += ["------------------------------------------------------\n"]
        message += [f"automations defined in {CONFIG_PATH}:\n"]
        message += ["------------------------------------------------------\n"]
        message += [f"{name}\n" for name in AUTOMATIONS.keys()]
        message += ["------------------------------------------------------\n\n"]
        info = "".join(message)
        return info

    def start_automations_on_startup(self):
        """
        Start all automations configured with run_on_startup=True.
        """
        self.logger.debug("starting automations with run_on_startup=True")

        for name, cfg in AUTOMATIONS.items():
            if cfg.get("run_on_startup", False):
                self.start_automation(name)

    def start_automation(self, automation_name: str) -> str:
        """
        Checks if the automation by that name is not yet running, if it
        is defined correctly in the config - has at least the keys "class"
        and "config_path".

        Initialises the automation instance for the class specified in the
        config for automation_name in CONFIG_PATH.

        Initialises and starts the automation runner for this automation.

        Returns a response message indicating success or failure.
        """

        if automation_name in self.automation_runners:
            return f"{automation_name} is already running, stop it first\n"

        if automation_name not in AUTOMATIONS:
            return f"{automation_name} not specified in AUTOMATIONS at {CONFIG_PATH}\n"

        if "config_path" not in AUTOMATIONS[automation_name]:
            return (
                f"config_path not specified for {automation_name} "
                f"in AUTOMATIONS at {CONFIG_PATH}\n"
            )

        config_path = AUTOMATIONS[automation_name]["config_path"]

        xvfb_display_id = -1
        in_xvfb_display = AUTOMATIONS[automation_name].get("in_xvfb_display", False)

        if in_xvfb_display:
            with self.xvfb_display_counter_lock:
                xvfb_display_id = self.xvfb_display_counter
                self.xvfb_display_counter = self.xvfb_display_counter + 1

        automation = AUTOMATIONS[automation_name]["class"](
            config_path=config_path,
        )

        automation_runner = AutomationRunner(
            automation, in_xvfb_display=in_xvfb_display, xvfb_display_id=xvfb_display_id
        )
        automation_runner.start()
        self.automation_runners[automation_name] = automation_runner

        return f"Started {automation_name} with config path: {config_path}\n"

    def stop_automation(self, automation_name: str) -> str:
        """
        Wait for automation to exit gracefully and clean up.
        """
        if automation_name not in self.automation_runners:
            return f"{automation_name} is not running\n"

        # TODO: need to create a message queue to notify through socket
        # when the automation has gracefully exited
        def wait_for_stopped():
            automation_runner = self.automation_runners[automation_name]

            while not automation_runner.stopped_event.is_set():
                time.sleep(0.1)

            del self.automation_runners[automation_name]
            del automation_runner

            # Notify the communication server through the shared queue
            msg = f"Automation [{automation_name}] stopped gracefully\n"
            self.message_queue.put(msg)

        self.automation_runners[automation_name].stop()

        threading.Thread(
            target=wait_for_stopped,
            args=(),
            daemon=True,
        ).start()

        return (
            f"stop command issued for automation [{automation_name}], exiting "
            f"gracefully\n"
        )
