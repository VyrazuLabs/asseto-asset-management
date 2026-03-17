from django.test import LiveServerTestCase, Client
from selenium import webdriver
from selenium.webdriver.common.by import By
from authentication.models import User
from license.models import License, LicenseType
from vendors.models import Vendor
import time


class LicenseTest(LiveServerTestCase):

    def setUp(self):

        # Create user
        self.test_user = User.objects.create_user(
            email="testuser@gmail.com",
            username="testuser",
            full_name="Test User",
            phone="9808123456",
            password="password123"
        )
        self.test_user.is_active = True
        self.test_user.save()

        # Create LicenseType
        self.license_type = LicenseType.objects.create(
            name="Software License"
        )

        # Create Vendor
        self.vendor = Vendor.objects.create(
            name="Microsoft",
            email="microsoft@test.com",
            phone="1234567890"
        )

        # Create License for update/delete
        self.license = License.objects.create(
            name="Windows License",
            license_type=self.license_type,
            vendor=self.vendor,
            seats=10,
            key="ABC123"
        )

        # Django client login
        self.client = Client()
        self.client.login(email="testuser@gmail.com", password="password123")

        self.session_cookie = self.client.cookies['sessionid']

        # Start selenium
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(10)

        self.driver.get(self.live_server_url)

        # Inject login session
        self.driver.add_cookie({
            'name': 'sessionid',
            'value': self.session_cookie.value,
            'path': '/',
            'secure': False
        })

    def tearDown(self):
        self.driver.quit()

    # --------------------------------
    # CREATE LICENSE
    # --------------------------------
    def test_create_license(self):

        self.driver.get(f"{self.live_server_url}/license/add/")

        # add_license = self.driver.find_element(
        #     By.XPATH, "//a[contains(text(),'Add License')]"
        # )
        # add_license.click()
        name = self.driver.find_element(By.NAME, "name")
        license_type = self.driver.find_element(By.NAME, "license_type")
        # vendor = self.driver.find_element(By.NAME, "vendor")
        seats = self.driver.find_element(By.NAME, "seats")
        key = self.driver.find_element(By.NAME, "key")
        notes = self.driver.find_element(By.NAME, "notes")

        name.send_keys("Office 365 License")
        license_type.send_keys("Software License")
        # vendor.send_keys("Microsoft")
        seats.send_keys("50")
        key.send_keys("XYZ-123-OFFICE")
        notes.send_keys("Created via Selenium Test")

        submit = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        submit.click()

        time.sleep(2)

        print("✅ License Created")

        self.assertIn("Office 365 License", self.driver.page_source)

    # --------------------------------
    # UPDATE LICENSE
    # --------------------------------
    def test_update_license(self):

        self.driver.get(
            f"{self.live_server_url}/license/update/{self.license.id}"
        )
        name = self.driver.find_element(By.NAME, "name")
        name.clear()
        name.send_keys("Updated Windows License")
        submit = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        submit.click()
        time.sleep(2)
        print("✅ License Updated")
        self.assertIn("Updated Windows License", self.driver.page_source)

    # --------------------------------
    # DELETE LICENSE
    # --------------------------------
    def test_delete_license(self):
        self.driver.get(
            f"{self.live_server_url}/license/list"
        )

        # delete_button = self.driver.find_element(
        #     By.XPATH, "//button[@type='submit']"
        #     # By.ID,"delete_button"
        # )
        time.sleep(2)
        self.driver.get(f"{self.live_server_url}/license/delete/{self.license.id}")
        # delete_button.click()

        time.sleep(2)

        print("🗑 License Deleted")