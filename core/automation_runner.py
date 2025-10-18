import logging
import os
import smtplib
import threading
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from xvfbwrapper import Xvfb

from core.automation import Automation
from config.automation_runner import (
    XVFB_DISPLAY_WIDTH,
    XVFB_DISPLAY_HEIGHT,
    APP_EMAIL,
    UNHANDLED_EXCEPTION_EMAIL,
    GMAIL_APP_PASS,
)
from core.utils import init_default_logger


SMTP_HOST_GMAIL = "smtp.gmail.com"
SMTP_PORT_GMAIL = 465


class AutomationRunner:
    """
    Controls a single Automation, possibly running in an X virtual framebuffer.

    On unhandled exception in the Automation's run(), re-starts and sends
    an email notification.
    """

    DEFAULT_EXCEPTION_RESTART_TIME_S = 60.0

    logger: logging.Logger
    stop_event: threading.Event
    stopped_event: threading.Event

    def __init__(
        self,
        automation: Automation,
        in_xvfb_display: bool = False,
        xvfb_display_id: int = -1,
    ):
        self.automation = automation
        self.in_xvfb_display = in_xvfb_display
        self.xvfb_display_id = xvfb_display_id

        logger, logs_folder_path = init_default_logger(f"{self.automation.name}")
        self.logger = logger

        if self.in_xvfb_display:
            display_env = os.environ.get("DISPLAY", None)

            if display_env is None:
                raise Exception(
                    "Cannot start in xvfb display without DISPLAY "
                    "environment variable being set"
                )
            else:
                self.logger.debug(f"DISPLAY: {display_env}")

        self.stop_event = threading.Event()
        self.stopped_event = threading.Event()

    def start(self):
        """
        Start the exception handling loop in a daemon thread.
        """
        threading.Thread(
            target=self.exception_handling_loop,
            daemon=True,
        ).start()

        self.logger.info("Exception handling loop started")

    def exception_handling_loop(self):
        """
        Start and run automation (until stopped by controller), possibly in xvfb
        display, then cleanup. Handle exception handling.
        """

        def run_automation_loop():
            self.automation.setup(self.logger)

            while not self.stop_event.is_set():
                self.automation.run()

        try:
            if self.in_xvfb_display:
                with Xvfb(
                    display=self.xvfb_display_id,
                    width=XVFB_DISPLAY_WIDTH,
                    height=XVFB_DISPLAY_HEIGHT,
                ):
                    run_automation_loop()
            else:
                run_automation_loop()
            # Returned by self.stop_event being set(), clean up
            self.cleanup()
        except Exception:
            self.logger.exception("")
            self.on_exception()

    def on_exception(self):
        """
        Cleanup automation, send exception email, wait 1 minute, then re-start.
        """
        self.automation.on_exception()
        self.automation.cleanup()

        self.logger.debug(
            f"sending unhandled exception email and restarting "
            f"{self.automation.name} in {self.DEFAULT_EXCEPTION_RESTART_TIME_S} s"
        )

        try:
            self.send_unhandled_exception_email()
        except Exception:
            # TODO: if internet issue, then retry, otherwise no hope
            self.logger.exception(
                f"could not send unhandled exception email for {self.automation.name}"
            )

        time.sleep(self.DEFAULT_EXCEPTION_RESTART_TIME_S)
        self.start()

    def send_unhandled_exception_email(self):
        """
        This is general to all automations, but each descendent class can
        implement its own prep_unhandled_exception_email() function.
        """
        from_email = APP_EMAIL
        to_email = UNHANDLED_EXCEPTION_EMAIL
        msg = MIMEMultipart()
        msg["From"] = from_email
        msg["To"] = to_email
        msg["Subject"] = f"{self.automation.name} unhandled exception"
        body = self.prep_unhandled_exception_email_body()
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP_SSL(SMTP_HOST_GMAIL, SMTP_PORT_GMAIL) as server:
            server.login(APP_EMAIL, GMAIL_APP_PASS)
            server.sendmail(from_email, to_email, msg.as_string())

    def prep_unhandled_exception_email_body(self):
        """
        Override this to customize exception email content.
        """
        return f"""Automation name: {self.automation.name}. Look at logs
    (is the default unhandled exception email body
    defined in automation_runner, so if it is not informative enough, you have to
    implement prep_unhandled_exception_email(self, ) in your own class)."""

    def stop(self):
        """
        Order important here, as setting automation stop event will
        return from run() in self._run_and_cleanup(), and the automation
        runner's stop event must be set before that to exit the loop.

        Cleanup() will be called by the thread which is watching
        self.stop_event (started in self.start())
        """
        self.logger.debug("Stopping")
        self.stop_event.set()
        self.automation.stop_event.set()

    def cleanup(self):
        """
        Tell my automation to cleanup and kill my logger.
        """
        self.logger.debug("Cleaning up")
        self.automation.cleanup()
        self.cleanup_logger()
        self.stopped_event.set()

    def cleanup_logger(self):
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
            handler.close()

        self.logger = None
