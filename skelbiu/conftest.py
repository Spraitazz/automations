import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from skelbiu.definitions import *


# get external config
config_path = Path.home() / "automation_configs" / "skelbiu" / "config.ini"
config = {}
configfile = configparser.ConfigParser(interpolation=None)
configfile.read(config_path)
config["EMAIL"] = configfile["DEFAULT"]["EMAIL"].strip().strip('"')
config["PASS"] = configfile["DEFAULT"]["PASS"].strip().strip('"')


@pytest.fixture(scope="session")
def driver_config():
    """Configure Chrome driver options"""
    return DEFAULT_BROWSER_OPTIONS


@pytest.fixture(scope="function")
def driver(driver_config):
    """Create and teardown WebDriver instance for each test"""
    driver = webdriver.Chrome(options=driver_config)
    #
    # TODO: why this doesnt work without the implciit wait?
    #
    driver.implicitly_wait(10)
    yield driver
    driver.quit()


@pytest.fixture
def test_credentials():
    """Test credentials - replace with your actual test data"""
    return {
        "valid_email": config["EMAIL"],
        "valid_password": config["PASS"],
        "invalid_email": "spraitass@gmail.com",
        "invalid_password": "fs!4%ekski7r",
    }


"""    
@pytest.fixture
def mock_driver(request):
    simulate_disconnected = getattr(request, "param", False)

    mock = MagicMock()

    if simulate_disconnected:
        def fake_get(url):
            raise WebDriverException("Simulated network failure: Cannot reach " + url)
        mock.get.side_effect = fake_get
    else:
        mock.get.return_value = None

    # Mock find_element for consistency
    mock.find_element.return_value.text = "Welcome, testuser"
    
    return mock
"""
