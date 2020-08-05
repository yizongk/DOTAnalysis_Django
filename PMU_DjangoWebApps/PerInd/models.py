# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Category(models.Model):
    category_id = models.AutoField(db_column='Category_ID', primary_key=True)  # Field name made lowercase.
    old_category_name = models.CharField(db_column='Old_Category_Name', max_length=255)  # Field name made lowercase.
    category_name = models.CharField(db_column='Category_Name', max_length=255)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Category'

    def __str__(self):
        return self.category_name


class DataSummaryType(models.Model):
    data_summary_id = models.AutoField(db_column='Data_Summary_ID', primary_key=True)  # Field name made lowercase.
    summary_type = models.CharField(db_column='Summary_Type', max_length=255)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Data_Summary_Type'

    def __str__(self):
        return self.summary_type


class DataType(models.Model):
    data_type_id = models.AutoField(db_column='Data_Type_ID', primary_key=True)  # Field name made lowercase.
    data_type = models.CharField(db_column='Data_Type', max_length=255)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Data_Type'

    def __str__(self):
        return self.data_type


class Unit(models.Model):
    unit_id = models.AutoField(db_column='Unit_ID', primary_key=True)  # Field name made lowercase.
    unit_type = models.CharField(db_column='Unit_Type', max_length=255)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Unit'

    def __str__(self):
        return self.unit_type


class Users(models.Model):
    user_id = models.AutoField(db_column='User_ID', primary_key=True)  # Field name made lowercase.
    first_name = models.CharField(db_column='First_Name', max_length=255)  # Field name made lowercase.
    last_name = models.CharField(db_column='Last_Name', max_length=255)  # Field name made lowercase.
    login = models.CharField(db_column='Login', max_length=255)  # Field name made lowercase.
    active_user = models.BooleanField(db_column='Active_User', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Users'

    def __str__(self):
        return self.login


class ValMultiplier(models.Model):
    val_multiplier_id = models.AutoField(db_column='Val_Multiplier_ID', primary_key=True)  # Field name made lowercase.
    multiplier_scale = models.IntegerField(db_column='Multiplier_Scale')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Val_Multiplier'

    def __str__(self):
        return self.multiplier_scale


class YearMonth(models.Model):
    year_month_id = models.AutoField(db_column='Year_Month_ID', primary_key=True)  # Field name made lowercase.
    yyyy = models.IntegerField(db_column='YYYY')  # Field name made lowercase.
    mm = models.IntegerField(db_column='MM')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Year_Month'


class UserPermissions(models.Model):
    user_permission_id = models.AutoField(db_column='User_Permission_ID', primary_key=True)  # Field name made lowercase.
    # user_id = models.IntegerField(db_column='User_ID', blank=True, null=True)  # Field name made lowercase.
    # category_id = models.IntegerField(db_column='Category_ID', blank=True, null=True)  # Field name made lowercase.
    read_right = models.BooleanField(db_column='Read_Right', blank=True, null=True)  # Field name made lowercase.
    write_right = models.BooleanField(db_column='Write_Right', blank=True, null=True)  # Field name made lowercase.
    user = models.ForeignKey(to=Users, on_delete=models.DO_NOTHING)  # Field name made lowercase.
    category = models.ForeignKey(to=Category, on_delete=models.DO_NOTHING)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'User_Permissions'


class IndicatorList(models.Model):
    indicator_id = models.AutoField(db_column='Indicator_ID', primary_key=True)  # Field name made lowercase.
    old_indicator_title = models.CharField(db_column='Old_Indicator_Title', max_length=255)  # Field name made lowercase.
    indicator_title = models.CharField(db_column='Indicator_Title', max_length=255)  # Field name made lowercase.
    # category_id = models.IntegerField(db_column='Category_ID')  # Field name made lowercase.
    # unit_id = models.IntegerField(db_column='Unit_ID')  # Field name made lowercase.
    # data_type_id = models.IntegerField(db_column='Data_Type_ID')  # Field name made lowercase.
    # val_multiplier_id = models.IntegerField(db_column='Val_Multiplier_ID')  # Field name made lowercase.
    active = models.BooleanField(db_column='Active', blank=True, null=True)  # Field name made lowercase.
    # summary_type_id = models.IntegerField(db_column='Summary_Type_ID')  # Field name made lowercase.
    category = models.ForeignKey(to=Category, on_delete=models.DO_NOTHING)  # Field name made lowercase.
    unit = models.ForeignKey(to=Unit, on_delete=models.DO_NOTHING)  # Field name made lowercase.
    data_type = models.ForeignKey(to=DataType, on_delete=models.DO_NOTHING)  # Field name made lowercase.
    val_multiplier = models.ForeignKey(to=ValMultiplier, on_delete=models.DO_NOTHING)  # Field name made lowercase.
    summary_type = models.ForeignKey(to=DataSummaryType, on_delete=models.DO_NOTHING)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Indicator_List'


    def __str__(self):
        return self.indicator_title


class IndicatorData(models.Model):
    record_id = models.AutoField(db_column='Record_ID', primary_key=True)  # Field name made lowercase.
    # indicator_id = models.IntegerField(db_column='Indicator_ID')  # Field name made lowercase.
    # year_month_id = models.IntegerField(db_column='Year_Month_ID')  # Field name made lowercase.
    val = models.FloatField(db_column='Val', blank=True, null=True)  # Field name made lowercase.
    created_date = models.DateTimeField(db_column='Created_Date')  # Field name made lowercase.
    updated_date = models.DateTimeField(db_column='Updated_Date')  # Field name made lowercase.
    # update_user_id = models.IntegerField(db_column='Update_User_ID')  # Field name made lowercase.
    indicator = models.ForeignKey(to=IndicatorList, on_delete=models.DO_NOTHING)  # Field name made lowercase.
    year_month = models.ForeignKey(to=YearMonth, on_delete=models.DO_NOTHING)  # Field name made lowercase.
    update_user = models.ForeignKey(to=Users, on_delete=models.DO_NOTHING)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Indicator_Data'
        ordering = ['indicator__indicator_title', 'year_month__yyyy', 'year_month__mm']
