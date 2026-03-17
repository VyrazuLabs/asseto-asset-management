# from django.test import LiveServerTestCase
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from authentication.models import User
# from products.models import Product
# import time


# class ProductTest(LiveServerTestCase):

#     def setUp(self):
#         # Create test user
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

#     # def tearDown(self):
#     #     self.driver.quit()
#     def tearDown(self):
#         self.driver.quit()

#     def test_login(self):
#         self.driver.get("http://10.0.0.91:9000/")

#         email_input = self.driver.find_element(By.NAME, "email")
#         password_input = self.driver.find_element(By.NAME, "password")
#         login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")

#         email_input.send_keys("testusergmail.com")
#         password_input.send_keys("password123")
#         login_button.click()
#     def test_create_product(self):
#         # print("Creating Products")
#         # # Open login page
#         # self.driver.get("http://10.0.0.91:9000/")

#         # # Login
#         # email_input = self.driver.find_element(By.NAME, "email")
#         # password_input = self.driver.find_element(By.NAME, "password")
#         # login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")

#         # email_input.send_keys("testuser@gmail.com")
#         # password_input.send_keys("password123")
#         # login_button.click()
#         print("Login Done")
#         time.sleep(2)

#         # Go to product page
#         self.driver.get("http://10.0.0.91:9000/products/list")

#         # Click Add Product button
#         add_product_button = self.driver.find_element(By.XPATH, "//a[contains(text(),'Add Product')]")
#         add_product_button.click()

#         # Fill product form
#         name_input = self.driver.find_element(By.NAME, "name")
#         product_type = self.driver.find_element(By.NAME, "product_type")
#         product_category = self.driver.find_element(By.NAME, "product_category")
#         description_input = self.driver.find_element(By.NAME, "description")

#         name_input.send_keys("Test Laptop")
#         product_type.send_keys("Dell")
#         product_category.send_keys("Latitude 5400")
#         description_input.send_keys("Test Product Created By Selenium")
#         # Submit form
#         submit_button = self.driver.find_element(By.ID, "//button[@type='submit']")
#         submit_button.click()
#         print("Added Product")
#         time.sleep(2)

#         # Verify product created
#         self.assertIn("Test Laptop", self.driver.page_source)

# #     from selenium.webdriver.common.by import By
# # from .base import BaseTestCase


# # class ProductEditTest(BaseTestCase):
#     # def test_edit_product(self):
#     #     print("Editing Products---------")
#     #     # self.login()

#     #     self.driver.get("http://127.0.0.1:9000//products/update/1")

#     #     # edit_button = self.driver.find_element(By.XPATH, "//a[contains(text(),'Edit')]")
#     #     edit_button = self.driver.find_element(By.ID, "edit-product-btn")
#     #     edit_button.click()

#     #     name_field = self.driver.find_element(By.NAME, "name")
#     #     name_field.clear()
#     #     name_field.send_keys("Updated Laptop")

#     #     self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
#     #     print("Updated Product")
#     #     self.assertIn("Updated Laptop", self.driver.page_source)

from django.test import LiveServerTestCase, Client
from selenium import webdriver
from selenium.webdriver.common.by import By
from authentication.models import User
from products.models import Product
from dashboard.models import ProductCategory, ProductType,Organization
import time


class ProductTest(LiveServerTestCase):

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
        self.organization=Organization.objects.create(
            name="Organization 1",
            website="www.example.com",
            email="organization@example.com",
            phone="1234567890"
        )
        self.root_category = ProductCategory.objects.create(
            name="Root",
            organization=self.organization,
            parent=None
        )
        self.product_category=ProductCategory.objects.create(
            name="Product Category 1",
            organization=self.organization,
            parent=self.root_category
        )
        self.product_type=ProductType.objects.create(
            name="Product Type 1",
            organization=self.organization,
        )
        # To do update/delete
        self.product = Product.objects.create(
            name="Old Laptop",
            product_type=self.product_type,
            product_sub_category=self.product_category,
            description="Old Product",
        )  
        self.product.save()
        # Django test client
        self.client = Client()

        # Login using Django test client
        self.client.login(email="testuser@gmail.com", password="password123")

        # Get session cookie
        self.session_cookie = self.client.cookies['sessionid']

        # Start selenium driver
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(10)

        # Open live server to set domain
        self.driver.get(self.live_server_url)

        # Inject session cookie into browser
        self.driver.add_cookie({
            'name': 'sessionid',
            'value': self.session_cookie.value,
            'path': '/',
            'secure': False
        })

    def tearDown(self):
        self.driver.quit()

    def test_create_product(self):

        # Directly open protected page (login bypassed)
        self.driver.get(f"{self.live_server_url}/products/list")

        # Click Add Product button
        add_product_button = self.driver.find_element(
            By.XPATH, "//a[contains(text(),'Add Product')]"
        )
        add_product_button.click()

        # Fill product form
        name_input = self.driver.find_element(By.NAME, "name")
        product_type = self.driver.find_element(By.NAME, "product_type")
        product_category = self.driver.find_element(By.NAME, "product_category")
        description_input = self.driver.find_element(By.NAME, "description")

        name_input.send_keys("Test Laptop")
        product_type.send_keys("Dell")
        product_category.send_keys("Latitude 5400")
        description_input.send_keys("Test Product Created By Selenium")
        print("✅ Product Created")
        # Submit form
        submit_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        submit_button.click()

        time.sleep(2)

        # Verify product created
        self.assertIn("Test Laptop", self.driver.page_source)

    def test_update_product(self):
        print("prod_id",self.product.id)
        self.driver.get(
            f"{self.live_server_url}/products/update/{self.product.id}"
        )

        name_field = self.driver.find_element(By.NAME, "name")
        name_field.clear()
        name_field.send_keys("Updated Laptop")

        submit = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        submit.click()

        time.sleep(2)
        print("Product Updated")
        self.assertIn("Updated Laptop", self.driver.page_source)


    # -------------------------------
    # DELETE PRODUCT TEST
    # -------------------------------
    def test_delete_product(self):
        print("prod_id",self.product.id)
        self.driver.get(
            f"{self.live_server_url}/products/list"
        )

        # delete_button = self.driver.find_element(
        #     By.XPATH, f"//a[contains(@href,'/products/delete/{self.product.id}')]"
        # )
        delete_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        delete_button.click()

        time.sleep(2)   
        print("Product Deleted")
        # self.assertNotIn("New Laptop", self.driver.page_source)