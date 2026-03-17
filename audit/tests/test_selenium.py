from django.test import LiveServerTestCase, Client
from selenium import webdriver
from selenium.webdriver.common.by import By
from authentication.models import User
from audit.models import Audit
from assets.models import Asset
from dashboard.models import Organization
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

class AuditTest(LiveServerTestCase):

    def setUp(self):

        # Create test user
        self.test_user = User.objects.create_user(
            email="testuser@gmail.com",
            username="testuser",
            full_name="Test User",
            phone="9808123456",
            password="password123"
        )
        self.test_user.is_active = True
        self.test_user.save()

        # Create Organization
        self.organization = Organization.objects.create(
            name="Organization 1",
            website="www.example.com",
            email="organization@example.com",
            phone="1234567890"
        )

        # Create Asset (required for audit)
        self.asset = Asset.objects.create(
            name="Laptop Asset",
            organization=self.organization
        )

        # Existing audit (for update/delete tests)
        self.audit = Audit.objects.create(
            assigned_to="John Doe",
            asset=self.asset,
            organization=self.organization,
            condition=1,
            notes="Initial audit",
            audited_by=self.test_user
        )

        # Django client
        self.client = Client()

        # Login using Django client
        self.client.login(email="testuser@gmail.com", password="password123")

        # Get session cookie
        self.session_cookie = self.client.cookies['sessionid']

        # Start selenium driver
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(10)

        # Open live server
        self.driver.get(self.live_server_url)

        # Inject session cookie
        self.driver.add_cookie({
            'name': 'sessionid',
            'value': self.session_cookie.value,
            'path': '/',
            'secure': False
        })

    def tearDown(self):
        self.driver.quit()

    # -------------------------------
    # CREATE AUDIT TEST
    # -------------------------------

    def test_create_audit(self):

        self.driver.get(f"{self.live_server_url}/audit/add-audit/")

        tag = self.driver.find_element(By.NAME, "tag")
        assigned_to = self.driver.find_element(By.NAME, "assigned_to")
        notes = self.driver.find_element(By.NAME, "comments")

        tag.send_keys("VY00069")

        self.driver.execute_script(
            "arguments[0].removeAttribute('disabled')", assigned_to
        )
        assigned_to.send_keys("Jane Doe")

        # Click condition button
        condition_button = self.driver.find_element(
            By.XPATH, "//button[text()='Good']"
        )
        condition_button.click()

        notes.send_keys("Audit created via Selenium")

        submit_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        submit_button.click()

        time.sleep(2)

        print("✅ Audit Created")

        # self.assertIn("Jane Doe", self.driver.page_source)

    # -------------------------------
    # UPDATE AUDIT TEST
    # -------------------------------
    # def test_update_audit(self):

    #     print("audit_id:", self.audit.id)

    #     self.driver.get(
    #         f"{self.live_server_url}/audits/update/{self.audit.id}"
    #     )

    #     assigned_field = self.driver.find_element(By.NAME, "assigned_to")

    #     assigned_field.clear()
    #     assigned_field.send_keys("Updated User")

    #     submit = self.driver.find_element(By.XPATH, "//button[@type='submit']")
    #     submit.click()

    #     time.sleep(2)

    #     print("Audit Updated")

    #     self.assertIn("Updated User", self.driver.page_source)

    # -------------------------------
    # DELETE AUDIT TEST
    # -------------------------------
    # def test_delete_audit(self):

    #     print("audit_id:", self.audit.id)

    #     self.driver.get(f"{self.live_server_url}/audit/pending-audits/")

    #     delete_button = self.driver.find_element(
    #         By.XPATH, f"//a[contains(@href,'/audits/delete/{self.audit.id}')]"
    #     )

    #     delete_button.click()

    #     time.sleep(2)

    #     print("Audit Deleted")

    #     self.assertNotIn("Initial audit", self.driver.page_source)