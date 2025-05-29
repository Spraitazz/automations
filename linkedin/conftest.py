
import pytest
from selenium import webdriver
from unittest.mock import MagicMock

@pytest.fixture
def driver():
    driver = webdriver.Chrome()
    yield driver
    driver.quit()

@pytest.fixture
def mock_driver():
    mock = MagicMock()
    mock.get.return_value = None
    mock.find_element.return_value.text = "Welcome, testuser"
    return mock

