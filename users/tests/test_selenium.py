# from django.test import LiveServerTestCase
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# import time
# from authentication.models import User


# class UserLoginTest(LiveServerTestCase):

#     def setUp(self):
#         self.test_user = User.objects.create_user(
#             email="testuser@gmail.com",
#             username="testuser",
#             full_name="Test User",
#             phone="9808123456",
#             password="password123"
#         )

#         self.test_user.is_active = True
#         self.test_user.save()

#         self.driver = webdriver.Chrome()
#         self.driver.implicitly_wait(10)

#     def tearDown(self):
#         self.driver.quit()

#     def test_login(self):
#         self.driver.get(f"http://10.0.0.117:9000/login")

#         email_input = self.driver.find_element(By.NAME, "email")
#         password_input = self.driver.find_element(By.NAME, "password")
#         login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")

#         email_input.send_keys("testusergmail.com")
#         password_input.send_keys("password123")
#         login_button.click()
#         # wait until login completes (example: dashboard loads)
#         WebDriverWait(self.driver, 10).until(
#             EC.url_contains("/")
#         )
#         self.driver.get("http://10.0.0.117:9000/assets/list")
#         buttons = self.driver.find_elements(By.TAG_NAME, "button")
#         print("Total buttons found:", len(buttons))

#         for i, btn in enumerate(buttons):
#             try:
#                 print(
#                     f"{i} | text='{btn.text}' | type='{btn.get_attribute('type')}' | hx-get='{btn.get_attribute('hx-get')}'"
#                 )
#             except Exception as e:
#                 print(f"{i} | error reading button: {e}")
#         # add_btn = wait.until(
#         #     EC.element_to_be_clickable((By.CSS_SELECTOR, "button[hx-get='/vendors/add']"))
#         # )
#         # self.assertIn("Dashboard", self.driver.page_source)

from django.test import LiveServerTestCase, Client
from selenium import webdriver
from selenium.webdriver.common.by import By
from authentication.models import User
from dashboard.models import Organization
import time


class UserTest(LiveServerTestCase):

    def setUp(self):

        # Create admin user for login
        self.test_user = User.objects.create_user(
            email="admin@test.com",
            username="admin",
            full_name="Admin User",
            phone="9800000000",
            password="password123"
        )
        self.test_user.is_active = True
        self.test_user.is_staff = True
        self.test_user.save()

        # Organization required by User model
        self.organization = Organization.objects.create(
            name="Test Organization",
            website="www.test.com",
            email="org@test.com",
            phone="1234567890"
        )

        # User object for update/delete
        self.user = User.objects.create_user(
            email="olduser@test.com",
            username="olduser",
            full_name="Old User",
            phone="9811111111",
            password="password123",
            organization=self.organization
        )
        self.user.is_active = True
        self.user.save()

        # Django test client
        self.client = Client()

        # Login using Django client
        self.client.login(email="admin@test.com", password="password123")

        # Get session cookie
        self.session_cookie = self.client.cookies['sessionid']

        # Start selenium
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(10)

        # Open live server
        self.driver.get(self.live_server_url)

        # Inject login session
        self.driver.add_cookie({
            "name": "sessionid",
            "value": self.session_cookie.value,
            "path": "/",
            "secure": False
        })

    def tearDown(self):
        self.driver.quit()

    # -------------------------------
    # CREATE USER TEST
    # -------------------------------
    def test_create_user(self):

        self.driver.get(f"{self.live_server_url}/users/list")

        add_user_button = self.driver.find_element(
            By.XPATH, "//a[contains(text(),'Add User')]"
        )
        add_user_button.click()

        email = self.driver.find_element(By.NAME, "email")
        username = self.driver.find_element(By.NAME, "username")
        full_name = self.driver.find_element(By.NAME, "full_name")
        phone = self.driver.find_element(By.NAME, "phone")
        password = self.driver.find_element(By.NAME, "password")
        organization = self.driver.find_element(By.NAME, "organization")

        email.send_keys("seleniumuser@test.com")
        username.send_keys("seleniumuser")
        full_name.send_keys("Selenium Test User")
        phone.send_keys("9822222222")
        password.send_keys("password123")
        organization.send_keys("Test Organization")

        print("✅ User Created")

        submit = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        submit.click()

        time.sleep(2)

        self.assertIn("seleniumuser@test.com", self.driver.page_source)

    # -------------------------------
    # UPDATE USER TEST
    # -------------------------------
    def test_update_user(self):

        self.driver.get(
            f"{self.live_server_url}/users/update-assets-details/{self.user.id}"
        )

        full_name = self.driver.find_element(By.NAME, "full_name")
        full_name.clear()
        full_name.send_keys("Updated User")

        submit = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        submit.click()

        time.sleep(2)

        print("✅ User Updated")

        self.assertIn("Updated User", self.driver.page_source)

    # -------------------------------
    # DELETE USER TEST
    # -------------------------------
    def test_delete_user(self):

        self.driver.get(
            f"{self.live_server_url}/users/list"
        )

        delete_button = self.driver.find_element(
            By.XPATH, "//button[@type='submit']"
        )

        delete_button.click()

        time.sleep(2)

        print("🗑 User Deleted")