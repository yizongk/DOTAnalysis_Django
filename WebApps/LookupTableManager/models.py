from django.db import models

# Create your models here.

#Abrar- Model class based off local database table

class WUTable2(models.Model):
    id = models.CharField(db_column='ID', max_length=50, blank=True, null=False, primary_key= True)  # Field name made lowercase.
    wu = models.CharField(db_column='WU', max_length=50, blank=True, null=True)  # Field name made lowercase.
    div = models.CharField(db_column='DIV', max_length=50, blank=True, null=True)  # Field name made lowercase.
    workunitdescription = models.CharField(db_column='WorkUnitDescription', max_length=50, blank=True, null=True)  # Field name made lowercase.
    divisiongroup = models.CharField(db_column='DivisionGroup', max_length=50, blank=True, null=True)  # Field name made lowercase.
    subdivision = models.CharField(db_column='SubDivision', max_length=50, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'WorkUnitTable2'