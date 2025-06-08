# import signal
from abc import ABC, abstractmethod
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from definitions import *
from utils import init_default_logger


def interruptable_sleep(event: threading.Event, timeout: float, logger: logging.Logger):
    """Not the ideal kind of sleep."""

    start_time = time.time()
    while not event.is_set():
        if time.time() - start_time >= timeout:
            break
        time.sleep(0.1)
    else:
        logger.debug("stopped by controller")


class Automation(ABC):
    """
    Wrapper for a persistent automation which handles starting,
    stopping, as well as re-starting and sending an email notification
    on catching an unhandled exception.
    """

    logger: typing.Optional[logging.Logger] = None
    stop_event: typing.Optional[threading.Event] = (
        None  # this is to be set by controller to stop automation
    )
    stopped_event: typing.Optional[threading.Event] = (
        None  # this is to be set by automation when its done
    )
    sleep: typing.Optional[typing.Callable] = lambda timeout: time.sleep(timeout)

    def __init__(self, name: str, config_fpath: str):
        self.name = name
        # self.run_func = run_func
        self.config_fpath = config_fpath

        logger, logs_folder_path = init_default_logger(self.name)
        self.logs_folder_path = logs_folder_path
        self.logger = logger

    #
    # TODO: delete this
    #
    def set_config(self, config: dict):
        self.config = config

    #
    # TODO: add @abstractmethod and inside just pass - WHAT HAPPENS IN Webautomation then?
    #
    @abstractmethod
    def run(self):
        pass

    #
    # TODO: check for case when self.logger is None/not a logging.Logger
    #
    def cleanup(self, controller_logger: logging.Logger):
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
            handler.close()
        self.stopped_event.set()
        controller_logger.debug(f"{self.name} cleaned up and stopped event set")

    def _run_and_cleanup(self, controller_logger: logging.Logger):
        self.run()
        controller_logger.debug(f"{self.name} stopped by return from run func")
        self.cleanup(controller_logger)

    #
    # TODO: make sure that when WebAutomation extends this class,
    #       it runs its version of cleanup()
    #
    '''
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.automation.stop()
        self.cleanup_driver()
    '''

    def prep_unhandled_exception_email(self):
        return """look at logs (is the default unhandled exception email body
 defined in automation.py(), so if it is not informative enough, you have to
 implement prep_unhandled_exception_email(self, args) in your own class)"""

    #
    # TO DO: this is general to all automations, but each descendent class can
    #        implement its own prep_email_body() function
    #
    def send_unhandled_exception_email(self):

        from_email = APP_EMAIL
        to_email = UNHANDLED_EXCEPTION_EMAIL

        msg = MIMEMultipart()
        msg["From"] = from_email
        msg["To"] = to_email
        msg["Subject"] = f"{self.name} unhandled exception"
        body = self.prep_unhandled_exception_email()
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(APP_EMAIL, GMAIL_APP_PASS)
            server.sendmail(from_email, to_email, msg.as_string())

    #
    # TODO: should be simply try run except send email and restart
    #
    def _on_exception(self, controller_logger: logging.Logger):
        """
        Send exception email, wait 1 minute, then restart.
        """
        controller_logger.debug(
            f"sending unhandled exception email and restarting {self.name}"
        )
        self.cleanup(controller_logger)
        send_unhandled_exception_email(self.name)
        time.sleep(60.0)
        self.email_exception_handling_wrapper(controller_logger)

    def email_exception_handling_wrapper(self, controller_logger: logging.Logger):
        try:
            self._run_and_cleanup(controller_logger)
        except:
            controller_logger.exception("")
            self._on_exception(controller_logger)

    def start(self, controller_logger):
        """
        Define threading.Events
        to notify the automation to stop, and to notify the controller
        that the automation is stopped. Then, define its sleep (interruptable)
        function and start the email exception handling loop.
        """
        self.stop_event = threading.Event()
        self.stopped_event = threading.Event()
        self.sleep = lambda timeout: interruptable_sleep(
            self.stop_event, timeout, self.logger
        )

        threading.Thread(
            target=self.email_exception_handling_wrapper,
            args=(controller_logger,),
            daemon=True,
        ).start()
