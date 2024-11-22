from django.test import TestCase
from .models import Role
from dashboard.models import Organization

class Asseto_test_add(TestCase):
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
        Role.objects.create(
            related_name= "Role 1",
            organization=user_organization,
        )
        print("setup product category")

    def test_product_category(self):
        print("testing.......")
        role = Role.objects.get(related_name="Role 1")
        self.assertEqual(role.related_name, "Role 1")
        self.assertEqual(role.organization.name, "Organization 1")


class EditRoleTest(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name='Organization 1',
                                                        website='www.example.com',
                                                        email='organization@example.com', 
                                                        phone='1234567890')
        self.role = Role.objects.create(related_name='Role 1', organization=self.organization)

    def test_edit_role(self):
        # Edit the role
        self.role.related_name = 'New Role'
        self.role.organization.name = 'New Organization'
        self.role.organization.website = 'www.newexample.com'
        self.role.organization.email = 'neworganization@example.com'
        self.role.organization.phone = '9876543210'
        self.role.save()

        # Check that the changes were saved correctly
        self.assertEqual(self.role.related_name, 'New Role')
        self.assertEqual(self.role.organization.name, 'New Organization')
        self.assertEqual(self.role.organization.website, 'www.newexample.com')
        self.assertEqual(self.role.organization.email, 'neworganization@example.com')
        self.assertEqual(self.role.organization.phone, '9876543210')

    def test_edit_role_with_same_info(self):
        # Edit the role with same information
        self.role.related_name = 'Role 1'
        self.role.organization.name = 'Organization 1'
        self.role.organization.website = 'www.example.com'
        self.role.organization.email = 'organization@example.com'
        self.role.organization.phone = '1234567890'
        self.role.save()

        # Check that the changes were saved correctly
        self.assertEqual(self.role.related_name, 'Role 1')
        self.assertEqual(self.role.organization.name, 'Organization 1')
        self.assertEqual(self.role.organization.website, 'www.example.com')
        self.assertEqual(self.role.organization.email, 'organization@example.com')
        self.assertEqual(self.role.organization.phone, '1234567890')