from django.test import TestCase
from .models import Vendor
from dashboard.models import Address,Organization
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
        self.vendor=Vendor.objects.create(
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
        self.edit_address=Address.objects.create(
            address_line_one = "Address line 12",
            address_line_two = "Address line 22",
            country = "Pakistan",
            state="Punjab",
            city = "Karachi",
            pin_code = "600069",
        )
        self.edit_organization=Organization.objects.create(
            name="Organization 112",
            website="asseto1.com",
            phone="1234567899",
            email="asseto@asseto1.com",
            currency="PAK",
            date_format="dd-mm-yyyy",
            logo = "logo2.png"
        )


    def test_vendor(self):
        self.vendor = Vendor.objects.get(email="vendor1@asseto.com")
        self.assertEqual(self.vendor.name, "Vendor 1")
        self.assertEqual(self.vendor.phone, "7896321454")
        self.assertEqual(self.vendor.contact_person, "Person 1")
        self.assertEqual(self.vendor.designation, "Designation 1")
        self.assertEqual(self.vendor.gstin_number, "1234567890")
        self.assertEqual(self.vendor.description, "Description 1")
        self.assertEqual(self.vendor.address.address_line_one,"Address line 1")
        self.assertEqual(self.vendor.organization.name, "Organization 1")

# class EditVendorTest(TestCase):
    # def setUp(self):
    #     self.vendor = Vendor.objects.create(name='Vendor 1', email='vendor1@example.com', phone='1234567890')

    def test_edit_vendor(self):
        # Edit the vendor
        self.vendor.name = 'New Name'
        self.vendor.email = 'newemail@example.com'
        self.vendor.phone = '1112223333'
        self.vendor.contact_person='Arpan'
        self.vendor.designation='Designation 1'
        self.vendor.gstin_number='GST123'
        self.vendor.description="Desc 1"
        self.vendor.address=self.edit_address
        self.vendor.organization=self.edit_organization

        self.vendor.save()

        # Check that the changes were saved correctly
        self.assertEqual(self.vendor.name, 'New Name')
        self.assertEqual(self.vendor.email, 'newemail@example.com')
        self.assertEqual(self.vendor.phone, '1112223333')
        self.assertEqual(self.vendor.contact_person, 'Arpan')
        self.assertEqual(self.vendor.designation, 'Designation 1')
        self.assertEqual(self.vendor.gstin_number, 'GST123')
        self.assertEqual(self.vendor.description, 'Desc 1')
        self.assertEqual(self.vendor.address.address_line_one, 'Address line 12')
        self.assertEqual(self.vendor.address.address_line_two, 'Address line 22')
        self.assertEqual(self.vendor.address.country, 'Pakistan')
        self.assertEqual(self.vendor.address.state, 'Punjab')
        self.assertEqual(self.vendor.address.city, 'Karachi')
        self.assertEqual(self.vendor.address.pin_code, '600069')
        self.assertEqual(self.vendor.organization.name,"Organization 112")
        self.assertEqual(self.vendor.organization.website,"asseto1.com")
        self.assertEqual(self.vendor.organization.phone,"1234567899")
        self.assertEqual(self.vendor.organization.email,"asseto@asseto1.com")
        self.assertEqual(self.vendor.organization.currency,"PAK")
        self.assertEqual(self.vendor.organization.date_format,"dd-mm-yyyy")
        self.assertEqual(self.vendor.organization.logo,"logo2.png")

    # def test_edit_vendor_with_same_info(self):
    #     # Edit the vendor with same information
    #     self.vendor.name = 'Vendor 1'
    #     self.vendor.email = 'vendor1@example.com'
    #     self.vendor.phone = '1234567890'

    #     self.vendor.save()

    #     # Check that the changes were saved correctly
    #     self.assertEqual(self.vendor.name, 'Vendor 1')
    #     self.assertEqual(self.vendor.email, 'vendor1@example.com')
    #     self.assertEqual(self.vendor.phone, '1234567890')

    # def test_edit_vendor_with_required_fields(self):
    #     # Edit the vendor with required fields (name)
    #     self.vendor.name = 'New Name'

    #     self.vendor.save()

    #     # Check that the changes were saved correctly
    #     self.assertEqual(self.vendor.name, 'New Name')

# class TestVendorDeletion(TestCase):
    # def setUp(self):
    #     # Create a test vendor object
    #     user_address=Address.objects.create(
    #         address_line_one = "Address line 1",
    #         address_line_two = "Address line 2",
    #         country = "India",
    #         state="West Bengal",
    #         city = "Kolkata",
    #         pin_code = "700018",
    #     )
    #     user_organization = Organization.objects.create(
    #         name="Organization 1",
    #         website="asseto.com",
    #         phone="1234567890",
    #         email="asseto@asseto.com",
    #         currency="INR",
    #         date_format="dd-mm-yyyy",
    #         logo = "logo.png"
    #     )
    #     self.vendor = Vendor(name='Test Vendor', email='test@example.com', phone='7896541230',contact_person='person',
    #                         designation='developer',gstin_number='21321',description='description 1',
    #                         address=user_address,organization=user_organization)
    #     self.vendor.save()
    def test_delete_vendor(self):
        # Try to delete the vendor object
        self.vendor.delete()
        
        # Check if the vendor object is deleted from the database
        with self.assertRaises(Vendor.DoesNotExist):
            Vendor.objects.get(id=self.vendor.id)

        # Check if the address and organization objects are not affected
        address = Address.objects.get(id=self.vendor.address.id)
        organization = Organization.objects.get(id=self.vendor.organization.id)
        self.assertIsNotNone(address)
        self.assertIsNotNone(organization)

