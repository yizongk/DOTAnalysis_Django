# Generated by Django 2.2.14 on 2020-07-16 17:03

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('category_id', models.AutoField(db_column='Category_ID', primary_key=True, serialize=False)),
                ('old_category_name', models.CharField(db_column='Old_Category_Name', max_length=255)),
                ('category_name', models.CharField(db_column='Category_Name', max_length=255)),
            ],
            options={
                'db_table': 'Category',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='DataSummaryType',
            fields=[
                ('data_summary_id', models.AutoField(db_column='Data_Summary_ID', primary_key=True, serialize=False)),
                ('summary_type', models.CharField(db_column='Summary_Type', max_length=255)),
            ],
            options={
                'db_table': 'Data_Summary_Type',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='DataType',
            fields=[
                ('data_type_id', models.AutoField(db_column='Data_Type_ID', primary_key=True, serialize=False)),
                ('data_type', models.CharField(db_column='Data_Type', max_length=255)),
            ],
            options={
                'db_table': 'Data_Type',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='IndicatorData',
            fields=[
                ('record_id', models.AutoField(db_column='Record_ID', primary_key=True, serialize=False)),
                ('indicator_id', models.IntegerField(db_column='Indicator_ID')),
                ('year_month_id', models.IntegerField(db_column='Year_Month_ID')),
                ('val', models.FloatField(blank=True, db_column='Val', null=True)),
                ('created_date', models.DateTimeField(db_column='Created_Date')),
                ('updated_date', models.DateTimeField(db_column='Updated_Date')),
                ('update_user_id', models.IntegerField(db_column='Update_User_ID')),
            ],
            options={
                'db_table': 'Indicator_Data',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='IndicatorList',
            fields=[
                ('indicator_id', models.AutoField(db_column='Indicator_ID', primary_key=True, serialize=False)),
                ('old_indicator_title', models.CharField(db_column='Old_Indicator_Title', max_length=255)),
                ('new_indicator_title', models.CharField(db_column='New_Indicator_Title', max_length=255)),
                ('category_id', models.IntegerField(db_column='Category_ID')),
                ('unit_id', models.IntegerField(db_column='Unit_ID')),
                ('data_type_id', models.IntegerField(db_column='Data_Type_ID')),
                ('val_multiplier_id', models.IntegerField(db_column='Val_Multiplier_ID')),
                ('active', models.BooleanField(blank=True, db_column='Active', null=True)),
                ('summary_type_id', models.IntegerField(db_column='Summary_Type_ID')),
            ],
            options={
                'db_table': 'Indicator_List',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Unit',
            fields=[
                ('unit_id', models.AutoField(db_column='Unit_ID', primary_key=True, serialize=False)),
                ('unit_type', models.CharField(db_column='Unit_Type', max_length=255)),
            ],
            options={
                'db_table': 'Unit',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='UserPermissions',
            fields=[
                ('user_permission_id', models.AutoField(db_column='User_Permission_ID', primary_key=True, serialize=False)),
                ('user_id', models.IntegerField(blank=True, db_column='User_ID', null=True)),
                ('category_id', models.IntegerField(blank=True, db_column='Category_ID', null=True)),
                ('read_right', models.BooleanField(blank=True, db_column='Read_Right', null=True)),
                ('write_right', models.BooleanField(blank=True, db_column='Write_Right', null=True)),
            ],
            options={
                'db_table': 'User_Permissions',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Users',
            fields=[
                ('user_id', models.AutoField(db_column='User_ID', primary_key=True, serialize=False)),
                ('first_name', models.CharField(db_column='First_Name', max_length=255)),
                ('last_name', models.CharField(db_column='Last_Name', max_length=255)),
                ('login', models.CharField(db_column='Login', max_length=255)),
                ('active_user', models.BooleanField(blank=True, db_column='Active_User', null=True)),
            ],
            options={
                'db_table': 'Users',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='ValMultiplier',
            fields=[
                ('val_multiplier_id', models.AutoField(db_column='Val_Multiplier_ID', primary_key=True, serialize=False)),
                ('multiplier_scale', models.IntegerField(db_column='Multiplier_Scale')),
            ],
            options={
                'db_table': 'Val_Multiplier',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='YearMonth',
            fields=[
                ('year_month_id', models.AutoField(db_column='Year_Month_ID', primary_key=True, serialize=False)),
                ('yyyy', models.IntegerField(db_column='YYYY')),
                ('mm', models.IntegerField(db_column='MM')),
            ],
            options={
                'db_table': 'Year_Month',
                'managed': False,
            },
        ),
    ]