import pytest

# import time
from skelbiu.login_page import LoginPage


class TestLoginFunctionality:
    """Test cases for login functionality using TDD approach"""

    def test_navigate_to_login_page(self, driver):
        """Test 1: Verify navigation to login page"""
        # Arrange
        login_page = LoginPage(driver)

        # Act
        login_page.navigate_to_login()

        # Assert
        assert "signin" in driver.current_url.lower()
        assert driver.title  # Page should have a title

    def test_login_page_elements_present(self, driver):
        """Test 2: Verify all login page elements are present"""
        # Arrange
        login_page = LoginPage(driver)
        login_page.navigate_to_login()

        # Act
        email_field = driver.find_element(*login_page.USERNAME_INPUT)
        password_field = driver.find_element(*login_page.PASSWORD_INPUT)
        login_button = driver.find_element(*login_page.LOGIN_BUTTON)

        # Assert
        assert email_field.is_displayed()
        assert password_field.is_displayed()
        assert login_button.is_displayed()

    def test_valid_login_success(self, driver, test_credentials):
        """Test 3: Verify successful login with valid credentials"""
        # Arrange
        login_page = LoginPage(driver)
        login_page.navigate_to_login()

        # Act
        login_success = login_page.login(
            test_credentials["valid_email"], test_credentials["valid_password"]
        )

        # Assert
        assert login_success is True
        assert login_page.is_login_successful()

    def test_invalid_credentials_login_failure(self, driver, test_credentials):
        """Test 4: Verify login failure with invalid email"""
        # Arrange
        login_page = LoginPage(driver)
        login_page.navigate_to_login()

        # Act
        login_success = login_page.login(
            test_credentials["invalid_email"], test_credentials["invalid_password"]
        )

        # Assert
        assert not login_success is True
        assert not login_page.is_login_successful()
        error_message = login_page.get_error_message()
        assert error_message is not None
        assert "neteisingi prisijungimo duomenys" in error_message.lower()

    '''
    @pytest.mark.parametrize("email,password,expected_result", [
        ("", "", False),
        ("test@example.com", "", False),
        ("", "password123", False),
        ("invalid-email", "password123", False),
        ("test@example.com", "short", False),
    ])
    def test_login_validation_scenarios(self, driver, marketplace_urls, email, password, expected_result):
        """Test 8: Parametrized test for various validation scenarios"""
        # Arrange
        login_page = LoginPage(driver)
        login_page.navigate_to_login(marketplace_urls["login_url"])
        
        # Act
        login_page.login(email, password)
        
        # Assert
        assert login_page.is_login_successful() == expected_result
    '''


"""
@pytest.mark.real
def test_login_real(driver):
    driver.get(LOGIN_URL)
    
    target = driver.find_element(By.ID, "onetrust-reject-all-handler")
    target.click()
    click_delay()

    # These elements might not exist yet!
    driver.find_element(By.ID, "username").send_keys("testuser")
    driver.find_element(By.ID, "password").send_keys("securepassword")
    driver.find_element(By.ID, "login-button").click()

    welcome_text = driver.find_element(By.ID, "welcome").text
    assert "Welcome, testuser" in welcome_text
  
    
@pytest.mark.mock
@pytest.mark.parametrize("mock_driver", [False], indirect=True)
def test_mock_driver_connected(mock_driver):
    mock_driver.get(LOGIN_URL)
    text = mock_driver.find_element().text
    assert "Welcome" in text

@pytest.mark.mock
@pytest.mark.parametrize("mock_driver", [True], indirect=True)
def test_mock_driver_disconnected(mock_driver):
    with pytest.raises(WebDriverException, match="Simulated network failure"):
        mock_driver.get(LOGIN_URL)
"""
