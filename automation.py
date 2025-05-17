import re

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
            if self.driver is not None:
                self.driver.quit()
        except:
            logger.exception("")
        finally:
            self.driver = None
            super().cleanup(logger)

    def driver_try_get(self, url: str):

        num_tries_max = 3
        retry_sleep_s = 10.0
        i_try = 0
        while i_try < num_tries_max:
            try:
                self.driver.get(url)
                return
            except:
                self.logger.debug(
                    f"connection error on try {i_try+1}/{num_tries_max}, will retry in {retry_sleep_s} s"
                )
                self.interruptable_sleep(retry_sleep_s)
                i_try += 1
        exc_fstr = f"driver could not get {url} after {num_tries_max} tries"
        self.logger.error(exc_fstr)
        raise Exception(exc_fstr)

    def driver_try_click(self, elem: WebElement):

        try:
            elem.click()
            return True
        except ElementClickInterceptedException as e:
            # Click intercepted
            pass
            # Try to extract the intercepting element
            match = re.search(r"Other element would receive the click: (.+?)\n", str(e))
            if match:
                html_snippet = match.group(1)
                # print("Intercepting element:", html_snippet)

                # Try to build a selector from id > class > tag
                id_match = re.search(r'id="([^"]+)"', html_snippet)
                class_match = re.search(r'class="([^"]+)"', html_snippet)
                tag_match = re.search(r"<(\w+)", html_snippet)

                selector = None
                if id_match:
                    selector = f"#{id_match.group(1)}"
                elif class_match:
                    class_selector = "." + ".".join(class_match.group(1).split())
                    selector = (
                        f"{tag_match.group(1)}{class_selector}"
                        if tag_match
                        else class_selector
                    )
                elif tag_match:
                    selector = tag_match.group(1)

                if selector:
                    # Try to hide {selector}
                    self.driver.execute_script(
                        f"""
                        var el = document.querySelector("{selector}");
                        if (el) {{
                            el.style.display = "none";
                            el.remove();
                        }}
                        """
                    )
                    time.sleep(0.5)
                else:
                    pass
                    # Could not construct a selector from the intercepted element
            else:
                # Could not extract element from exception
                pass

            return False

    def email_exception_handling_wrapper(self, logger: logging.Logger):

        try:
            if self.with_xvfb:
                with Xvfb(display=self.xvfb_display, width=2560, height=1600) as xvfb:
                    self._run_and_cleanup(logger)
            else:
                self._run_and_cleanup(logger)
        except:
            self._on_exception(logger)

