from django.db import models

# Create your models here.

# All field names made lowercase.
class Admins(models.Model):
    window_username = models.CharField(db_column='WindowUsername', max_length=255, primary_key=True)
    active = models.BooleanField(db_column='Active')

    class Meta:
        managed = False
        db_table = 'FleetDataCollectionAdmins'

    def __str__(self):
        return self.window_username

class DomicilePermissions(models.Model):
    domicile_permission_id = models.AutoField(db_column='FleetDataCollectionDomicilePermissionId', primary_key=True)
    window_username = models.CharField(db_column='WindowUsername', max_length=255)
    domicile = models.CharField(db_column='Domicile', max_length=5)

    class Meta:
        managed = False
        db_table = 'FleetDataCollectionDomicilePermissions'

    def __str__(self):
        return self.domicile

class WUPermissions(models.Model):
    wu_permission_id = models.AutoField(db_column='FleetDataCollectionWUPermissionId', primary_key=True)
    window_username = models.CharField(db_column='WindowUsername', max_length=255)
    wu = models.CharField(db_column='WU', max_length=4)

    class Meta:
        managed = False
        db_table = 'FleetDataCollectionWUPermissions'

    def __str__(self):
        return self.wu

class M5DriverVehicleDataConfirmations(models.Model):
    unit_number = models.CharField(db_column='UnitNumber', primary_key=True, max_length=20)
    pms = models.CharField(db_column='PMS', max_length=7)
    class2 = models.BooleanField(db_column='Class2')

    class Meta:
        managed = False
        db_table = 'FleetDataCollectionM5DriverVehicleDataConfirmations'

    def __str__(self):
        return self.unit_number

class TblEmployees(models.Model):
    pms = models.CharField(db_column='PMS#', primary_key=True, max_length=7)
    first_name = models.CharField(db_column='F-Name', max_length=255)
    last_name = models.CharField(db_column='L-Name', max_length=255)
    wu = models.CharField(db_column='WU', max_length=4)

    class Meta:
        managed = False
        db_table = 'tblEmployees'

    def __str__(self):
        return self.pms

class NYC_DOTR_UNIT_MAIN(models.Model):
    unit_no = models.CharField(db_column='UNIT_NO', max_length=30, primary_key=True)
    class1 = models.CharField(db_column='CLASS1', max_length=4)
    make = models.CharField(db_column='MAKE', max_length=30)
    model = models.CharField(db_column='MODEL', max_length=30)
    domicile = models.CharField(db_column='USING_DEPT_NO', max_length=30)

    class Meta:
        managed = False
        db_table = 'NYC_DOTR_UNIT_MAIN'

    def __str__(self):
        return self.unit_no