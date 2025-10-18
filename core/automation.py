import logging
import threading
import time
from abc import ABC, abstractmethod
from pathlib import Path


def interruptable_sleep(stop_event: threading.Event, timeout: float):
    """
    Not the ideal kind of sleep.
    """
    start_time = time.time()

    while not stop_event.is_set():
        if time.time() - start_time >= timeout:
            break
        time.sleep(0.1)


class Automation(ABC):
    """
    Interface for automation implementations. Controlled by
    AutomationRunner.
    """

    def __init__(self, name: str, config_path: Path):
        self.name = name
        self.config_path = config_path

        self.stop_event = threading.Event()
        self.sleep = lambda timeout: interruptable_sleep(self.stop_event, timeout)

    @abstractmethod
    def setup(self, logger: logging.Logger):
        """
        The AutomationRunner instance owning this Automation sets it up,
        passing in the logger.

        Anything that needs to be done after initialising the Automation
        instance but before run() is called.
        """

    @abstractmethod
    def run(self):
        """
        Implement your automation logic here. This function is to called
        in a while loop by AutomationRunner.
        """
        pass

    @abstractmethod
    def on_exception(self):
        """
        Anything that needs to be done when an exception occurs in run().
        """
        pass

    @abstractmethod
    def cleanup(self):
        """
        Clean up after your automation here.
        """
        pass
