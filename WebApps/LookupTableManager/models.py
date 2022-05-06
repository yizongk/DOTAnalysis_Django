from django.db import models

# Create your models here.

#Abrar- Model class based off local database table

class TblUsers(models.Model):
    user_id = models.AutoField(db_column='UserId', primary_key=True)
    windows_username = models.CharField(db_column='WindowsUsername', max_length=255, blank=False, null=False, unique=True)
    is_admin = models.BooleanField(db_column='IsAdmin', blank=False, null=False, default=False)
    active = models.BooleanField(db_column='Active', blank=False, null=False, default=True)

    class Meta:
        managed = False
        db_table = 'tblUsers'

    def __str__(self):
        return self.windows_username

class TblWorkUnits(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)
    wu = models.CharField(db_column='WU', max_length=4, unique=True)
    div = models.CharField(db_column='DIV', max_length=255)
    wu_desc = models.CharField(db_column='Work Unit Description', max_length=255)
    div_group = models.CharField(db_column='Division Group', max_length=255)
    subdiv = models.CharField(db_column='SubDivision', max_length=255)
    active = models.BooleanField(db_column='Active', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tblWorkUnits'

    def __str__(self):
        return self.wu
