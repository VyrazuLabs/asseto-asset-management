from django.test import TestCase
from .models import Address,Location,Organization,ProductType,ProductCategory,Department
# Create your tests here.

class Asseto_test_address(TestCase):
    def setUp(self):
        Address.objects.create(
            country = "India",
            state = "Rajasthan",
            address_line_one = "testline 1",
            address_line_two = "testline 2",
            city = "Jaipur",
            pin_code = "302001"
        )

    def test_product_category(self):
        address = Address.objects.get(country="India")
        self.assertEqual(address.state, "Rajasthan")
class Asseto_test_location(TestCase):
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
        self.user_address=Address.objects.create(
            address_line_one = "Address line 1",
            address_line_two = "Address line 2",
            country = "India",
            state="West Bengal",
            city = "Kolkata",
            pin_code = "700018",
        )
        self.location=Location.objects.create(
            office_name = "Office 1",
            address = self.user_address,
            contact_person_name = "Person 1",
            contact_person_email = "person1@asseto.com",
            contact_person_phone = "1234567890",
            organization = self.user_organization,
        )
        self.location.save()

        self.edit_address=Address.objects.create(
        address_line_one = "Address line 1",
        address_line_two = "Address line 2",
        country = "India",
        state="West Bengal",
        city = "Kolkata",
        pin_code = "700018",
        )
        self.edit_organization = Organization.objects.create(name='Organization 1', website='www.example.com', email='organization@example.com', phone='1234567890')
        self.edit_location = Location.objects.create(
            office_name="Test Office",
            contact_person_name="John Doe",
            contact_person_email="johndoe@example.com",
            contact_person_phone="1234567890",
            address=self.edit_address,
            organization=self.edit_organization,
        )
        self.product_category=ProductCategory.objects.create(
            name="Category 1",
            organization=self.edit_organization,
        )
        self.product_type=ProductType.objects.create(
            name="Type 1",
            organization=self.edit_organization
        )

    def test_location(self):
        # location = Location.objects.get(office_name="Office 1")
        self.assertEqual(self.location.contact_person_name, "Person 1")
        self.assertEqual(self.location.contact_person_email, "person1@asseto.com")
        self.assertEqual(self.location.contact_person_phone, "1234567890")
        self.assertEqual(self.location.office_name,'Office 1')
        self.assertEqual(self.location.address.address_line_one,'Address line 1')
        self.assertEqual(self.location.address.address_line_two,'Address line 2')
        self.assertEqual(self.location.address.country,'India')
        self.assertEqual(self.location.address.state,'West Bengal')
        self.assertEqual(self.location.address.city,'Kolkata')
        self.assertEqual(self.location.address.pin_code,'700018')

class Asseto_test_producttype(TestCase):
    def setUp(self):
        user_organization = Organization.objects.create(
            name="Organization 1",
            website="asseto.com",
            phone="1234567890",
            email="asseto@asseto.com",
            currency="INR",
            date_format="dd-mm-yyyy",
            logo = "logo.png"
        )
        ProductType.objects.create(
            name="Type 1",
            organization=user_organization,
        )

    def test_product_type(self):
        type = ProductType.objects.get(name="Type 1")
        self.assertEqual(type.name, "Type 1")
        # self.assertEqual(type.organization.name, "Organization 1")

class Asseto_test_four(TestCase):
    def setUp(self):
        user_organization = Organization.objects.create(
            name="Organization 1",
            website="asseto.com",
            phone="1234567890",
            email="asseto@asseto.com",
            currency="INR",
            date_format="dd-mm-yyyy",
            logo = "logo.png"
        )
        ProductCategory.objects.create(
            name="Category 1",
            organization=user_organization,
        )

    def test_product_category(self):
        category = ProductCategory.objects.get(name="Category 1")
        self.assertEqual(category.name, "Category 1")
        self.assertEqual(category.organization.name, "Organization 1")

class Asseto_test_five(TestCase):
    def setUp(self):
        user_organization = Organization.objects.create(
            name="Organization 1",
            website="asseto.com",
            phone="1234567890",
            email="asseto@asseto.com",
            currency="INR",
            date_format="dd-mm-yyyy",
            logo = "logo.png"
        )
        Department.objects.create(
            name="Department 1",
            organization=user_organization,
            contact_person_name = "Person 1",
            contact_person_email = "person1@asseto.com",
            contact_person_phone = "1234567890",
        )

    def test_product_category(self):
        department = Department.objects.get(name="Department 1")
        self.assertEqual(department.name, "Department 1")
        self.assertEqual(department.organization.name, "Organization 1")
        self.assertEqual(department.contact_person_name, "Person 1")
        self.assertEqual(department.contact_person_email, "person1@asseto.com")
        self.assertEqual(department.contact_person_phone, "1234567890")

class EditDepartmentTest(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name='Organization 1', website='www.example.com', email='organization@example.com', phone='1234567890')
        self.department = Department.objects.create(name='Department 1', contact_person_name='Contact Person 1', contact_person_email='contactperson1@example.com', 
contact_person_phone='1112223333', organization=self.organization)

    def test_edit_department(self):
        # Edit the department
        self.department.name = 'New Department'
        self.department.contact_person_name = 'New Contact Person'
        self.department.contact_person_email = 'newcontactperson@example.com'
        self.department.contact_person_phone = '4445556666'

        self.department.save()

        # Check that the changes were saved correctly
        self.assertEqual(self.department.name, 'New Department')
        self.assertEqual(self.department.contact_person_name, 'New Contact Person')
        self.assertEqual(self.department.contact_person_email, 'newcontactperson@example.com')
        self.assertEqual(self.department.contact_person_phone, '4445556666')

    # def test_edit_department_with_same_info(self):
    #     # Edit the department with same information
    #     self.department.name = 'Department 1'
    #     self.department.contact_person_name = 'Contact Person 1'
    #     self.department.contact_person_email = 'contactperson1@example.com'
    #     self.department.contact_person_phone = '1112223333'

    #     self.department.save()

    #     # Check that the changes were saved correctly
    #     self.assertEqual(self.department.name, 'Department 1')
    #     self.assertEqual(self.department.contact_person_name, 'Contact Person 1')
    #     self.assertEqual(self.department.contact_person_email, 'contactperson1@example.com')
    #     self.assertEqual(self.department.contact_person_phone, '1112223333')

    def test_edit_department_organization(self):
        # Edit the organization of the department
        new_organization = Organization.objects.create(name='New Organization', website='www.newexample.com', email='neworganization@example.com', phone='5556667777')
        self.department.organization = new_organization
        self.department.save()

        # Check that the changes were saved correctly
        self.assertEqual(self.department.organization.name, 'New Organization')
        self.assertEqual(self.department.organization.website, 'www.newexample.com')
        self.assertEqual(self.department.organization.email, 'neworganization@example.com')
        self.assertEqual(self.department.organization.phone, '5556667777')

class EditProductTypeTest(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name='Organization 1', website='www.example.com', email='organization@example.com', phone='1234567890')
        self.product_type = ProductType.objects.create(name='Product Type 1', organization=self.organization)

    def test_edit_product_type(self):
        # Edit the product type
        self.product_type.name = 'New Product Type'
        self.product_type.save()

        # Check that the changes were saved correctly
        self.assertEqual(self.product_type.name, 'New Product Type')
    # def test_edit_product_type_with_same_info(self):
    #     # Edit the product type with same information
    #     self.product_type.name = 'Product Type 1'

    #     self.product_type.save()

    #     # Check that the changes were saved correctly
    #     self.assertEqual(self.product_type.name, 'Product Type 1')

class EditProductCategoryTest(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name='Organization 1',
                                                     website='www.example.com', email='organization@example.com', 
                                                     phone='1234567890')
        self.product_category = ProductCategory.objects.create(name='Product Category 1', organization=self.organization)

    def test_edit_product_category(self):
        self.product_category.name = 'New Product category'
        self.product_category.save()
        # Check that the changes were saved correctly
        self.assertEqual(self.product_category.name, 'New Product category')

    # def test_edit_product_type_with_same_info(self):
    #     # Edit the product type with same information
    #     self.product_category.name = 'Product Category 1'

    #     self.product_category.save()

    #     # Check that the changes were saved correctly
    #     self.assertEqual(self.product_category.name, 'Product Category 1')

class TestEditLocation(TestCase):
    def setUp(self):
        self.address=Address.objects.create(
            address_line_one = "Address line 1",
            address_line_two = "Address line 2",
            country = "India",
            state="West Bengal",
            city = "Kolkata",
            pin_code = "700018",
        )
        self.organization = Organization.objects.create(name='Organization 1', website='www.example.com', email='organization@example.com', phone='1234567890')
        self.location = Location.objects.create(
            office_name="Test Office",
            contact_person_name="John Doe",
            contact_person_email="johndoe@example.com",
            contact_person_phone="1234567890",
            address=self.address,
            organization=self.organization,
        )
        self.product_category=ProductCategory.objects.create(
            name="Category 1",
            organization=self.organization,
        )
        self.product_type=ProductType.objects.create(
            name="Type 1",
            organization=self.organization
        )

    # def test_edit_location_with_same_info(self):


    def test_edit_location(self):
        # Test editing the office name
        self.location.office_name = "New Office Name"
        self.location.contact_person_name = "Jane Doe"
        self.location.contact_person_email = "johndoe@example.com"  
        self.location.contact_person_phone = "9876543210"
        self.location.address.address_line_one = "New Address Line 1"
        self.location.address.address_line_two = "New Address Line 2"
        self.location.address.country = "New Country"
        self.location.address.state = "New State"
        self.location.address.city = "New City"
        self.location.address.pin_code = "123456"
        self.location.organization.name = "New Organization"
        self.location.organization.website = "www.newexample.com"
        self.location.organization.email = "neworganization@example.com"
        self.location.organization.phone = "5556667777"
        self.location.save()

        # Check that the changes were saved correctly
        self.assertEqual(self.location.office_name, "New Office Name")
        self.assertEqual(self.location.contact_person_name, "Jane Doe")
        self.assertEqual(self.location.contact_person_email, "johndoe@example.com")
        self.assertEqual(self.location.contact_person_phone, "9876543210")
        self.assertEqual(self.location.address.address_line_one, "New Address Line 1")
        self.assertEqual(self.location.address.address_line_two, "New Address Line 2")
        self.assertEqual(self.location.address.country, "New Country")
        self.assertEqual(self.location.address.state, "New State")
        self.assertEqual(self.location.address.city, "New City")
        self.assertEqual(self.location.address.pin_code, "123456")
        self.assertEqual(self.location.organization.name, "New Organization")
        self.assertEqual(self.location.organization.website, "www.newexample.com")
        self.assertEqual(self.location.organization.email, "neworganization@example.com")
        self.assertEqual(self.location.organization.phone, "5556667777")
    
    # def test_edit_location_invalid_data(self):
    #     # Test that editing with invalid data raises a ValidationError
    #     new_office_name = ""  # Empty string is not allowed
    #     with self.assertRaises(ValidationError):
    #         self.location.office_name = new_office_name
    #         self.location.save()
    def test_delete_location(self):
        self.location.delete()
        with self.assertRaises(Location.DoesNotExist):
            Location.objects.get(id=self.location.id)
        address=Address.objects.get(city=self.location.address.city)
        organization=Organization.objects.get(id=self.location.organization.id)
        self.assertIsNotNone(organization)
        self.assertIsNotNone(address)

    def test_delete_product_category(self):
        self.product_category.delete()
        organization=Organization.objects.get(id=self.product_category.organization.id)
        self.assertIsNotNone(organization)


    def test_delete_product_type(self):
        self.product_type.delete()
        organization=Organization.objects.get(id=self.product_type.organization.id)
        self.assertIsNotNone(organization)
