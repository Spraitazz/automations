from selenium import webdriver


DEFAULT_BROWSER_OPTIONS = webdriver.ChromeOptions()
DEFAULT_BROWSER_OPTIONS.add_argument("--incognito")
DEFAULT_BROWSER_OPTIONS.add_argument("--window-size=1920,1080")
DEFAULT_BROWSER_OPTIONS.add_argument("--start-maximized")
