from django.db import models

# Create your models here.

# All field names made lowercase.
class TblChanges(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)
    updated_on = models.DateTimeField(db_column='UpdatedOn', blank=False, null=False, )
    updated_by_pms = models.CharField(db_column='UpdatedByPMS', blank=False, null=False, max_length=7)
    updated_to_pms = models.CharField(db_column='UpdatedToPMS', blank=False, null=False, max_length=7)
    new_value = models.CharField(db_column='NewValue', blank=True, null=True, max_length=255)
    column_name = models.CharField(db_column='ColumnName', blank=False, null=False, max_length=255)

    class Meta:
        managed = False
        db_table = 'tblChanges'

    def __str__(self):
        return self.new_value

class TblDOTSites(models.Model):
    id = models.AutoField(db_column='Id', primary_key=True)
    site_id = models.CharField(db_column='SiteId', max_length=255, blank=False, null=False, unique=True) ## Funtional PK
    pms_loc_cd = models.CharField(db_column='PMSLocCd', max_length=255)
    site = models.CharField(db_column='Site', max_length=255)
    address = models.CharField(db_column='Address', max_length=255)

    class Meta:
        managed = False
        db_table = 'tblDOTSites'

    def __str__(self):
        return self.site

class TblDOTSiteFloors(models.Model):
    id = models.AutoField(db_column='Id', primary_key=True)
    floor_id = models.CharField(db_column='FloorId', max_length=255, blank=False, null=False, unique=True) ## Funtional PK
    site_id = models.ForeignKey(TblDOTSites, to_field='site_id', db_column='SiteId', max_length=255, blank=False, null=False, on_delete=models.DO_NOTHING)
    floor = models.CharField(db_column='Floor', max_length=5)
    square_footage = models.BigIntegerField(db_column='SquareFootage')

    class Meta:
        managed = False
        db_table = 'tblDOTSiteFloors'

    def __str__(self):
        return self.floor

class TblDOTSiteTypes(models.Model):
    site_type_id = models.AutoField(db_column='SiteTypeId', primary_key=True) ## Funtional PK
    site_type = models.CharField(db_column='SiteType', max_length=255, blank=False, null=False)
    site_description = models.CharField(db_column='SiteDescription', max_length=255, blank=False, null=False)

    class Meta:
        managed = False
        db_table = 'tblDOTSiteTypes'

    def __str__(self):
        return self.site_type

class TblDOTSiteFloorSiteTypes(models.Model):
    id = models.AutoField(db_column='Id', primary_key=True)
    floor_id = models.ForeignKey(TblDOTSiteFloors, to_field='floor_id', db_column='FloorId', max_length=255, blank=False, null=False, on_delete=models.DO_NOTHING)
    site_type_id = models.ForeignKey(TblDOTSiteTypes, to_field='site_type_id', db_column='SiteTypeId', blank=False, null=False, on_delete=models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'tblDOTSiteFloorSiteTypes'

    def __str__(self):
        return f"{self.site_type_id}"

class TblEmployees(models.Model):
    '''
    Some of the ForeignKey has null=True, to allow for Django Queryset to use LEFT JOIN/LEFT OUTER JOIN (They are the same MS Sql Server) instead of INNER JOIN.
    This way, the LEFT JOIN will keeps rows with NULL fks.
    '''
    wu = models.ForeignKey(db_column='WU', to='TblWorkUnits', to_field='wu', on_delete=models.DO_NOTHING, null=True)
    last_name = models.CharField(db_column='L-Name', max_length=255)
    first_name = models.CharField(db_column='F-Name', max_length=255)
    pms = models.CharField(db_column='PMS#', primary_key=True, max_length=7)
    civil_title = models.CharField(db_column='Title', max_length=255)

    supervisor_pms = models.ForeignKey(to='TblEmployees', to_field='pms', db_column='SupervisorPMS', max_length=7, on_delete=models.DO_NOTHING, null=True)
    office_title = models.CharField(db_column='OfficeTitle', max_length=255)  ## Should a foreign key to tblOfficeTitles, but this logic is not in the over arching umbrella yet.

    actual_site_id = models.ForeignKey(TblDOTSites, to_field='site_id', db_column='ActualSiteId', max_length=255, on_delete=models.DO_NOTHING, null=True)
    actual_floor_id = models.ForeignKey(TblDOTSiteFloors, to_field='floor_id', db_column='ActualFloorId', max_length=255, on_delete=models.DO_NOTHING, null=True)
    actual_site_type_id = models.ForeignKey(TblDOTSiteTypes, to_field='site_type_id', db_column='ActualSiteTypeId', on_delete=models.DO_NOTHING, null=True)

    abc_group = models.CharField(db_column='ABCGroup', max_length=1)

    lv = models.CharField(db_column='Lv', max_length=255)

    class Meta:
        managed = False
        db_table = 'tblEmployees'

    def __str__(self):
        return self.pms

class TblOfficeTitles(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)
    office_title = models.CharField(db_column='OfficeTitle', max_length=255, blank=False, null=False)
    active = models.BooleanField(db_column='Active', blank=False, null=False)

    class Meta:
        managed = False
        db_table = 'tblOfficeTitles'

    def __str__(self):
        return self.office_title

class TblWorkUnits(models.Model):
    id = models.AutoField(db_column='ID', primary_key=True)
    wu = models.CharField(db_column='WU', max_length=4, unique=True)
    div = models.CharField(db_column='DIV', max_length=255)
    wu_desc = models.CharField(db_column='Work Unit Description', max_length=255)
    div_group = models.CharField(db_column='Division Group', max_length=255)
    subdiv = models.CharField(db_column='SubDivision', max_length=255)

    class Meta:
        managed = False
        db_table = 'tblWorkUnits'

    def __str__(self):
        return self.wu

class TblUsers(models.Model):
    user_id = models.AutoField(db_column='UserId', primary_key=True)
    pms = models.ForeignKey(db_column='PMS', to='TblEmployees', to_field='pms', on_delete=models.DO_NOTHING, blank=False, null=False, max_length=7, unique=True)
    windows_username = models.CharField(db_column='WindowsUsername', max_length=255, blank=False, null=False, unique=True)
    is_admin = models.BooleanField(db_column='IsAdmin', blank=False, null=False, default=False)
    active = models.BooleanField(db_column='Active', blank=False, null=False, default=True)

    class Meta:
        managed = False
        db_table = 'tblUsers'

    def __str__(self):
        return self.windows_username

class TblPermissionsWorkUnit(models.Model):
    permission_id = models.AutoField(db_column='PermissionId', primary_key=True)
    user_id = models.ForeignKey(db_column='UserId', to='TblUsers', to_field='user_id', blank=False, null=False, on_delete=models.DO_NOTHING)
    wu = models.ForeignKey(db_column='WU', to='TblWorkUnits', to_field='wu', blank=False, null=False, on_delete=models.DO_NOTHING, max_length=4)

    class Meta:
        managed = False
        db_table = 'tblPermissionsWorkUnit'

    def __str__(self):
        return self.wu

# class TblPositions(models.Model):
#     position_id = models.AutoField(db_column='PositionID', primary_key=True)
#     reports_to_position_id = models.ForeignKey(to='TblPositions', to_field='position_id', db_column='ReportsToPositionID', max_length=7, on_delete=models.DO_NOTHING)
#     budgeted_bc = models.CharField(db_column='BudgetedBC', max_length=4)
#     position_filled = models.BooleanField(db_column='PositionFilled')
#     pms = models.ForeignKey(to='TblEmployees', to_field='pms', db_column='PMS', max_length=7, on_delete=models.DO_NOTHING)

#     class Meta:
#         managed = False
#         db_table = 'tblPositions'

#     def __str__(self):
#         return self.position_id