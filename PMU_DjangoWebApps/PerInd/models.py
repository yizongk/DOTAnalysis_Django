# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


# All field names made lowercase.
class Category(models.Model):
    category_id = models.AutoField(db_column='Category_ID', primary_key=True)
    old_category_name = models.CharField(db_column='Old_Category_Name', max_length=255)
    category_name = models.CharField(db_column='Category_Name', max_length=255)

    class Meta:
        managed = False
        db_table = 'Category'

    def __str__(self):
        return self.category_name


class DataSummaryType(models.Model):
    data_summary_id = models.AutoField(db_column='Data_Summary_ID', primary_key=True)
    summary_type = models.CharField(db_column='Summary_Type', max_length=255)

    class Meta:
        managed = False
        db_table = 'Data_Summary_Type'

    def __str__(self):
        return self.summary_type


class DataType(models.Model):
    data_type_id = models.AutoField(db_column='Data_Type_ID', primary_key=True)
    data_type = models.CharField(db_column='Data_Type', max_length=255)

    class Meta:
        managed = False
        db_table = 'Data_Type'

    def __str__(self):
        return self.data_type


class Unit(models.Model):
    unit_id = models.AutoField(db_column='Unit_ID', primary_key=True)
    unit_type = models.CharField(db_column='Unit_Type', max_length=255)

    class Meta:
        managed = False
        db_table = 'Unit'

    def __str__(self):
        return self.unit_type


"""
ALTER TABLE [Users]
ADD CONSTRAINT [AK_Users_Login] UNIQUE (Login);
"""
class Users(models.Model):
    user_id = models.AutoField(db_column='User_ID', primary_key=True)
    first_name = models.CharField(db_column='First_Name', max_length=255)
    last_name = models.CharField(db_column='Last_Name', max_length=255)
    login = models.CharField(db_column='Login', max_length=255, unique=True)
    active_user = models.BooleanField(db_column='Active_User', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Users'

    def __str__(self):
        return self.login


class ValMultiplier(models.Model):
    val_multiplier_id = models.AutoField(db_column='Val_Multiplier_ID', primary_key=True)
    multiplier_scale = models.IntegerField(db_column='Multiplier_Scale')

    class Meta:
        managed = False
        db_table = 'Val_Multiplier'

    def __str__(self):
        return self.multiplier_scale

"""
ALTER TABLE Year_Month
ADD [Fiscal_Year] INT DEFAULT 0 NOT NULL
GO
UPDATE Year_Month
SET [Fiscal_Year] = (
	CASE
		WHEN MM IN (1, 2, 3, 4, 5, 6) THEN [YYYY]
		WHEN MM IN (7, 8, 9, 10, 11, 12) THEN [YYYY] + 1
		ELSE 0
	END
)
GO
"""
class YearMonth(models.Model):
    year_month_id = models.AutoField(db_column='Year_Month_ID', primary_key=True)
    yyyy = models.IntegerField(db_column='YYYY')
    mm = models.IntegerField(db_column='MM')
    fiscal_year = models.IntegerField(db_column='Fiscal_Year')

    class Meta:
        managed = False
        db_table = 'Year_Month'


class UserPermissions(models.Model):
    # All field names made lowercase.
    user_permission_id = models.AutoField(db_column='User_Permission_ID', primary_key=True)
    # user_id = models.IntegerField(db_column='User_ID', blank=True, null=True)
    # category_id = models.IntegerField(db_column='Category_ID', blank=True, null=True)
    user = models.ForeignKey(to=Users, on_delete=models.DO_NOTHING)
    category = models.ForeignKey(to=Category, on_delete=models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'User_Permissions'


class IndicatorList(models.Model):
    indicator_id = models.AutoField(db_column='Indicator_ID', primary_key=True)
    old_indicator_title = models.CharField(db_column='Old_Indicator_Title', max_length=255)
    indicator_title = models.CharField(db_column='Indicator_Title', max_length=255)
    # category_id = models.IntegerField(db_column='Category_ID')
    # unit_id = models.IntegerField(db_column='Unit_ID')
    # data_type_id = models.IntegerField(db_column='Data_Type_ID')
    # val_multiplier_id = models.IntegerField(db_column='Val_Multiplier_ID')
    active = models.BooleanField(db_column='Active', blank=True, null=True)
    # summary_type_id = models.IntegerField(db_column='Summary_Type_ID')
    category = models.ForeignKey(to=Category, on_delete=models.DO_NOTHING)
    unit = models.ForeignKey(to=Unit, on_delete=models.DO_NOTHING)
    data_type = models.ForeignKey(to=DataType, on_delete=models.DO_NOTHING)
    val_multiplier = models.ForeignKey(to=ValMultiplier, on_delete=models.DO_NOTHING)
    summary_type = models.ForeignKey(to=DataSummaryType, on_delete=models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'Indicator_List'


    def __str__(self):
        return self.indicator_title


class IndicatorData(models.Model):
    record_id = models.AutoField(db_column='Record_ID', primary_key=True)
    # indicator_id = models.IntegerField(db_column='Indicator_ID')
    # year_month_id = models.IntegerField(db_column='Year_Month_ID')
    val = models.FloatField(db_column='Val', blank=True, null=True)
    created_date = models.DateTimeField(db_column='Created_Date')
    updated_date = models.DateTimeField(db_column='Updated_Date')
    # update_user_id = models.IntegerField(db_column='Update_User_ID')
    indicator = models.ForeignKey(to=IndicatorList, on_delete=models.DO_NOTHING)
    year_month = models.ForeignKey(to=YearMonth, on_delete=models.DO_NOTHING)
    update_user = models.ForeignKey(to=Users, on_delete=models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'Indicator_Data'
        ordering = ['indicator__indicator_title', 'year_month__yyyy', 'year_month__mm']


"""
CREATE TABLE Admins (
	[Admin_ID] int NOT NULL IDENTITY PRIMARY KEY,
	[User_ID] int NOT NULL FOREIGN KEY REFERENCES Users([User_ID]),
	[Active] bit NOT NULL,
    CONSTRAINT [AK__Admins__User_ID] UNIQUE (User_ID)
)

INSERT INTO dbo.Admins
([User_ID], [Active]) VALUEs (67, 1)
"""
class Admins(models.Model):
    admin_id = models.AutoField(db_column='Admin_ID', primary_key=True)
    user = models.ForeignKey(to=Users, on_delete=models.DO_NOTHING)
    active = models.BooleanField(db_column='Active', blank=False, null=False)

    class Meta:
        managed = False
        db_table = 'Admins'