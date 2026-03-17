from django.test import TestCase
from dashboard.models import LicenseType
from license.models import License
from vendors.models import Vendor
# class TestLicense(TestCase):
#     def setUp(self):
#         create_license_type=LicenseType.objects.create(name='Test License type')
#         create_vendor=Vendor.objects.create(name='TestVendor')
#         License.objects.create(
#             name='Test License',
#             license_type=create_license_type,
#             vendor=create_vendor,
#             seats=12,
#             start_date="01/01/2026",
#             expiry_date="01/01/2027",
#             key="98798qw7d9wddDWD7984",
#             notes="Test Description",
#             is_assigned=True
#         )
    
#     def test_license_list(self):
#         get_license=License.objects.get(name='Test License')
#         self.assertEqual(get_license.name,'Test License')
#         self.assertEqual(get_license.license_type.name,'Test License type')
#         self.assertEqual(get_license.vendor.name,"TestVendor")
#         self.assertEqual(get_license.seats,12)
#         self.assertEqual(get_license.start_date,"01/01/2026")
#         self.assertEqual(get_license.expiry_date,"01/01/2027")
#         self.assertEqual(get_license.key,"98798qw7d9wddDWD7984")
#         self.assertEqual(get_license.notes,"Test Description")

#     def test_edit_liense(self):

#         self.get_license='Test License2'
#         self.get_license.license_type.name,'Test License type'
#         self.assertEqualget_license.vendor.name,"TestVendor"
#         self.assertEqualget_license.seats,12
#         self.assertEqualget_license.start_date,"01/01/2026"
#         self.assertEqualget_license.expiry_date,"01/01/2027"
#         self.assertEqualget_license.key,"98798qw7d9wddDWD7984"
#         self.assertEqualget_license.notes,"Test Description"

#         get_license=License.objects.get(name='Test License')

from django.test import TestCase
from django.contrib.auth import get_user_model
from dashboard.models import Organization, Address
from vendors.models import Vendor
from license.models import License, LicenseType, AssignLicense

User = get_user_model()


class LicenseTest(TestCase):

    def setUp(self):
        # User
        self.user = User.objects.create_user(
            full_name="Test User",
            phone="9433622983",
            username="testuser",
            email="testuser@test.com",
            password="password123"
        )

        # Address
        self.address = Address.objects.create(
            address_line_one="Address line 1",
            address_line_two="Address line 2",
            country="India",
            state="West Bengal",
            city="Kolkata",
            pin_code="700018",
        )

        # Organization
        self.organization = Organization.objects.create(
            name="Organization 1",
            website="asseto.com",
            phone="1234567890",
            email="asseto@asseto.com",
            currency="INR",
            date_format="dd-mm-yyyy",
            logo="logo.png"
        )

        # Vendor
        self.vendor = Vendor.objects.create(
            name="Vendor 1",
            email="vendor1@asseto.com",
            phone="7896321454",
            contact_person="Person 1",
            designation="Designation 1",
            gstin_number="1234567890",
            description="Description 1",
            address=self.address,
            organization=self.organization
        )

        # License Type
        self.license_type = LicenseType.objects.create(
            name="Software License"
        )

        # License
        self.license = License.objects.create(
            name="License 1",
            license_type=self.license_type,
            vendor=self.vendor,
            seats=10,
            start_date="2023-01-01",
            expiry_date="2024-01-01",
            key="ABC123XYZ",
            notes="Initial License Notes",
            is_assigned=False
        )

        # Assign License
        self.assign_license = AssignLicense.objects.create(
            license=self.license,
            user=self.user,
            notes="Assigned to testuser"
        )

    # ✅ Test Create License
    def test_create_license(self):
        license = License.objects.get(id=self.license.id)

        self.assertEqual(license.name, "License 1")
        self.assertEqual(license.license_type.name, "Software License")
        self.assertEqual(license.vendor.name, "Vendor 1")
        self.assertEqual(license.seats, 10)
        self.assertEqual(str(license.start_date), "2023-01-01")
        self.assertEqual(str(license.expiry_date), "2024-01-01")
        self.assertEqual(license.key, "ABC123XYZ")
        self.assertEqual(license.notes, "Initial License Notes")
        self.assertEqual(license.is_assigned, False)

    # ✅ Test Edit License
    def test_edit_license(self):
        self.license.name = "License 2"
        self.license.seats = 20
        self.license.key = "NEWKEY123"
        self.license.notes = "Updated Notes"
        self.license.is_assigned = True
        self.license.save()

        license = License.objects.get(id=self.license.id)

        self.assertEqual(license.name, "License 2")
        self.assertEqual(license.seats, 20)
        self.assertEqual(license.key, "NEWKEY123")
        self.assertEqual(license.notes, "Updated Notes")
        self.assertEqual(license.is_assigned, True)

    # ✅ Test Delete License
    def test_delete_license(self):
        license_id = self.license.id
        self.license.delete()

        with self.assertRaises(License.DoesNotExist):
            License.objects.get(id=license_id)

    # ✅ Test AssignLicense Creation
    def test_assign_license(self):
        assign = AssignLicense.objects.get(id=self.assign_license.id)

        self.assertEqual(assign.license.name, "License 1")
        self.assertEqual(assign.user.username, "testuser")
        self.assertEqual(assign.notes, "Assigned to testuser")
        self.assertIsNotNone(assign.assigned_date)

    # ✅ Test Cascade: Delete License → AssignLicense Deleted
    def test_delete_license_deletes_assignment(self):
        assign_id = self.assign_license.id
        self.license.delete()

        with self.assertRaises(AssignLicense.DoesNotExist):
            AssignLicense.objects.get(id=assign_id)

    # ✅ Test Cascade: Delete User → AssignLicense Deleted
    def test_delete_user_deletes_assignment(self):
        assign_id = self.assign_license.id
        self.user.delete()

        with self.assertRaises(AssignLicense.DoesNotExist):
            AssignLicense.objects.get(id=assign_id)
