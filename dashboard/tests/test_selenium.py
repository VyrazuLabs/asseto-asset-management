from django.test import LiveServerTestCase, Client
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from authentication.models import User
from dashboard.models import Organization, Department
from authentication.models import User
from dashboard.models import Organization, Location, Address
import time
from selenium.common.exceptions import TimeoutException

class LocationTest(LiveServerTestCase):

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

    def navigate_to_locations_page(self):
        """Navigate to the locations list page."""
        locations_url = f"{self.live_server_url}/admin/locations/list/"
        self.driver.get(locations_url)
        
        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "add-location-button"))
        )
    
    def test_add_location_successfully(self):
        """Test adding a location successfully through the modal."""
        
        # Step 1: Click the Add Location button to open modal
        add_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "add-location-button"))
        )
        add_button.click()
        
        # Step 2: Wait for modal to appear and load content
        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "add-location-modal"))
        )
        
        # Wait for form to load via HTMX
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#add-location-modal-content form"))
        )
        
        # Small pause for HTMX to fully load
        time.sleep(1)
        
        # Step 3: Fill the form with test data
        test_data = {
            "office_name": "Main Office - Test",
            "contact_person": "John Smith",
            "contact_email": "john.smith@example.com",
            "contact_phone": "555-0123",
            "address_line_one": "123 Business Ave",
            "address_line_two": "Suite 500",
            "country": "USA",
            "state": "California",
            "city": "San Francisco",
            "pin_code": "94105"
        }
        
        # Fill office name (required)
        office_name_field = self.driver.find_element(By.NAME, "office_name")
        office_name_field.send_keys(test_data["office_name"])
        
        # Fill contact person
        contact_person_field = self.driver.find_element(By.NAME, "contact_person_name")
        contact_person_field.send_keys(test_data["contact_person"])
        
        # Fill contact email
        contact_email_field = self.driver.find_element(By.NAME, "contact_person_email")
        contact_email_field.send_keys(test_data["contact_email"])
        
        # Fill contact phone
        contact_phone_field = self.driver.find_element(By.NAME, "contact_person_phone")
        contact_phone_field.send_keys(test_data["contact_phone"])
        
        # Fill address line 1
        address1_field = self.driver.find_element(By.NAME, "address_line_one")
        address1_field.send_keys(test_data["address_line_one"])
        
        # Fill address line 2
        address2_field = self.driver.find_element(By.NAME, "address_line_two")
        address2_field.send_keys(test_data["address_line_two"])
        
        # Fill country
        country_field = self.driver.find_element(By.NAME, "country")
        country_field.send_keys(test_data["country"])
        
        # Fill state
        state_field = self.driver.find_element(By.NAME, "state")
        state_field.send_keys(test_data["state"])
        
        # Fill city
        city_field = self.driver.find_element(By.NAME, "city")
        city_field.send_keys(test_data["city"])
        
        # Fill zip code
        zip_field = self.driver.find_element(By.NAME, "pin_code")
        zip_field.send_keys(test_data["pin_code"])
        
        # Step 4: Take screenshot before submission (optional)
        self.driver.save_screenshot("/tmp/before_submission.png")
        
        # Step 5: Click Save button
        save_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        
        # Get current URL for reload detection
        current_url = self.driver.current_url
        
        # Click save
        save_button.click()
        
        # Step 6: Wait for modal to close (success) or errors to appear
        try:
            # Wait for modal to disappear (success case)
            WebDriverWait(self.driver, 10).until(
                EC.invisibility_of_element_located((By.ID, "add-location-modal"))
            )
            
            # Step 7: Wait for page reload (due to HTMX beforeSwap)
            WebDriverWait(self.driver, 10).until(
                lambda d: d.current_url != current_url
            )
            
        except TimeoutException:
            # Check for validation errors
            error_elements = self.driver.find_elements(By.CSS_SELECTOR, ".text-danger")
            if error_elements:
                errors = [elem.text for elem in error_elements if elem.text]
                self.fail(f"Form validation failed with errors: {errors}")
            else:
                self.fail("Modal did not close after submission")
        
        # Step 8: Take screenshot after submission
        self.driver.save_screenshot("/tmp/after_submission.png")
        
        # Step 9: Verify location was created in database
        location = Location.objects.filter(office_name=test_data["office_name"]).first()
        self.assertIsNotNone(location, "Location was not created in database")
        
        # Verify address was created
        self.assertIsNotNone(location.address, "Address was not created")
        
        # Verify field values
        self.assertEqual(location.office_name, test_data["office_name"])
        self.assertEqual(location.contact_person_name, test_data["contact_person"])
        self.assertEqual(location.contact_person_email, test_data["contact_email"])
        self.assertEqual(location.contact_person_phone, test_data["contact_phone"])
        
        # Verify address fields
        self.assertEqual(location.address.address_line_one, test_data["address_line_one"])
        self.assertEqual(location.address.address_line_two, test_data["address_line_two"])
        self.assertEqual(location.address.country, test_data["country"])
        self.assertEqual(location.address.state, test_data["state"])
        self.assertEqual(location.address.city, test_data["city"])
        self.assertEqual(location.address.pin_code, test_data["pin_code"])
        
        # Step 10: Verify location appears in the list on page
        table = self.driver.find_element(By.CSS_SELECTOR, "table")
        page_source = self.driver.page_source
        self.assertIn(test_data["office_name"], page_source, 
                     "Location name not found in table")


class LicenseTypeTestCase(LiveServerTestCase):
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

    def test_add_license_type(self):
        """Test adding a location successfully through the modal."""
        
        # Step 1: Click the Add Location button to open modal
        add_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "add-license-type-button"))
        )
        add_button.click()
        
        # Step 2: Wait for modal to appear and load content
        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "#add-license-type-modal"))
        )
        
        # Wait for form to load via HTMX
        # hx-target="#add-license-type-modal-content"
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#add-license-type-modal-content form"))
        )
        
        # Small pause for HTMX to fully load
        time.sleep(5)

        test_data = {
            "license_type": "Driving License",
        }
        
        # Fill office name (required)
        license_type_name_field = self.driver.find_element(By.NAME, "name")
        license_type_name_field.send_keys(test_data["license_type"])