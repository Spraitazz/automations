import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from definitions import *
from utils import init_default_logger

def interruptable_sleep(event: threading.Event, timeout: float, logger: logging.Logger):
    """Not the ideal kind of sleep, but it does the job."""
    
    start_time = time.time()
    while not event.is_set():
        if time.time() - start_time >= timeout:
            break
        time.sleep(0.1)
    else:
        logger.debug("stopped by controller")


class Automation:
    """Wrapper for a persistent automation which handles starting,
    stopping, as well as re-starting and sending an email notification
    on catching an unhandled exception."""

    logger: typing.Optional[logging.Logger] = None 
    stop_event: typing.Optional[
        threading.Event
    ] = None  # this is to be set by controller to stop automation
    stopped_event: typing.Optional[
        threading.Event
    ] = None  # this is to be set by automation when its done
    sleep: typing.Optional[typing.Callable] = None

    def __init__(
        self,
        name: str,
        run_func: typing.Callable,
        config_fpath: str               
    ):
        self.name = name
        self.run_func = run_func
        self.config_fpath = config_fpath

    def set_config(self, config: dict):
        self.config = config

    def run(self):
        self.run_func(self)

    def cleanup(self, logger: logging.Logger):
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
            handler.close()
        self.stopped_event.set()

    def _run_and_cleanup(self, logger: logging.Logger):
        self.run()
        logger.debug(f"{self.name} stopped by return from run func")
        self.cleanup(logger)


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

    def _on_exception(self, logger: logging.Logger):
        """send exception email, wait 60 seconds, then restart"""
        logger.exception("")
        logger.debug(f"sending unhandled exception email and restarting {self.name}")
        self.cleanup(logger)
        send_unhandled_exception_email(self.name)
        time.sleep(60.0)
        self.email_exception_handling_wrapper(logger)

    def email_exception_handling_wrapper(self, logger: logging.Logger):
        try:
            self._run_and_cleanup(logger)
        except:
            self._on_exception(logger)     

    def start(self, controller_logger):

        logger, logs_folder_path = init_default_logger(self.name)

        self.logs_folder_path = logs_folder_path
        self.logger = logger
        self.stop_event = threading.Event()
        self.stopped_event = threading.Event()        
        self.sleep = lambda timeout: interruptable_sleep(
            self.stop_event, timeout, logger
        )

        threading.Thread(
            target=self.email_exception_handling_wrapper,
            args=(controller_logger,),
            daemon=True,
        ).start()



