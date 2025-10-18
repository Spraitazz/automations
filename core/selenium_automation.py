import logging
import os
from abc import ABC
from datetime import datetime
from pathlib import Path

from core.automation import Automation
from core.extended_chrome_driver import ExtendedChromeDriver

DEFAULT_URL = "https://google.com"


class SeleniumAutomation(Automation, ABC):
    """
    A selenium automation with a single webdriver. Logs to a logger
    with the default parameters, as defined in utils.init_default_logger().
    """

    logger: logging.Logger | None = None
    logs_folder_path: Path | None = None

    driver: ExtendedChromeDriver | None = None

    def __init__(self, name: str, base_dir: Path, config_path: Path):
        super().__init__(name, config_path)
        self.name = name
        self.base_dir = base_dir
        self.config_path = config_path

    def setup(self, logger: logging.Logger):
        """
        Initialise webdriver.
        """
        self.logger = logger
        self.driver = ExtendedChromeDriver(self.sleep, self.logger)
        self.logger.info("Automation set up")

    def on_exception(self):
        """
        Take screenshot.
        """
        self.take_screenshot("")

    def take_screenshot(self, test_name: str = "") -> Path:
        """
        Take screenshot and return its filepath.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{test_name}_{timestamp}.png"

        screenshots_dir_path = self.base_dir / "screenshots"
        os.makedirs(screenshots_dir_path, exist_ok=True)

        filepath = screenshots_dir_path / filename
        self.driver.save_screenshot(filepath)
        self.logger.debug(f"screenshot saved in {filepath}")

        return filepath

    def cleanup(self):
        """
        Cleanup my webdriver
        """
        try:
            self.driver.quit()
        except Exception:
            self.logger.exception("")
        finally:
            self.driver = None
