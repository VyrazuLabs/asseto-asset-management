# from selenium.webdriver.common.by import By
# from django.test import LiveServerTestCase
# import time
# from selenium import webdriver
# from authentication.models import User
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# class UserLoginTest(LiveServerTestCase):

#     def setUp(self):
#         # self.test_user = User.objects.create_user(
#         #     email="testuser@gmail.com",
#         #     username="testuser",
#         #     full_name="Test User",
#         #     phone="9808123456",
#         #     password="password123"
#         # )

#         # self.test_user.is_active = True
#         # self.test_user.save()

#         self.driver = webdriver.Chrome()
#         self.driver.implicitly_wait(10)

#     # def tearDown(self):
#     #     self.driver.quit()

#     # def test_login(self):
#     #     self.driver.get("http://10.0.0.91:9000")

#     #     email_input = self.driver.find_element(By.NAME, "email")
#     #     password_input = self.driver.find_element(By.NAME, "password")
#     #     login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")

#     #     email_input.send_keys("testusergmail.com")
#     #     password_input.send_keys("password123")
#     #     login_button.click()
#     #     print("Login Done")
#         # time.sleep(2)

#     def test_asset_add(self):
#         # self.assertIn("Dashboard", self.driver.page_source)
#         # self.test_login()
#         # Step 2: open asset page
#         self.driver.get("http://10.0.0.91:9000/assets/list")

#         # Step 3: click add asset
#         # add_asset = self.driver.find_element(By.CSS_SELECTOR("button[class*='btn btn-sm btn-outline-info my-3 me-2']"))
    
#         # add_asset=self.driver.find_element(By.XPATH, "//button[text()='Add Asset']").click()
#         add_asset = self.driver.find_element(By.ID, "asset-add")
#         # add_asset = WebDriverWait(self.driver, 10).until(
#         #     EC.element_to_be_clickable((By.ID, "asset-add"))
#         # )
#         add_asset.click()

#         # Step 4: fill form
#         tag = self.driver.find_element(By.NAME, "tag")
#         name = self.driver.find_element(By.NAME, "name")
#         serial = self.driver.find_element(By.NAME, "serial_no")
#         price = self.driver.find_element(By.NAME, "price")

#         tag.send_keys("ASSET-001")
#         name.send_keys("Office Laptop")
#         serial.send_keys("SN123456")
#         price.send_keys("1200")

#         # Step 5: submit
#         submit_button = self.driver.find_element(By.ID, "asset-add")
#         submit_button.click()

#         time.sleep(2)

#         # Step 6: verify asset created
#         self.assertIn("Office Laptop", self.driver.page_source)

# # class AssetEditTest(LiveServerTestCase):

# #     def test_edit_asset(self):

# #         print("Editing Asset ----------")

# #         # self.login()

#         self.driver.get("http://10.0.0.91:9000/assets/update/1")

#         name = self.driver.find_element(By.NAME, "name")
#         name.clear()
#         name.send_keys("Updated Asset Name")

#         self.driver.find_element(By.XPATH, "//button[@type='submit']").click()

#         self.assertIn("Updated Asset Name", self.driver.page_source)

# # class AssetDeleteTest(LiveServerTestCase):

#     # def test_delete_asset(self):

#         print("Deleting Asset ----------")

#         # self.login()

#         self.driver.get("http://10.0.0.91:9000/assets/delete/1")

#         delete_button = self.driver.find_element(By.XPATH, "//a[contains(@href,'delete')]")
#         delete_button.click()

#         confirm = self.driver.find_element(By.XPATH, "//button[contains(text(),'Confirm')]")
#         confirm.click()

#         self.assertNotIn("Office Laptop", self.driver.page_source)

# # class AssetImageUploadTest(LiveServerTestCase):

#     # def test_upload_asset_image(self):

#         print("Uploading Asset Image ----------")

        

#         self.driver.get("http://10.0.0.91:9000/assets/update/1")

#         image_input = self.driver.find_element(By.NAME, "image")

#         image_input.send_keys("/home/youruser/test_image.jpg")

#         self.driver.find_element(By.XPATH, "//button[@type='submit']").click()

#         self.assertIn("image", self.driver.page_source)

from django.test import LiveServerTestCase, Client
from selenium import webdriver
from selenium.webdriver.common.by import By
from authentication.models import User
from assets.models import Asset, AssetStatus
from products.models import Product
from vendors.models import Vendor
from dashboard.models import ProductCategory, ProductType, Organization,Location
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class AssetTest(LiveServerTestCase):

    def setUp(self):

        # -------------------------
        # Create Test User
        # -------------------------
        self.test_user = User.objects.create_user(
            email="testuser@gmail.com",
            username="testuser",
            full_name="Test User",
            phone="9808123456",
            password="password123"
        )
        self.test_user.is_active = True
        self.test_user.is_superuser = True
        self.test_user.save()

        # -------------------------
        # Organization
        # -------------------------
        self.organization = Organization.objects.create(
            name="Organization 1",
            website="www.example.com",
            email="organization@example.com",
            phone="1234567890"
        )

        # -------------------------
        # Product Setup
        # -------------------------
        self.root_category = ProductCategory.objects.create(
            name="Root",
            organization=self.organization,
            parent=None
        )

        self.product_category = ProductCategory.objects.create(
            name="Laptop",
            organization=self.organization,
            parent=self.root_category
        )

        self.product_type = ProductType.objects.create(
            name="Electronics",
            organization=self.organization
        )

        self.product = Product.objects.create(
            name="Dell Laptop",
            product_type=self.product_type,
            product_sub_category=self.product_category,
            organization=self.organization
        )

        # -------------------------
        # Vendor
        # -------------------------
        self.vendor = Vendor.objects.create(
            name="Test Vendor",
            email="vendor@test.com",
            phone="9999999999",
            contact_person="John Doe"
        )

        # -------------------------
        # Location
        # -------------------------
        self.location = Location.objects.create(
            office_name="Head Office",
            organization=self.organization
        )

        # -------------------------
        # Asset Status
        # -------------------------
        self.asset_status = AssetStatus.objects.create(
            name="Available",
            organization=self.organization
        )

        # -------------------------
        # Existing Asset
        # -------------------------
        self.asset = Asset.objects.create(
            tag="ASSET001",
            name="Old Laptop",
            serial_no="SN12345",
            price=50000,
            product=self.product,
            vendor=self.vendor,
            location=self.location,
            asset_status=self.asset_status,
            organization=self.organization
        )
        print(self.asset,"IN ASSET SETUPPPPPPPPPPP")
        # -------------------------
        # Django Client Login
        # -------------------------
        self.client = Client()
        self.client.login(email="testuser@gmail.com", password="password123")

        self.session_cookie = self.client.cookies['sessionid']

        # -------------------------
        # Selenium Driver
        # -------------------------
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(10)

        self.driver.get(self.live_server_url)

        self.driver.add_cookie({
            "name": "sessionid",
            "value": self.session_cookie.value,
            "path": "/",
            "secure": False
        })

    def tearDown(self):
        self.driver.quit()

    # -------------------------
    # CREATE ASSET
    # -------------------------

    def login(self):
        self.driver.get(f"{self.live_server_url}/login/")
        username = self.driver.find_element(By.NAME, "username")
        password = self.driver.find_element(By.NAME, "password")

        username.send_keys("testuser")
        password.send_keys("testpassword")

        self.driver.find_element(By.XPATH, "//button[@type='submit']").click()

    def test_create_asset(self):
        self.driver.get(f"{self.live_server_url}/assets/list")
        add_asset_button = self.driver.find_element(
            By.XPATH, "//a[contains(text(),'Add Asset')]"
        )

        add_asset_button.click()
        
        time.sleep(2)

        self.driver.find_element(By.NAME, "tag").send_keys("ASSET002")
        self.driver.find_element(By.NAME, "name").send_keys("Test Laptop")
        self.driver.find_element(By.NAME, "serial_no").send_keys("SN98765")
        self.driver.find_element(By.NAME, "price").send_keys("60000")
        print(self.asset.id,"ASSET_IDDDDDDDDDDDDDDDDDDDDDD")
        self.driver.find_element(By.NAME, "description").send_keys(
            "Asset created via Selenium"
        )

        submit_button = self.driver.find_element(
            By.XPATH, "//button[@type='submit']"
        )

        submit_button.click()

        # time.sleep(2)

        print("✅ Asset Created")

        # self.assertIn("Old Laptop", self.driver.page_source)

    # -------------------------
    # UPDATE ASSET
    # -------------------------
    # def test_update_asset(self):

    #     print("asset_id:", self.asset.id)

    #     self.driver.get(
    #         f"{self.live_server_url}/assets/update/{self.asset.id}"
    #     )

    #     name_field = self.driver.find_element(By.NAME, "name")

    #     name_field.clear()
    #     name_field.send_keys("Updated Laptop")

    #     submit_button = self.driver.find_element(
    #         By.ID, "update-asset"
    #     )

    #     submit_button.click()

    #     time.sleep(2)

    #     print("✅ Asset Updated")

    #     self.assertIn("Updated Laptop", self.driver.page_source)
    def test_update_asset(self):
        # self.login()

        self.driver.get(
            f"{self.live_server_url}/assets/update-assets-details/{self.asset.id}"
        )

        wait = WebDriverWait(self.driver, 10)
        name_field = wait.until(
            EC.presence_of_element_located((By.NAME, "name"))
        )
        name_field.clear()
        name_field.send_keys("Updated Laptop")

        submit_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
        )
        submit_button.click()

        self.assertIn("Updated Laptop", self.driver.page_source)
    # -------------------------
    # DELETE ASSET
    # -------------------------
    def test_delete_asset(self):
        print("asset_id:", self.asset.id)
        time.sleep(2)
        self.driver.get(f"{self.live_server_url}/assets/delete/{self.asset.id}")
        # Discover all buttons on the page
        # buttons = self.driver.find_elements(By.TAG_NAME, "button")
        # print(f"Total buttons found: {len(buttons)}")
        # for i, btn in enumerate(buttons):
        #     try:
        #         print(
        #             f"{i} -> TEXT: '{btn.text}' | "
        #             f"ID: {btn.get_attribute('id')} | "
        #             f"CLASS: {btn.get_attribute('class')} | "
        #             f"TYPE: {btn.get_attribute('type')}"
        #         )
        #     except:
        #         pass
        # # After identifying the correct button, you can use its selector
        # delete_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        # delete_button.click()
        time.sleep(2)
        print("✅ Asset Deleted")
        self.assertNotIn("Old Laptop", self.driver.page_source)