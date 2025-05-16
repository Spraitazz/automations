from definitions import *


def interruptable_sleep(event: threading.Event, timeout: float, logger: logging.Logger):
    start_time = time.time()
    while not event.is_set():
        if time.time() - start_time >= timeout:
            break
        time.sleep(0.1)
    else:
        logger.debug("stopped by controller")


def send_unhandled_exception_email(bot_name: str):

    from_email = APP_EMAIL
    to_email = UNHANDLED_EXCEPTION_EMAIL
    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = f"{bot_name} unhandled exception"
    body = "look at logs"
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(APP_EMAIL, GMAIL_APP_PASS)
        server.sendmail(from_email, to_email, msg.as_string())


class AutomationState(IntEnum):
    ON = 0
    PAUSED = 1
    STOPPED = 2  # when this is set, the controller can finally clean up (del bots_running[bot_name])


#
# TO DO: add AutomationState
#
class Automation:

    def __init__(
        self,
        name: str,
        run_func: typing.Callable,
        config_fpath: str,
        logger: typing.Optional[logging.Logger] = None,
        stop_event: typing.Optional[
            threading.Event
        ] = None,  # this is to be set by controller to stop automation
        stopped_event: typing.Optional[
            threading.Event
        ] = None,  # this is to be set by automation when its done
        interruptable_sleep: typing.Optional[typing.Callable] = None,
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
        # not expecting to return
        logger.debug(f"{self.name} stopped by return from run func")
        self.cleanup(logger)

    def _on_exception(self, logger: logging.Logger):
        # send email, then restart
        logger.exception("")
        logger.debug(f"sending unhandled exception email and restarting {self.name}")
        self.cleanup(logger)
        send_unhandled_exception_email(self.name)
        time.sleep(10.0)
        self.email_exception_handling_wrapper(logger)

    def email_exception_handling_wrapper(self, logger: logging.Logger):
        try:
            self._run_and_cleanup(logger)
        except:
            self._on_exception(logger)
            """
            # send email, then restart
            logger.exception("")
            logger.debug(
                f"sending unhandled exception email and restarting {self.name}"
            )
            self.cleanup(logger)
            send_unhandled_exception_email(self.name)
            self.email_exception_handling_wrapper(logger)
            """

    def start(self, controller_logger):

        logs_folder_path = os.path.join(BASE_DIR, "logs", self.name)
        if not os.path.exists(logs_folder_path):
            os.makedirs(logs_folder_path)

        log_path = os.path.join(logs_folder_path, "log")
        logger = logging.getLogger(f"{self.name}_logger")
        logger.setLevel(LOG_LEVEL_DEFAULT)
        handler = TimedRotatingFileHandler(
            log_path, when="midnight", backupCount=LOG_NUM_DAYS_BACKUP_DEFAULT
        )
        handler.suffix = LOG_HANDLER_SUFFIX_DEFAULT
        handler.setLevel(LOG_LEVEL_DEFAULT)
        handler.setFormatter(LOG_FORMATTER_DEFAULT)
        logger.addHandler(handler)

        self.logs_folder_path = logs_folder_path
        self.logger = logger
        self.stop_event = threading.Event()
        self.stopped_event = threading.Event()
        self.interruptable_sleep = lambda timeout: interruptable_sleep(
            self.stop_event, timeout, logger
        )

        threading.Thread(
            target=self.email_exception_handling_wrapper,
            args=(controller_logger,),
            daemon=True,
        ).start()


#
# TO DO: un-hardcode xvfb params
#
class WebAutomation(Automation):
    driver: typing.Optional[ChromeDriver] = None

    def __init__(
        self,
        name: str,
        run_func: typing.Callable,
        config_fpath: str,
        with_xvfb: bool = False,
        xvfb_display: int = -1,
    ):
        super().__init__(name, run_func, config_fpath)
        self.driver = None
        self.with_xvfb = with_xvfb
        self.xvfb_display = xvfb_display

    def set_driver(self, driver: ChromeDriver):
        self.driver = driver

    def cleanup(self, logger: logging.Logger):
        try:
            self.driver.quit()
        except:
            logger.exception("")
        finally:
            self.driver = None
            super().cleanup(logger)

    def email_exception_handling_wrapper(self, logger: logging.Logger):

        try:
            if self.with_xvfb:
                with Xvfb(display=self.xvfb_display, width=2560, height=1600) as xvfb:
                    self._run_and_cleanup(logger)
            else:
                self._run_and_cleanup(logger)
        except:
            self._on_exception(logger)
            """
            # send email, then restart
            logger.exception("")
            logger.debug(
                f"sending unhandled exception email and restarting {self.name}"
            )
            self.cleanup(logger)
            send_unhandled_exception_email(self.name)
            self.email_exception_handling_wrapper(logger)
            """
