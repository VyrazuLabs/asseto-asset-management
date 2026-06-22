from django.test import TestCase
from django.contrib.auth import get_user_model
from dashboard.models import Organization, Address, Location, ProductType, ProductCategory
from vendors.models import Vendor
from products.models import Product
from assets.models import Asset
from audit.models import Audit

User = get_user_model()


class AuditTest(TestCase):

    def setUp(self):
        # Create User
        self.user = User.objects.create_user(
            full_name="Auditor 1",
            phone="9433622983",
            username="auditor",
            email="auditor@test.com",
            password="password123"
        )

        # Create Address
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

        # Product Category & Type
        self.category = ProductCategory.objects.create(
            name="Category 1",
            organization=self.organization,
        )

        self.type = ProductType.objects.create(
            name="Type 1",
            organization=self.organization,
        )

        # Product
        self.product = Product.objects.create(
            name="Product 1",
            product_picture="test.jpg",
            manufacturer="Manufacturer 1",
            description="Description 1",
            product_sub_category=self.category,
            product_type=self.type,
            organization=self.organization
        )

        # Location
        self.location = Location.objects.create(
            office_name="Office 1",
            address=self.address,
            contact_person_name="Person 1",
            contact_person_email="person1@asseto.com",
            contact_person_phone="1234567890",
            organization=self.organization,
        )

        # Asset
        self.asset = Asset.objects.create(
            name="Asset 1",
            serial_no="1234567890",
            description="Description 1",
            location=self.location,
            organization=self.organization,
            product=self.product,
            vendor=self.vendor,
            price=1000.00,
            purchase_date="2020-01-01",
            warranty_expiry_date="2021-01-01",
            purchase_type="Warranty",
            is_assigned=False,
        )

        # Audit
        self.audit = Audit.objects.create(
            assigned_to="Employee 1",
            asset=self.asset,
            organization=self.organization,
            condition=1,
            notes="Initial audit notes",
            audited_by=self.user
        )

    # Test Create Audit
    def test_create_audit(self):
        audit = Audit.objects.get(id=self.audit.id)

        self.assertEqual(audit.assigned_to, "Employee 1")
        self.assertEqual(audit.asset.name, "Asset 1")
        self.assertEqual(audit.organization.name, "Organization 1")
        self.assertEqual(audit.condition, 1)
        self.assertEqual(audit.notes, "Initial audit notes")
        self.assertEqual(audit.audited_by.username, "auditor")
        self.assertIsNotNone(audit.created_at)

    # Test Edit Audit
    def test_edit_audit(self):
        self.audit.assigned_to = "Employee 2"
        self.audit.condition = 2
        self.audit.notes = "Updated audit notes"
        self.audit.save()

        audit = Audit.objects.get(id=self.audit.id)

        self.assertEqual(audit.assigned_to, "Employee 2")
        self.assertEqual(audit.condition, 2)
        self.assertEqual(audit.notes, "Updated audit notes")

    # Test Delete Audit
    def test_delete_audit(self):
        audit_id = self.audit.id
        self.audit.delete()

        with self.assertRaises(Audit.DoesNotExist):
            Audit.objects.get(id=audit_id)

    # Test Cascade: Delete Asset → Audit Deleted
    def test_delete_asset_deletes_audit(self):
        audit_id = self.audit.id
        self.asset.delete()

        with self.assertRaises(Audit.DoesNotExist):
            Audit.objects.get(id=audit_id)

    # Test Cascade: Delete Organization → Audit Deleted
    # def test_delete_organization_deletes_audit(self):
    #     audit_id = self.audit.id
    #     self.organization.delete()

    #     with self.assertRaises(Audit.DoesNotExist):
    #         Audit.objects.get(id=audit_id)

    # Test Cascade: Delete User → Audit Deleted
    def test_delete_user_deletes_audit(self):
        audit_id = self.audit.id
        self.user.delete()

        with self.assertRaises(Audit.DoesNotExist):
            Audit.objects.get(id=audit_id)