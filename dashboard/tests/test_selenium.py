from django.test import LiveServerTestCase, Client
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from authentication.models import User
from dashboard.models import Organization, Department
from authentication.models import User
from dashboard.models import Organization, Location, Address

class DepartmentTest(LiveServerTestCase):

    def setUp(self):
        self.test_user = User.objects.create_user(
            email="testuser@gmail.com",
            username="testuser",
            full_name="Test User",
            phone="9808123456",
            password="password123"
        )

        self.test_user.is_active = True
        self.test_user.save()

        self.organization = Organization.objects.create(
            name="Test Organization",
            website="www.example.com",
            email="org@example.com",
            phone="1234567890"
        )

        self.department = Department.objects.create(
            name="Old Department",
            contact_person_name="Old Person",
            contact_person_email="old@example.com",
            contact_person_phone="9876543210",
            organization=self.organization
        )

        self.client = Client()
        self.client.login(email="testuser@gmail.com", password="password123")

        self.session_cookie = self.client.cookies['sessionid']

        self.driver = webdriver.Chrome()
        self.driver.get(self.live_server_url)

        self.driver.add_cookie({
            'name': 'sessionid',
            'value': self.session_cookie.value,
            'path': '/',
            'secure': False
        })

        self.wait = WebDriverWait(self.driver, 10)

    def tearDown(self):
        self.driver.quit()

    def wait_for_location_modal_open(self):
        """Wait for #add-location-modal to change from display:none → visible"""
        timeout=15
        wait = WebDriverWait(self.driver, timeout)
        
        def modal_visible(driver):
            modal = driver.find_element(By.ID, "add-location-modal")
            style = modal.value_of_css_property("display")
            visible = modal.is_displayed()
            print(f"Modal display: '{style}', is_displayed(): {visible}")
            return visible
        
        # Wait for modal to become visible
        wait.until(modal_visible)
        print("✅ Modal opened (display: block)")
        
        # Extra wait for form fields (HTMX content swap)
        wait.until(EC.presence_of_element_located((By.ID, "id_office_name")))
        print("✅ Form fields loaded")
        return True

    def test_create_location(self):
        self.driver.get(f"{self.live_server_url}/admin/locations/list")

        # Click Add Location
        add_button = self.wait.until(
            EC.element_to_be_clickable((By.ID, "add-location-button"))
        )
        add_button.click()
        print("Button Clicked")
        # Wait for modal open
        if add_button.click():
        #   val=self.wait.until(lambda d: "show" in d.find_element(By.ID, "add-location-modal"))
            self.wait.until(EC.presence_of_element_located((By.ID, "add-location-modal")))
            print("Modal Opened")
        else:
            print("Modal not opened")
        # Wait for HTMX content
        # self.wait.until(
        #     lambda d: d.find_element(By.ID, "add-location-modal-content")
        #             .get_attribute("innerHTML").strip() != ""
        # )
        # print("HTMX Content Loaded")
        # Wait for form ready
        modal = self.driver.find_element(By.ID, "add-location-modal-content")

        office = self.wait.until(
            EC.element_to_be_clickable((By.ID, "id_office_name"))
        )

        # Fill form
        office.send_keys("Test Office")
        modal.find_element(By.ID, "id_contact_person_name").send_keys("John Doe")
        modal.find_element(By.ID, "id_contact_person_email").send_keys("john@example.com")
        modal.find_element(By.ID, "id_contact_person_phone").send_keys("9999999999")
        modal.find_element(By.ID, "id_address_line_one").send_keys("Street 1")
        modal.find_element(By.ID, "id_city").send_keys("Kathmandu")
        modal.find_element(By.ID, "id_state").send_keys("Bagmati")
        modal.find_element(By.ID, "id_country").send_keys("Nepal")
        modal.find_element(By.ID, "id_pin_code").send_keys("44600")

        # Submit
        modal.find_element(By.XPATH, ".//button[@type='submit']").click()

        # Wait for result in table
        self.wait.until(
            EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Test Office")
        )

        print("✅ Location Created")


    # --------------------------------
    # UPDATE DEPARTMENT
    # --------------------------------
    # def test_update_department(self):

    #     self.driver.get(f"{self.live_server_url}/admin/departments/list")

    #     # Click edit button
    #     edit_button = self.wait.until(
    #         EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-info"))
    #     )
    #     edit_button.click()

    #     # Wait for modal content to load
    #     name = self.wait.until(
    #         EC.visibility_of_element_located((By.NAME, "name"))
    #     )

    #     name.clear()
    #     name.send_keys("Updated Department")

    #     submit = self.driver.find_element(By.XPATH, "//button[@type='submit']")
    #     submit.click()

    #     self.wait.until(
    #         EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Updated Department")
    #     )

    #     print("✅ Department Updated")

    # # --------------------------------
    # # DELETE DEPARTMENT
    # # --------------------------------
    # def test_delete_department(self):

    #     self.driver.get(f"{self.live_server_url}/admin/departments/list")

    #     delete_button = self.wait.until(
    #         EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-danger"))
    #     )

    #     delete_button.click()

    #     # Confirm alert if exists
    #     try:
    #         alert = self.driver.switch_to.alert
    #         alert.accept()
    #     except:
    #         pass

    #     self.wait.until(
    #         EC.invisibility_of_element_located((By.XPATH, "//td[contains(text(),'Old Department')]"))
    #     )

    #     print("✅ Department Deleted")


