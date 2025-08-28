from django.test import TestCase
from django.contrib.auth import get_user_model
from dashboard.models import Organization,Address,Location,Department
from roles.models import Role
from authentication.models import User
from vendors.models import Vendor
import uuid
# Create your tests here.

class User_Test(TestCase):
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
            country = "India",
            state = "Rajasthan",
            address_line_one = "testline 1",
            address_line_two = "testline 2",
            city = "Jaipur",
            pin_code = "302001"
        )
        self.user_role=Role.objects.create(
            related_name= "Role 1",
            organization=self.user_organization,
        )
        self.user_location=Location.objects.create(
            office_name = "Office 1",
            address = self.user_address,
            contact_person_name = "Person 1",
            contact_person_email = "person1@asseto.com",
            contact_person_phone = "1234567890",
            organization = self.user_organization
        )
        self.user_department=Department.objects.create(
            name="Department 1",
            organization=self.user_organization,
            contact_person_name = "Person 1",
            contact_person_email = "person1@asseto.com",
            contact_person_phone = "1234567890",
        )
        self.user=User.objects.create(
        email = "mail@gmail.com",
        username = 'usertest',
        full_name = 'test',
        phone = '1234567890',
        role = self.user_role,
        organization = self.user_organization,
        address= self.user_address,
        location=self.user_location,
        department=self.user_department,
        profile_pic="test.jpg",
        employee_id="1234",
        is_active=True,
        is_staff=True,
        access_level=1
        )
        self.edit_user_organization = Organization.objects.create(
            name="Organization 2",
            website="asseto2.com",
            phone="123456789",
            email="asseto@asseto2.com",
            currency="INR2",
            date_format="dd-mm-yyyy",
            logo = "logo2.png"
        )
        self.edit_user_address=Address.objects.create(
            country = "India",
            state = "West Bengal",
            address_line_one = "testline 11",
            address_line_two = "testline 21",
            city = "Kolkata",
            pin_code = "700018"
        )
        # self.edit_user_role=Role.objects.create(
        #     related_name= "Role 2",
        #     organization=self.edit_user_organization,
        # )
        self.edit_user_location=Location.objects.create(
            office_name = "Office 2",
            address = self.edit_user_address,
            contact_person_name = "Person 2",
            contact_person_email = "person2@asseto.com",
            contact_person_phone = "1234567899",
            organization = self.edit_user_organization
        )
        self.edit_user_department=Department.objects.create(
            name="Department 2",
            organization=self.edit_user_organization,
            contact_person_name = "Person 2",
            contact_person_email = "person2@asseto.com",
            contact_person_phone = "1234567899",
        )
        self.edit_user=User.objects.create(
        email = "mail2@gmail.com",
        username = 'usertest2',
        full_name = 'test2',
        phone = '1234567899',
        role = self.user_role,
        organization = self.edit_user_organization,
        address= self.edit_user_address,
        location= self.edit_user_location,
        department= self.edit_user_department,
        profile_pic="test2.jpg",
        employee_id="12342",
        is_active=True,
        is_staff=True,
        access_level=0
        )


    def test_user(self):
        # self.user = User.objects.get(email = "mail@gmail.com")
        self.assertEqual(self.user.full_name, "test")
        self.assertEqual(self.user.username, "usertest")
        self.assertEqual(self.user.profile_pic, "test.jpg")
        self.assertEqual(self.user.phone, "1234567890")
        self.assertEqual(self.user.employee_id, "1234")
        self.assertEqual(self.user.is_active, True)
        self.assertEqual(self.user.is_staff, True)
        self.assertEqual(self.user.access_level, 1)
        self.assertEqual(self.user.address.address_line_one, "testline 1")
        self.assertEqual(self.user.address.address_line_two, "testline 2")
        self.assertEqual(self.user.address.city, "Jaipur")
        self.assertEqual(self.user.address.pin_code, "302001")
        self.assertEqual(self.user.address.state, "Rajasthan")
        self.assertEqual(self.user.address.country, "India")
        self.assertEqual(self.user.location.office_name, "Office 1")
        # self.assertEqual(user.location.contact_person_name, "Person 1")
        # self.assertEqual(user.location.contact_person_email, "person1@asseto.com")
        # self.assertEqual(user.location.contact_person_phone, "1234567890")
        self.assertEqual(self.user.role.related_name, "Role 1")
        self.assertEqual(self.user.department.name, "Department 1")
        self.assertEqual(self.user.department.contact_person_name, "Person 1")
        self.assertEqual(self.user.department.contact_person_email, "person1@asseto.com")
        self.assertEqual(self.user.department.contact_person_phone, "1234567890")
        self.assertEqual(self.user.organization.name, "Organization 1")
        self.assertEqual(self.user.organization.website, "asseto.com")
        self.assertEqual(self.user.organization.phone, "1234567890")
        self.assertEqual(self.user.organization.email, "asseto@asseto.com")
        self.assertEqual(self.user.organization.currency, "INR")
        self.assertEqual(self.user.organization.date_format, "dd-mm-yyyy")
        self.assertEqual(self.user.organization.logo, "logo.png")


    def test_edit_user(self):
        # user = User.objects.get(email="mail2@gmail.com")
        self.user.username = "usertest2"
        self.user.full_name = "test2"
        self.user.phone = "1234567890"
        self.user.profile_pic = "test2.jpg"
        self.user.employee_id = "12342"
        self.user.is_active = True
        self.user.is_staff = True
        self.user.access_level = 0
        self.user.organization.name = "Organization 2"
        self.user.organization.website = "asseto2.com"
        self.user.organization.phone = "123456789"
        self.user.organization.email = "asseto@asseto2.com"
        self.user.organization.currency = "INR2"
        self.user.organization.date_format = "dd-mm-yyyy"
        self.user.organization.logo = "logo2.png"
        self.user.address.country = "India"
        self.user.address.state = "West Bengal"
        self.user.address.address_line_one = "testline 11"
        self.user.address.address_line_two = "testline 21"
        self.user.address.city = "Kolkata"
        self.user.address.pin_code = "700018"
        self.user.location.office_name = "Office 2"
        self.user.location.contact_person_name = "Person 2"
        self.user.location.contact_person_email = "person2@asseto.com"
        self.user.location.contact_person_phone = "1234567890"
        self.user.department.name = "Department 2"
        self.user.department.contact_person_name = "Person 2"
        self.user.department.contact_person_email = "person2@asseto.com"
        self.user.department.contact_person_phone = "1234567890"
        self.user.save()
        self.assertEqual(self.user.username, "usertest2")
        self.assertEqual(self.user.full_name, "test2")
        self.assertEqual(self.user.phone, "1234567890")
        self.assertEqual(self.user.profile_pic, "test2.jpg")
        self.assertEqual(self.user.employee_id, "12342")
        self.assertEqual(self.user.is_active, True)
        self.assertEqual(self.user.is_staff, True)
        self.assertEqual(self.user.access_level, 0)
        self.assertEqual(self.user.organization.name, "Organization 2")
        self.assertEqual(self.user.organization.website, "asseto2.com")
        self.assertEqual(self.user.organization.phone, "123456789")
        self.assertEqual(self.user.organization.email, "asseto@asseto2.com")
        self.assertEqual(self.user.organization.currency, "INR2")
        self.assertEqual(self.user.organization.date_format, "dd-mm-yyyy")
        self.assertEqual(self.user.organization.logo, "logo2.png")
        self.assertEqual(self.user.address.country, "India")
        self.assertEqual(self.user.address.state, "West Bengal")
        self.assertEqual(self.user.address.address_line_one, "testline 11")
        self.assertEqual(self.user.address.address_line_two, "testline 21")
        self.assertEqual(self.user.address.city, "Kolkata")
        self.assertEqual(self.user.address.pin_code, "700018")
        self.assertEqual(self.user.location.office_name, "Office 2")
        self.assertEqual(self.user.location.contact_person_name, "Person 2")
        self.assertEqual(self.user.location.contact_person_email, "person2@asseto.com")
        self.assertEqual(self.user.location.contact_person_phone, "1234567890")
        self.assertEqual(self.user.department.name, "Department 2")
        self.assertEqual(self.user.department.contact_person_name, "Person 2")
        self.assertEqual(self.user.department.contact_person_email, "person2@asseto.com")
        self.assertEqual(self.user.department.contact_person_phone, "1234567890")   
        
    def delete_user(self):
        self.user.delete()

        # Check if the vendor object is deleted from the database
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(id=self.product.id)

        # Check if the address and organization objects are not affected
        address=Address.objects.get(id=self.user.address.id)
        location=Location.objects.get(id=self.user.location.id)
        organization = Organization.objects.get(name=self.user.organization.id)
        department=Department.objects.get(id=self.user.department.id)
        role=Role.objects.get(related_name=self.user.role.related_name)
        self.assertIsNotNone(location)
        self.assertIsNotNone(address)
        self.assertIsNotNone(department)
        self.assertIsNotNone(organization)
        self.assertIsNotNone(role)
