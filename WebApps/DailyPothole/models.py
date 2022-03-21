from django.db import models

# Create your models here.

# SQL Server store datetime as UTC time

# All field names made lowercase.
class TblBoro(models.Model):
    boro_id = models.AutoField(db_column='BoroId', primary_key=True)
    boro_order = models.IntegerField(db_column='BoroOrder', unique=True)
    boro_code = models.CharField(db_column='BoroCode', max_length=1, blank=False, null=False, unique=True)
    boro_long = models.CharField(db_column='BoroLong', max_length=20, blank=False, null=False)

    class Meta:
        managed = False
        db_table = 'tblBoro'

    def __str__(self):
        return self.boro_code


class TblOperation(models.Model):
    operation_id = models.AutoField(db_column='OperationId', primary_key=True)
    operation_code = models.IntegerField(db_column='OperationCode', blank=False, null=False, unique=True)
    operation = models.CharField(db_column='Operation', max_length=50, blank=False, null=False)

    class Meta:
        managed = False
        db_table = 'tblOperation'

    def __str__(self):
        return self.operation


class TblUser(models.Model):
    user_id = models.AutoField(db_column='UserId', primary_key=True)
    username = models.CharField(db_column='Username', max_length=50, unique=True)
    is_admin = models.BooleanField(db_column='IsAdmin')

    class Meta:
        managed = False
        db_table = 'tblUser'

    def __str__(self):
        return self.username


class TblPermission(models.Model):
    permission_id = models.AutoField(db_column='PermissionId', primary_key=True)
    user_id = models.ForeignKey(to=TblUser, to_field='user_id', db_column='UserId', on_delete=models.DO_NOTHING)
    operation_id = models.ForeignKey(to=TblOperation, to_field='operation_id', db_column='OperationId', on_delete=models.DO_NOTHING)
    boro_id = models.ForeignKey(to=TblBoro, to_field='boro_id', db_column='BoroId', on_delete=models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'tblPermission'

    def __str__(self):
        return self.user_id


class TblPotholeMaster(models.Model):
    '''
    Some of the ForeignKey has null=True, to allow for Django Queryset to use LEFT JOIN/LEFT OUTER JOIN (They are the same MS Sql Server) instead of INNER JOIN.
    This way, the LEFT JOIN will keeps rows with NULL fks.(Especially when you you want to use some_model.values(...))
    '''
    pothole_master_id = models.AutoField(db_column='PotholeMasterId', primary_key=True)
    repair_date = models.DateField(db_column='RepairDate')
    operation_id = models.ForeignKey(to=TblOperation, to_field='operation_id', db_column='OperationId', on_delete=models.DO_NOTHING, null=True)
    boro_id = models.ForeignKey(to=TblBoro, to_field='boro_id', db_column='BoroId', on_delete=models.DO_NOTHING, null=True)
    daily_crew_count = models.DecimalField(db_column='PlannedCrewCount', max_digits=11, decimal_places=2)
    repair_crew_count = models.DecimalField(db_column='ActualCrewCount', max_digits=11, decimal_places=2)
    holes_repaired = models.IntegerField(db_column='ActualPotholesRepaired')
    last_modified_timestamp = models.DateTimeField(db_column='LastModifiedTimestamp')
    last_modified_by_user_id = models.ForeignKey(to=TblUser, to_field='user_id', db_column='LastModifiedByUserId', on_delete=models.DO_NOTHING, null=True)

    class Meta:
        managed = False
        db_table = 'tblPotholeMaster'

    def __str__(self):
        return self.last_modified_by_user_id


class TblComplaint(models.Model):
    complaint_id        = models.AutoField(     db_column='ComplaintId'     , primary_key=True)
    complaint_date      = models.DateField(     db_column='ComplaintDate'   , unique=True)
    fits_complaints     = models.IntegerField(  db_column='FITSComplaints'  )
    fits_bronx          = models.IntegerField(  db_column='FITSBronx'       )
    fits_brooklyn       = models.IntegerField(  db_column='FITSBrooklyn'    )
    fits_manhattan      = models.IntegerField(  db_column='FITSManhattan'   )
    fits_queens         = models.IntegerField(  db_column='FITSQueens'      )
    fits_staten_island  = models.IntegerField(  db_column='FITSStatenIsland')
    fits_unassigned     = models.IntegerField(  db_column='FITSUnassigned'  )
    siebel_complaints   = models.IntegerField(  db_column='SiebelComplaints')

    class Meta:
        managed = False
        db_table = 'tblComplaint'

    def __str__(self):
        return self.complaint_date