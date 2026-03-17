from django.test import TestCase
from dashboard.models import LicenseType
from license.models import License
from vendors.models import Vendor
class TestLicense(TestCase):
    def setUp(self):
        create_license_type=LicenseType.objects.create(name='Test License type')
        create_vendor=Vendor.objects.create(name='TestVendor')
        License.objects.create(
            name='Test License',
            license_type=create_license_type,
            vendor=create_vendor,
            seats=12,
            start_date="01/01/2026",
            expiry_date="01/01/2027",
            key="98798qw7d9wddDWD7984",
            notes="Test Description",
            is_assigned=True
        )
    
    def test_license_list(self):
        get_license=License.objects.get(name='Test License')
        self.assertEqual(get_license.name,'Test License')
        self.assertEqual(get_license.license_type.name,'Test License type')
        self.assertEqual(get_license.vendor.name,"TestVendor")
        self.assertEqual(get_license.seats,12)
        self.assertEqual(get_license.start_date,"01/01/2026")
        self.assertEqual(get_license.expiry_date,"01/01/2027")
        self.assertEqual(get_license.key,"98798qw7d9wddDWD7984")
        self.assertEqual(get_license.notes,"Test Description")

    def test_edit_liense(self):

        self.get_license='Test License2'
        self.get_license.license_type.name,'Test License type'
        self.assertEqualget_license.vendor.name,"TestVendor"
        self.assertEqualget_license.seats,12
        self.assertEqualget_license.start_date,"01/01/2026"
        self.assertEqualget_license.expiry_date,"01/01/2027"
        self.assertEqualget_license.key,"98798qw7d9wddDWD7984"
        self.assertEqualget_license.notes,"Test Description"

        get_license=License.objects.get(name='Test License')

