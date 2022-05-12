from django.db import models

# Create your models here.
class ActiveDirectory(models.Model):
    object_guid         = models.CharField(db_column='ObjectGUID', max_length=100, primary_key=True)
    sid                 = models.CharField(db_column='SID', max_length=100, unique=True, blank=False, null=False)
    windows_username    = models.CharField(db_column='WindowsUsername', max_length=100, unique=True, blank=False, null=False)
    pms                 = models.CharField(db_column='PMS', max_length=7, blank=False, null=False)
    object_class        = models.CharField(db_column='ObjectClass', max_length=100, blank=False, null=False)
    enabled             = models.BooleanField(db_column='Enabled', blank=False, null=False)
    first_name          = models.CharField(db_column='FirstName', max_length=100)
    last_name           = models.CharField(db_column='LastName', max_length=100)
    full_name           = models.CharField(db_column='FullName', max_length=100)
    dot_email           = models.CharField(db_column='DOTEmail', max_length=100)

    class Meta:
        managed     = False
        db_table    = 'ActiveDirectory'

    def __str__(self):
        return self.windows_username

    ## This model should only accept SELECT statments. The rest of the statements should not be allowed
    def save(self, *args, **kwargs):
        return

    def delete(self, *args, **kwargs):
        return

    def create(self, *args, **kwargs):
        return

    def update(self, *args, **kwargs):
        return


class WebApps(models.Model):
    web_app_id      = models.AutoField(db_column='WebAppId', primary_key=True)
    web_app_name    = models.CharField(db_column='WebAppName', max_length=100, unique=True, blank=False, null=False)
    is_active       = models.BooleanField(db_column='IsActive', blank=False, null=False, default=True)

    class Meta:
        managed     = False
        db_table    = 'WebApps'

    def __str__(self):
        return self.web_app_name


class WebAppUserMemberships(models.Model):
    web_app_user_membership_id  = models.AutoField(db_column='WebAppUserMembershipId', primary_key=True)
    web_app_id                  = models.ForeignKey(db_column='WebAppId', to='WebApps', to_field='web_app_id', blank=False, null=False, on_delete=models.DO_NOTHING)
    windows_username            = models.ForeignKey(db_column='WindowsUsername', to='ActiveDirectory', to_field='windows_username', max_length=100, blank=False, null=False, on_delete=models.DO_NOTHING)
    is_admin                    = models.BooleanField(db_column='IsAdmin', blank=False, null=False, default=False)
    is_active                   = models.BooleanField(db_column='IsActive', blank=False, null=False, default=True)

    class Meta:
        managed     = False
        db_table    = 'WebAppUserMemberships'

    def __str__(self):
        return self.web_app_name