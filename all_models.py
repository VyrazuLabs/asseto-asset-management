# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Assets(models.Model):
    name = models.CharField(max_length=255)
    serial_no = models.CharField(max_length=45)
    price = models.FloatField()
    purchase_date = models.DateField()
    warranty_expiry_date = models.DateField()
    purchase_type = models.CharField(max_length=45)
    status = models.IntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    created_by = models.IntegerField()
    updated_by = models.DateTimeField()
    products_product = models.ForeignKey('Products', models.DO_NOTHING)
    vendors_vendor = models.ForeignKey('Vendors', models.DO_NOTHING)
    organization = models.ForeignKey('Organization', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'assets'
        unique_together = (('id', 'products_product', 'vendors_vendor', 'organization'),)


class AssetsSpecification(models.Model):
    assets_asset = models.OneToOneField(Assets, models.DO_NOTHING, primary_key=True)
    specification_specification = models.ForeignKey('Specification', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'assets_specification'
        unique_together = (('assets_asset', 'specification_specification'),)


class Departments(models.Model):
    name = models.CharField(max_length=255)
    contact_person_name = models.CharField(max_length=255)
    contact_person_email = models.CharField(max_length=255)
    contact_person_phone = models.CharField(max_length=255)
    status = models.IntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    created_by = models.IntegerField()
    updated_by = models.IntegerField()
    organization = models.ForeignKey('Organization', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'departments'
        unique_together = (('id', 'organization'),)


class Employees(models.Model):
    name = models.CharField(max_length=255)
    employee_id = models.CharField(max_length=45)
    departments = models.ForeignKey(Departments, models.DO_NOTHING)
    reporting_manager = models.ForeignKey('self', models.DO_NOTHING, db_column='reporting_manager')
    email = models.CharField(max_length=255)
    phone = models.CharField(max_length=45)
    status = models.IntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    created_by = models.IntegerField()
    updated_by = models.IntegerField()
    organization = models.ForeignKey('Organization', models.DO_NOTHING)
    locations = models.ForeignKey('Locations', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'employees'
        unique_together = (('id', 'departments', 'reporting_manager', 'organization', 'locations'),)


class Locations(models.Model):
    organization = models.ForeignKey('Organization', models.DO_NOTHING)
    office_name = models.CharField(max_length=255)
    address_line_one = models.CharField(max_length=255)
    address_line_two = models.CharField(max_length=255)
    country = models.IntegerField()
    state = models.IntegerField()
    city = models.CharField(max_length=255)
    pin_code = models.CharField(max_length=255)
    contact_person_name = models.CharField(max_length=255)
    contact_person_phone = models.CharField(max_length=255)
    status = models.IntegerField()
    created_by = models.IntegerField()
    updated_by = models.IntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'locations'
        unique_together = (('id', 'organization'),)


class Organization(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    website = models.CharField(max_length=255, blank=True, null=True)
    email = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)
    currency = models.IntegerField()
    date_format = models.IntegerField(blank=True, null=True)
    logo = models.CharField(max_length=255, blank=True, null=True)
    status = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'organization'


class ProductCategory(models.Model):
    category_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    status = models.IntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    created_by = models.IntegerField()
    updated_by = models.DateTimeField()
    organization = models.ForeignKey(Organization, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'product_category'
        unique_together = (('category_id', 'organization'),)


class ProductType(models.Model):
    type_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    status = models.IntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    created_by = models.IntegerField()
    updated_by = models.IntegerField()
    organization = models.ForeignKey(Organization, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'product_type'
        unique_together = (('type_id', 'organization'),)


class Products(models.Model):
    name = models.CharField(max_length=255)
    manufacturer = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    status = models.IntegerField()
    created_by = models.IntegerField()
    updated_by = models.IntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    product_category_category = models.ForeignKey(ProductCategory, models.DO_NOTHING)
    product_type_type = models.ForeignKey(ProductType, models.DO_NOTHING)
    organization = models.ForeignKey(Organization, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'products'
        unique_together = (('id', 'product_category_category', 'product_type_type', 'organization'),)


class Specification(models.Model):
    specification_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    created_by = models.IntegerField(blank=True, null=True)
    updated_by = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'specification'


class Uploads(models.Model):
    id = models.IntegerField(primary_key=True)
    organization = models.ForeignKey(Organization, models.DO_NOTHING)
    entity_type = models.CharField(max_length=255, blank=True, null=True)
    entity_id = models.IntegerField(blank=True, null=True)
    filename = models.CharField(max_length=255, blank=True, null=True)
    orignal_filename = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    size = models.CharField(max_length=255, blank=True, null=True)
    created_by = models.IntegerField(blank=True, null=True)
    updated_at = models.CharField(max_length=255, blank=True, null=True)
    updated_by = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'uploads'
        unique_together = (('id', 'organization'),)


class Users(models.Model):
    organization = models.ForeignKey(Locations, models.DO_NOTHING)
    user_id = models.CharField(max_length=255)
    locations = models.ForeignKey(Locations, models.DO_NOTHING)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)
    user_role = models.CharField(max_length=255)
    status = models.IntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    created_by = models.IntegerField()
    updated_by = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'users'
        unique_together = (('id', 'organization', 'locations'),)


class Vendors(models.Model):
    vendor_name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    phone = models.CharField(max_length=45)
    contact_person = models.CharField(max_length=255)
    designation = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    pin_code = models.CharField(max_length=45)
    gstin_number = models.CharField(max_length=45)
    address = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    status = models.IntegerField()
    created_by = models.IntegerField()
    updated_by = models.IntegerField()
    created_at = models.DateTimeField()
    updated_at = models.IntegerField()
    organization = models.ForeignKey(Organization, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'vendors'
        unique_together = (('id', 'organization'),)
