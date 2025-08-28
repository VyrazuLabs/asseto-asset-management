from django.test import TestCase
from dashboard.models import Organization,Address,Location,ProductType,ProductCategory,Department
from vendors.models import Vendor
from products.models import Product
from .models import Asset
# Create your tests here.
class Asseto_test(TestCase):
    def setUp(self):
        user_address=Address.objects.create(
            address_line_one = "Address line 1",
            address_line_two = "Address line 2",
            country = "India",
            state="West Bengal",
            city = "Kolkata",
            pin_code = "700018",
        )
        user_organization = Organization.objects.create(
            name="Organization 1",
            website="asseto.com",
            phone="1234567890",
            email="asseto@asseto.com",
            currency="INR",
            date_format="dd-mm-yyyy",
            logo = "logo.png"
        )
        user_vendor=Vendor.objects.create(
            name = "Vendor 1",
            email = "vendor1@asseto.com",
            phone = "7896321454",
            contact_person = "Person 1",
            designation = "Designation 1",
            gstin_number = "1234567890",
            description = "Description 1",
            address= user_address,
            organization = user_organization
        )
        product_category=ProductCategory.objects.create(
            name="Category 1",
            organization=user_organization,
        )
        product_type=ProductType.objects.create(
            name="Type 1",
            organization=user_organization,
        )
        user_product=Product.objects.create(
            name = "Product 1",
            product_picture = "test.jpg",
            manufacturer = "Manufacturer 1",
            description = "Description 1",
            product_category = product_category,
            product_type = product_type,
            organization = user_organization
        )
        user_location=Location.objects.create(
            office_name = "Office 1",
            address = user_address,
            contact_person_name = "Person 1",
            contact_person_email = "person1@asseto.com",
            contact_person_phone = "1234567890",
            organization = user_organization,
        )
        self.asset=Asset.objects.create(
            name = "Asset 1",
            serial_no = "1234567890",
            description = "Description 1",
            location = user_location,
            organization = user_organization,
            product=user_product,
            vendor=user_vendor,
            price = 1000.00,
            purchase_date = "2020-01-01",
            warranty_expiry_date = "2021-01-01",
            purchase_type = "Warranty",
            is_assigned = False,
        )

    def test_asset(self):
        asset = Asset.objects.get(name="Asset 1")
        self.assertEqual(asset.name, "Asset 1")
        self.assertEqual(asset.serial_no, "1234567890")
        self.assertEqual(asset.description, "Description 1")
        self.assertEqual(asset.price, 1000.00)
        # self.assertEqual(asset.purchase_date, "2020-01-01")
        # self.assertEqual(asset.warranty_expiry_date, "2021-01-01")
        self.assertEqual(asset.purchase_type, "Warranty")
        self.assertEqual(asset.is_assigned, False)
        self.assertEqual(asset.location.office_name, "Office 1")
        self.assertEqual(asset.location.address.address_line_one, "Address line 1")
        self.assertEqual(asset.location.address.address_line_two, "Address line 2")
        self.assertEqual(asset.location.address.country, "India")
        self.assertEqual(asset.location.address.state, "West Bengal")
        self.assertEqual(asset.location.address.city, "Kolkata")
        self.assertEqual(asset.organization.name, "Organization 1")
        self.assertEqual(asset.location.contact_person_name, "Person 1")
        self.assertEqual(asset.location.contact_person_email, "person1@asseto.com")
        self.assertEqual(asset.location.contact_person_phone, "1234567890")
        self.assertEqual(asset.product.name, "Product 1")
        self.assertEqual(asset.product.product_picture, "test.jpg")
        self.assertEqual(asset.product.manufacturer, "Manufacturer 1")
        self.assertEqual(asset.product.description, "Description 1")
        self.assertEqual(asset.product.product_category.name, "Category 1")
        self.assertEqual(asset.product.product_type.name, "Type 1")
        self.assertEqual(asset.vendor.email, "vendor1@asseto.com")
        self.assertEqual(asset.vendor.name, "Vendor 1")
        self.assertEqual(asset.vendor.phone, "7896321454")
        self.assertEqual(asset.vendor.contact_person, "Person 1")
        self.assertEqual(asset.vendor.designation, "Designation 1")
        self.assertEqual(asset.vendor.gstin_number, "1234567890")
        self.assertEqual(asset.vendor.description, "Description 1")


    def edit_asset(self):
        self.asset.name = "Asset 2"
        self.asset.serial_no = "1234567892"
        self.asset.description = "Description 2"
        self.asset.location.office_name = "Office 2"
        self.asset.organization.name = "Organization 2"
        self.asset.organization.website = "asseto2.com"
        self.asset.organization.phone = "1234567892"
        self.asset.organization.email = "asseto@asseto2.com"
        self.asset.organization.currency = "INR"
        self.asset.organization.date_format = "dd-mm-yyyy"
        self.asset.organization.logo = "logo2.png"
        self.asset.product.name = "Product 2"
        self.asset.product.product_picture = "test2.jpg"
        self.asset.product.manufacturer = "Manufacturer 2"
        self.asset.product.description = "Description 2"
        self.asset.product.product_category.name = "Category 2"
        self.asset.product.product_type.name = "Type 2"
        self.asset.vendor.name = "Vendor 2"
        self.asset.vendor.email = "vendor2@asseto.com"
        self.asset.vendor.phone = "7896321452"
        self.asset.vendor.contact_person = "Person 2"
        self.asset.vendor.designation = "Designation 2"
        self.asset.vendor.gstin_number = "1234567892"
        self.asset.vendor.description = "Description 2"
        self.asset.price = 1002.00
        self.asset.purchase_date = "2020-01-02"
        self.asset.warranty_expiry_date = "2021-01-02"
        self.asset.purchase_type = "Warranty"
        self.asset.is_assigned = False
        self.asset.save()

        self.assertEqual(self.asset.name, "Asset 2")
        self.assertEqual(self.asset.serial_no, "1234567892")
        self.assertEqual(self.asset.description, "Description 2")
        self.assertEqual(self.asset.location.office_name, "Office 2")
        self.assertEqual(self.asset.organization.name, "Organization 2")
        self.assertEqual(self.asset.organization.website, "asseto2.com")
        self.assertEqual(self.asset.organization.phone, "1234567892")
        self.assertEqual(self.asset.organization.email, "asseto@asseto2.com")
        self.assertEqual(self.asset.organization.currency, "INR")
        self.assertEqual(self.asset.organization.date_format, "dd-mm-yyyy")
        self.assertEqual(self.asset.organization.logo, "logo2.png")
        self.assertEqual(self.asset.location.contact_person_name, "Person 2")
        self.assertEqual(self.asset.location.contact_person_email, "person2@asseto.com")
        self.assertEqual(self.asset.location.contact_person_phone, "1234567892")
        self.assertEqual(self.asset.product.name, "Product 2")
        self.assertEqual(self.asset.product.product_picture, "test2.jpg")
        self.assertEqual(self.asset.product.manufacturer, "Manufacturer 2")
        self.assertEqual(self.asset.product.description, "Description 2")
        self.assertEqual(self.asset.product.product_category.name, "Category 2")
        self.assertEqual(self.asset.product.product_type.name, "Type 2")
        self.assertEqual(self.asset.vendor.name, "Vendor 2")
        self.assertEqual(self.asset.vendor.email, "vendor2@asseto.com")
        self.assertEqual(self.asset.vendor.phone, "7896321452")
        self.assertEqual(self.asset.vendor.contact_person, "Person 2")
        self.assertEqual(self.asset.vendor.designation, "Designation 2")    
        self.assertEqual(self.asset.vendor.gstin_number, "1234567892")
        self.assertEqual(self.asset.vendor.description, "Description 2")
        self.assertEqual(self.asset.price, 1002.00)
        self.assertEqual(self.asset.purchase_date, "2020-01-02")
        self.assertEqual(self.asset.warranty_expiry_date, "2021-01-02")
        self.assertEqual(self.asset.purchase_type, "Warranty")
        self.assertEqual(self.asset.is_assigned, False)


    def delete_asset(self):
        self.asset.delete()
        with self.assertRaises(Asset.DoesNotExist):
            Asset.objects.get(id=self.asset.id)
        location=Location.objects.get(id=self.asset.location.id)
        organization=Organization.objects.get(id=self.asset.organization.id)
        vendor=Vendor.objects.get(id=self.asset.vendor.id)
        product=Product.objects.get(id=self.asset.product.id)
        self.assertIsNotNone(location)
        self.assertIsNotNone(organization)
        self.assertIsNotNone(vendor)
        self.assertIsNotNone(product)
