from django.test import TestCase
from .models import Product
from dashboard.models import ProductCategory,ProductType,Organization
# Create your tests here.

class Asseto_test(TestCase):
    def setUp(self):
        self.user_organization = Organization.objects.create(
            name="Organization 1",
            website="asseto.com",
            phone="1234567890",
            email="asseto@asseto.com",
            currency="INR",
            date_format="dd-mm-yyyy",
            logo = "logo.png"
        )
        self.product_category=ProductCategory.objects.create(
            name="Category 1",
            organization=self.user_organization,
        )
        self.product_type=ProductType.objects.create(
            name="Type 1",
            organization=self.user_organization,
        )
        self.product=Product.objects.create(
            name = "Product 1",
            product_picture = "test.jpg",
            manufacturer = "Manufacturer 1",
            description = "Description 1",
            product_category = self.product_category,
            product_type = self.product_type,
            organization = self.user_organization
        )
        self.updated_product_type=ProductType.objects.create(
            name="Type 2",
            organization=self.user_organization,
        )
        self.updated_product_category=ProductCategory.objects.create(
            name="Category 2",
            organization=self.user_organization,
        )
        self.updated_product=Product.objects.create(
            name = "Product 2",
            product_picture = "test2.jpg",
            manufacturer = "Manufacturer 2",
            description = "Description 2",
            product_category = self.updated_product_category,
            product_type = self.updated_product_type,
            organization = self.user_organization
        )

    def test_product(self):
        # self.assertEqual(product.name, "Vendor 1")
        # self.assertEqual(address.email, "vendor1@asseto.com")
        self.assertEqual(self.product.product_picture,"test.jpg")
        self.assertEqual(self.product.manufacturer,"Manufacturer 1")
        self.assertEqual(self.product.description, "Description 1")
        self.assertEqual(self.product.product_category.name, "Category 1")
        self.assertEqual(self.product.product_type.name, "Type 1")
        self.assertEqual(self.product.organization.name, "Organization 1")
        # self.assertEqual(self.product.product_category.name, " ")
        # self.assertEqual(self.product.product_type.name, "Type 1")
        # self.assertEqual(self.product.product_type.name, "Type 1")
        # self.assertEqual(self.product.product_type.name, "Type 1")
        # self.assertEqual(self.product.product_type.name, "Type 1")
# class DeleteProduct(TestCase):
#     def setUp(self):
#         user_organization = Organization.objects.create(
#             name="Organization 1",
#             website="asseto.com",
#             phone="1234567890",
#             email="asseto@asseto.com",
#             currency="INR",
#             date_format="dd-mm-yyyy",
#             logo = "logo.png"
#         )
#         product_category=ProductCategory.objects.create(
#             name="Category 1",
#             organization=user_organization,
#         )
#         product_type=ProductType.objects.create(
#             name="Type 1",
#             organization=user_organization,
#         )
#         self.product=Product.objects.create(
#             name = "Product 1",
#             product_picture = "test.jpg",
#             manufacturer = "Manufacturer 1",
#             description = "Description 1",
#             product_category = product_category,
#             product_type = product_type,
#             organization = user_organization
#         )
#         self.product.save()
    def test_edit_porduct(self):
        self.product.name='Product 2'
        self.product.product_picture='test2.jpg'
        self.product.manufacturer="Manufacturer 2"
        self.product.description="Description 2"
        self.product.product_category.name="Category 2"
        self.product.product_type.name="Type 2"

        self.product.save()

        self.assertEqual(self.product.name,'Product 2')
        self.assertEqual(self.product.product_picture,'test2.jpg')
        self.assertEqual(self.product.manufacturer,"Manufacturer 2")
        self.assertEqual(self.product.description,"Description 2")
        self.assertEqual(self.product.product_category.name,"Category 2")
        self.assertEqual(self.product.product_type.name,"Type 2")     
    
    def del_product(self):
        self.product.delete()

        with self.assertRaises(Product.DoesNotExist):
            Product.objects.get(id=self.product.id)

        product_category=ProductCategory.objects.get(id=self.product.product_category.id)
        product_type=ProductType.objects.get(id=self.product.product_type.id)
        organization = Organization.objects.get(id=self.product.organization.id)
        self.assertIsNotNone(product_category)
        self.assertIsNotNone(product_type)
        self.assertIsNotNone(organization)
