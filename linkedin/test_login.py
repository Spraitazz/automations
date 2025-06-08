from selenium import webdriver
from selenium.webdriver.common.by import By
import pytest

# in conftest.py
"""
@pytest.fixture
def driver():
    driver = webdriver.Chrome()
    yield driver
    driver.quit()
"""


@pytest.mark.real
def test_login_real(driver):
    driver.get("http://example.com/login")

    # These elements might not exist yet!
    driver.find_element(By.ID, "username").send_keys("testuser")
    driver.find_element(By.ID, "password").send_keys("securepassword")
    driver.find_element(By.ID, "login-button").click()

    welcome_text = driver.find_element(By.ID, "welcome").text
    assert "Welcome, testuser" in welcome_text


@pytest.mark.mock
def test_login_mock(mock_driver):
    driver = mock_driver
    # interact with mock driver instead
    driver.get("http://example.com/login")  # doesn't really go there
