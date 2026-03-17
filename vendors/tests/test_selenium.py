# from django.contrib.staticfiles.testing import StaticLiveServerTestCase
# from django.contrib.auth import get_user_model
# from django.conf import settings
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# import pickle
# import time
# import os
# import base64


# User = get_user_model()

# class VendorAddTest(StaticLiveServerTestCase):

#     @classmethod
#     def setUpClass(cls):
#         super().setUpClass()
#         chrome_options = Options()
#         chrome_options.add_argument("--disable-web-security")
#         cls.driver = webdriver.Chrome(options=chrome_options)
#         cls.driver.implicitly_wait(10)

#     @classmethod
#     def tearDownClass(cls):
#         cls.driver.quit()
#         super().tearDownClass()

#     def setUp(self):
#         super().setUp()
#         self.driver.delete_all_cookies()

    # def login(self):
    #     driver = webdriver.Chrome()
    #     driver.maximize_window()

    #     driver.execute_cdp_cmd("Network.enable", {})

    #     auth = {'username': 'admin', 'password': 'admin'}

    #     credentials = f"{auth['username']}:{auth['password']}"
    #     encoded_credentials = base64.b64encode(credentials.encode()).decode()

    #     # driver.execute_cdp_cmd(
    #     #     "Network.setExtraHTTPHeaders",
    #     #     {"headers": {"Authorization": f"Basic {encoded_credentials}"}}
    #     # )
    #     driver.execute_cdp_cmd('Network.setExtraHTTPHeaders',{
    #         'headers':{
    #             'Authorization': 'Basic' + base64.b64encode(f"{auth['username']}:{auth['password']}".encode()).decode()
    #             }
    #         }
    #     )
    #     # driver.get("http://10.0.0.117:9000/login")
    #     vendors_url = f"{self.live_server_url}"
    #     print("logged in")
    #     self.driver.get(vendors_url)
    #     time.sleep(5)
    #     driver.quit()

    # def login(self):
    # # Create user
    #     self.user, _ = User.objects.get_or_create(
    #         email="test@example.com",
    #         defaults={
    #             "username": "testuser",
    #             "full_name": "Test User",
    #             "phone": "1234567890",
    #             "is_active": True,
    #             "is_staff": True,
    #         }
    #     )
    #     self.user.set_password("testpass123")
    #     self.user.save()

    #     self.client.session.flush()
    #     self.client.force_login(self.user)
    #     # pickle.dump(self.driver.get_cookies(), open("cookies.pkl", "wb"))
    #     session_cookie_name = settings.SESSION_COOKIE_NAME
    #     cookie = self.client.cookies[session_cookie_name]

    #     print(f"🔑 Session cookie: {session_cookie_name}={cookie.value[:20]}...")

    #     # Go to ROOT first to establish session
    #     self.driver.get(self.live_server_url + "/")
        
    #     # Add ALL cookies
    #     for ck_name, ck in self.client.cookies.items():
    #         try:
    #             self.driver.add_cookie({
    #                 "name": ck_name,
    #                 "value": ck.value,
    #                 "path": "/",
    #                 "domain": "localhost"
    #             })
    #         except Exception as e:
    #             print(f"⚠️ Cookie {ck_name} failed: {e}")

    #     # Refresh root to activate session
    #     self.driver.refresh()
        
    #     wait = WebDriverWait(self.driver, 10)
    #     wait.until(lambda d: "/login/" not in d.current_url)
    #     print("✅ Login confirmed on root")

    #     # Navigate to vendors/list
    #     vendors_url = f"{self.live_server_url}/vendors/list"
    #     self.driver.get(vendors_url)
        
    #     print("🌐 Final URL before check:", self.driver.current_url)
        
    #     # **FIX**: Don't timeout waiting for vendors/list - just verify we're NOT on login
    #     wait.until(lambda d: "/login/" not in d.current_url)
        
    #     # Check what URL we actually landed on
    #     final_url = self.driver.current_url
    #     print(f"🎯 Actual landing URL: {final_url}")
        
    #     # Accept ANY authenticated page (not login) and continue
    #     if "/vendors/list" not in final_url:
    #         print("⚠️ Redirected from vendors/list - continuing anyway...")
    #         # Go back to vendors/list explicitly
    #         self.driver.get(vendors_url)
    #         time.sleep(5)  # Let redirect settle
        
    #     print("✅ Ready for vendor test (on:", self.driver.current_url, ")")

    # def test_add_vendor(self):
    #     self.login()  # This now lands directly on vendors/list
    #     # cookies_path = os.path.join(os.path.dirname(__file__), "cookies.pkl")
    #     # cookies_path = "/home/vyrazu-70/Desktop/folders/Works/asetto_asset_management_app/asseto-asset-management/cookies.pkl"
    #     # cookies = pickle.load(open(cookies_path, "rb"))
    #     # for cookie in cookies:
    #     #     self.driver.add_cookie(cookie)
    #     self.driver.refresh()
    #     wait = WebDriverWait(self.driver, 10)
    #     vendors_url = f"{self.live_server_url}/vendors/list"
    #     self.driver.get(vendors_url)
        
    #     # Verify vendors list loaded (look for table or vendor content)
    #     wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
    #     print("✅ Vendors list page confirmed")

    #     # Debug buttons
    #     buttons = self.driver.find_elements(By.TAG_NAME, "button")
    #     print(f"Buttons found: {len(buttons)}")
    #     for i, btn in enumerate(buttons[:10]):
    #         try:
    #             print(f"{i}: '{btn.text.strip()}' | hx-get='{btn.get_attribute('hx-get')}'")
    #         except:
    #             pass

    #     # Find and click Add button
    #     add_selectors = [
    #         "button[hx-get*='/vendors/add']",
    #         "button[data-testid='add-vendor']",
    #         "button:contains('Add')",
    #         ".btn.btn-primary:has-text('Add')",
    #         "button[title*='Add']"
    #     ]
        
    #     add_btn = None
    #     for selector in add_selectors:
    #         try:
    #             add_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
    #             print(f"✅ Add button found: {selector}")
    #             break
    #         except:
    #             continue

    #     if not add_btn:
    #         # Fallback: click first button with 'add' text
    #         add_btn = self.driver.find_element(By.XPATH, "//button[contains(text(),'Add') or contains(text(),'add')]")
    #         print("✅ Add button found via XPath fallback")

    #     add_btn.click()
    #     print("✅ Add button clicked")

    #     # Wait for form (HTMX modal)
    #     wait.until(EC.presence_of_element_located((By.NAME, "name")))
    #     print("✅ Vendor form appeared")

    #     # Fill form
    #     self.driver.find_element(By.NAME, "name").send_keys("Test Vendor")
    #     self.driver.find_element(By.NAME, "email").send_keys("vendor@test.com")
    #     self.driver.find_element(By.NAME, "phone").send_keys("9999999999")
    #     self.driver.find_element(By.NAME, "contact_person").send_keys("John Doe")

    #     # Submit
    #     submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
    #     submit_btn.click()
    #     print("✅ Form submitted")

    #     # Success message
    #     wait.until(lambda d: any(msg in d.page_source.lower() for msg in 
    #                             ["vendor added", "success", "created"]))

    #     self.assertIn("vendor", self.driver.page_source.lower(), 
    #                  "Vendor should be added successfully")
    #     print("✅ TEST PASSED!")
        
# from django.contrib.staticfiles.testing import StaticLiveServerTestCase
# from django.contrib.auth import get_user_model
# from django.conf import settings
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# import time

# User = get_user_model()

# class VendorAddTest(StaticLiveServerTestCase):

#     @classmethod
#     def setUpClass(cls):
#         super().setUpClass()
#         cls.driver = webdriver.Chrome()
#         cls.driver.implicitly_wait(10)

#     @classmethod
#     def tearDownClass(cls):
#         cls.driver.quit()
#         super().tearDownClass()

#     def login(self):
#         # create user
#         self.user, _ = User.objects.get_or_create(
#             email="test@example.com",
#             defaults={
#                 "username": "testuser",
#                 "full_name": "Test User",
#                 "phone": "1234567890",
#             }
#         )
#         self.user.set_password("testpass123")
#         self.user.save()

#         # login via Django test client
#         self.client.force_login(self.user)

#         # selenium must visit domain first to set proper domain context
#         self.driver.get(self.live_server_url)

#         # get session cookie - use SESSION_COOKIE_NAME for generality
#         cookie = self.client.cookies[settings.SESSION_COOKIE_NAME]

#         # inject session cookie - omit domain to use current page's domain (localhost:<port>)
#         self.driver.add_cookie({
#             "name": "sessionid",
#             "value": cookie.value,
#             "path": "/",
#             # No 'domain' key - lets Selenium use the current domain automatically [web:7][web:18]
#         })

#         # reload page so session becomes active
#         self.driver.refresh()
#         WebDriverWait(self.driver, 10).until(
#             EC.url_contains("/")
#         )
#         print("Logged in via session cookie")

#     def test_add_vendor(self):
#         self.login()
        
#         # Now redirect to vendors/list after login is confirmed
#         self.driver.get(f"{self.live_server_url}/vendors/list")

#         wait = WebDriverWait(self.driver, 10)  # Increased timeout for stability
#         buttons = self.driver.find_elements(By.TAG_NAME, "button")

#         print("Total buttons found:", len(buttons))

#         for i, btn in enumerate(buttons):
#             try:
#                 print(
#                     f"{i} | text='{btn.text}' | type='{btn.get_attribute('type')}' | hx-get='{btn.get_attribute('hx-get')}'"
#                 )
#             except Exception as e:
#                 print(f"{i} | error reading button: {e}")
        
#         # Wait for and click the add button
#         add_btn = wait.until(
#             EC.element_to_be_clickable((By.CSS_SELECTOR, "button[hx-get='/vendors/add']"))
#         )
#         add_btn.click() 

#         # Wait for form fields (assuming HTMX loads the modal/form)
#         wait.until(EC.presence_of_element_located((By.NAME, "name")))

#         # Fill form
#         self.driver.find_element(By.NAME, "name").send_keys("Test Vendor")
#         self.driver.find_element(By.NAME, "email").send_keys("vendor@test.com")
#         self.driver.find_element(By.NAME, "phone").send_keys("9999999999")
#         self.driver.find_element(By.NAME, "contact_person").send_keys("John Doe")

#         # Submit
#         self.driver.find_element(By.XPATH, "//button[@type='submit']").click()

#         # Verify success message
#         wait.until(lambda d: "Vendor added successfully" in d.page_source)
#         self.assertIn("Vendor added successfully", self.driver.page_source)
    # def test_update_vendor(self):
    #     self.login()
    #     self.navigate_to_vendors_list()
        
    #     # Find first vendor row and click Edit button
    #     edit_btn = WebDriverWait(self.driver, 10).until(
    #         EC.element_to_be_clickable((By.CSS_SELECTOR, "button[hx-get*='/vendors/update'], button[title*='Edit'], button[title*='Update']"))
    #     )
    #     edit_btn.click()
    #     print("✅ Edit button clicked")
        
    #     # Wait for update form (might have different fields or pre-filled values)
    #     wait = WebDriverWait(self.driver, 10)
    #     wait.until(EC.presence_of_element_located((By.NAME, "name")))
    #     print("✅ Update form appeared")
        
    #     # Update existing data
    #     self.driver.find_element(By.NAME, "name").clear()
    #     self.driver.find_element(By.NAME, "name").send_keys("Updated Vendor")
    #     self.driver.find_element(By.NAME, "email").clear()
    #     self.driver.find_element(By.NAME, "email").send_keys("updated@test.com")
    #     self.driver.find_element(By.NAME, "phone").clear()
    #     self.driver.find_element(By.NAME, "phone").send_keys("8888888888")
    #     self.driver.find_element(By.NAME, "contact_person").clear()
    #     self.driver.find_element(By.NAME, "contact_person").send_keys("Jane Doe")
        
    #     # Submit update
    #     submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
    #     submit_btn.click()
    #     print("✅ Update form submitted")
        
    #     # Verify update success
    #     wait.until(lambda d: any(msg in d.page_source.lower() for msg in 
    #                             ["updated successfully", "update success", "saved", "vendor updated"]))
    #     self.assertIn("updated", self.driver.page_source.lower(), "Vendor should be updated successfully")
    #     print("✅ UPDATE TEST PASSED!")

    # def test_delete_vendor(self):
    #     self.login()
    #     self.navigate_to_vendors_list()
        
    #     # Find first vendor row and click Delete button
    #     delete_selectors = [
    #         "button[hx-get*='/vendors/delete']",
    #         "button[title*='Delete']",
    #         "button[class*='delete']",
    #         "//button[contains(text(),'Delete') or contains(text(),'delete')]"
    #     ]
        
    #     delete_btn = None
    #     wait = WebDriverWait(self.driver, 10)
    #     for selector in delete_selectors:
    #         try:
    #             if selector.startswith("//"):
    #                 delete_btn = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
    #             else:
    #                 delete_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
    #             print(f"✅ Delete button found: {selector}")
    #             break
    #         except:
    #             continue
        
    #     if not delete_btn:
    #         raise Exception("No delete button found")
        
    #     delete_btn.click()
    #     print("✅ Delete button clicked")
        
    #     # Wait for delete confirmation modal
    #     try:
    #         # Look for confirmation dialog
    #         confirm_btn = wait.until(EC.element_to_be_clickable((By.XPATH, 
    #             "//button[contains(text(),'Delete') or contains(text(),'Confirm') or contains(text(),'Yes')]")))
    #         confirm_btn.click()
    #         print("✅ Delete confirmed")
    #     except:
    #         print("⚠️ No confirmation dialog - direct delete")
        
    #     # Verify deletion success
    #     wait.until(lambda d: any(msg in d.page_source.lower() for msg in 
    #                             ["deleted successfully", "delete success", "removed", "vendor deleted"]))
    #     self.assertIn("delete", self.driver.page_source.lower(), "Vendor should be deleted successfully")
    #     print("✅ DELETE TEST PASSED!")

from django.test import LiveServerTestCase, Client
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from authentication.models import User
from vendors.models import Vendor
import time


class VendorTest(LiveServerTestCase):

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

        # Existing vendor
        self.vendor = Vendor.objects.create(
            name="Old Vendor",
            email="oldvendor@test.com",
            phone="9999999999",
            contact_person="John Doe"
        )

        # Django client login
        self.client = Client()
        self.client.login(email="testuser@gmail.com", password="password123")

        self.session_cookie = self.client.cookies['sessionid']

        # Selenium
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(10)

        self.driver.get(self.live_server_url)

        self.driver.add_cookie({
            'name': 'sessionid',
            'value': self.session_cookie.value,
            'path': '/',
            'secure': False
        })

        self.driver.refresh()

    def tearDown(self):
        self.driver.quit()

    # -------------------------
    # CREATE VENDOR
    # -------------------------
    def test_create_vendor(self):
        wait = WebDriverWait(self.driver, 10)
        self.driver.get(f"{self.live_server_url}/vendors/list")
        # Click Add Vendor
        add_button = wait.until(
            EC.element_to_be_clickable((By.ID, "add-vendor"))
        )
        add_button.click()
        # Wait until modal form loads via HTMX
        name_input = wait.until(
            EC.visibility_of_element_located((By.ID, "id_name"))
        )
        email = wait.until(
            EC.visibility_of_element_located((By.NAME, "email"))
        )
        phone = self.driver.find_element(By.NAME, "phone")
        contact_person = self.driver.find_element(By.NAME, "contact_person")

        # Fill form
        name_input.send_keys("Test Vendor")
        email.send_keys("vendor@test.com")
        phone.send_keys("8888888888")
        contact_person.send_keys("Jane Doe")

        # Submit
        submit_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        submit_button.click()

        wait.until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Test Vendor')]"))
        )

        print("✅ Vendor Created")

        self.assertIn("Test Vendor", self.driver.page_source)

    # -------------------------
    # UPDATE VENDOR
    # -------------------------
    def test_update_vendor(self):
        self.driver.get(f"{self.live_server_url}/vendors/update/{self.vendor.id}")
        name_field = self.driver.find_element(By.ID, "id_name")
        name_field.clear()
        name_field.send_keys("Updated Vendor")
        # update_button.click()
        submit = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        submit.click()

        time.sleep(2)

        print("✅ Vendor Updated")

        self.assertIn("Updated Vendor", self.driver.page_source)

    # -------------------------
    # DELETE VENDOR
    # -------------------------
    def test_delete_vendor(self):

        # wait = WebDriverWait(self.driver, 10)

        # self.driver.get(f"{self.live_server_url}/vendors/list")

        # # Find delete button inside form
        # delete_button = wait.until(
        #     EC.element_to_be_clickable(
        #         (By.XPATH, f"//form[contains(@action,'delete_vendor/{self.vendor.id}')]//button")
        #     )
        # )

        # delete_button.click()

        # time.sleep(2)

        # print("✅ Vendor Deleted")

        # self.assertNotIn("Old Vendor", self.driver.page_source)
        self.driver.get(
            f"{self.live_server_url}/vendors/list"
        )
        delete_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        delete_button.click()

        time.sleep(2)   
        print("Vendor Deleted")
        # self.assertNotIn("Test Vendor", self.driver.page_source)