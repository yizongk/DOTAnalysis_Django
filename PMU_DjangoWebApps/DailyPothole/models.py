from django.db import models

# Create your models here.

# SQL Server store datetime as UTC time

# All field names made lowercase.
class TblBoro(models.Model):
    boros_id = models.AutoField(db_column='BorosId', primary_key=True)
    boro_order = models.IntegerField(db_column='BoroOrder', unique=True)
    boro_code = models.CharField(db_column='BoroCode', max_length=1, blank=False, null=False, unique=True)
    boro_long = models.CharField(db_column='BoroLong', max_length=20, blank=False, null=False)

    class Meta:
        managed = False
        db_table = 'TblBoro'

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


class TblUserList(models.Model):
    user_id = models.AutoField(db_column='UserId', primary_key=True)
    username = models.CharField(db_column='Username', max_length=50, unique=True)
    operation_id = models.ForeignKey(to=TblOperation, to_field='operation_id', db_column='OperationId', on_delete=models.DO_NOTHING)
    boros_id = models.ForeignKey(to=TblBoro, to_field='boros_id', db_column='BorosId', on_delete=models.DO_NOTHING)
    is_admin = models.BooleanField(db_column='IsAdmin')

    class Meta:
        managed = False
        db_table = 'tblUserList'

    def __str__(self):
        return self.username


class TblPotholeMaster(models.Model):
    pothole_master_id = models.AutoField(db_column='PotholeMasterId', primary_key=True)
    repair_date = models.DateField(db_column='RepairDate')
    operation_id = models.ForeignKey(to=TblOperation, to_field='operation_id', db_column='OperationId', on_delete=models.DO_NOTHING)
    boros_id = models.ForeignKey(to=TblBoro, to_field='boros_id', db_column='BorosId', on_delete=models.DO_NOTHING)
    repair_crew_count = models.IntegerField(db_column='RepairCrewCount')
    holes_repaired = models.IntegerField(db_column='HolesRepaired')
    daily_crew_count = models.IntegerField(db_column='DailyCrewCount')
    last_modified_stamp = models.DateTimeField(db_column='LastModifiedStamp')
    last_modified_by_user_id = models.ForeignKey(to=TblUserList, to_field='user_id', db_column='LastModifiedByUserId', on_delete=models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'tblPotholeMaster'

    def __str__(self):
        return self.last_modified_by_user_id