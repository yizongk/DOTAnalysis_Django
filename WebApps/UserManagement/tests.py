from .models import *
from WebAppsMain.settings import TEST_WINDOWS_USERNAME
from WebAppsMain.testing_utils import HttpPostTestCase, HttpGetTestCase
from django.core.exceptions import ObjectDoesNotExist

# Create your tests here.


class TestModelActiveDirectory(HttpGetTestCase):

    def test_must_not_save(self):
        try:
            user_obj = ActiveDirectory.objects.using('default').get(windows_username__exact=TEST_WINDOWS_USERNAME)
            user_obj.first_name = 'hey'
            user_obj.save(using='default')

            ## Test if data actually went through
            user_obj = ActiveDirectory.objects.using('default').get(windows_username__exact=TEST_WINDOWS_USERNAME)
            self.assertTrue(user_obj.first_anme != 'hey'
                ,f"TestModelActiveDirectory: Model cannot allow save(): save() seems to worked")
        except Exception as e:
            if 'This model is immutable.' not in str(e):
                self.assertTrue(False
                    ,f"TestModelActiveDirectory: Model cannot allow save(): {e}")
        else:
            self.assertTrue(False
                ,f"TestModelActiveDirectory: Model cannot allow save()")

    def test_must_not_delete(self):
        try:
            user_obj = ActiveDirectory.objects.using('default').get(windows_username__exact=TEST_WINDOWS_USERNAME)
            user_obj.delete(using='default')

            ## Test if data actually went through
            try:
                user_obj = ActiveDirectory.objects.using('default').get(windows_username__exact=TEST_WINDOWS_USERNAME)
            except ObjectDoesNotExist:
                self.assertTrue(False
                    ,f"TestModelActiveDirectory: Model cannot allow delete(): delete() seems to worked")
            else:
                pass ## Good! delete() didn't work!
        except Exception as e:
            if 'This model is immutable.' not in str(e):
                self.assertTrue(False
                    ,f"TestModelActiveDirectory: Model cannot allow delete(): {e}")
        else:
            self.assertTrue(False
                ,f"TestModelActiveDirectory: Model cannot allow delete()")

    def test_must_not_create(self):
        try:
            user_obj = ActiveDirectory.objects.using('default').create(
                object_guid='abc123'
                ,sid='abc1234'
                ,windows_username='abc'
                ,pms='1234567'
                ,object_class='asd'
                ,enabled=True
                ,first_name='first_n'
                ,last_name='last_n'
                ,full_name='full_n'
                ,dot_email='fn_ln@gmail.com'
            )

            ## Test if data actually went through
            try:
                user_obj = ActiveDirectory.objects.using('default').get(windows_username__exact='abc')
            except ObjectDoesNotExist:
                pass ## Good! create() didn't work!
            else:
                self.assertTrue(False
                    ,f"TestModelActiveDirectory: Model cannot allow create(): create() seems to worked")
        except Exception as e:
            if 'This model is immutable.' not in str(e):
                self.assertTrue(False
                    ,f"TestModelActiveDirectory: Model cannot allow create(): {e}")
        else:
            self.assertTrue(False
                ,f"TestModelActiveDirectory: Model cannot allow create()")

    def test_must_not_update(self):
        try:
            user_obj = ActiveDirectory.objects.using('default').get(windows_username__exact=TEST_WINDOWS_USERNAME)
            user_obj.update(full_name='some full name')

            ## Test if data actually went through
            user_obj = ActiveDirectory.objects.using('default').get(windows_username__exact=TEST_WINDOWS_USERNAME)
            self.assertTrue(user_obj.full_name != 'some full name'
                ,f"TestModelActiveDirectory: Model cannot allow update(): update() seems to worked")
        except Exception as e:
            if 'This model is immutable.' not in str(e):
                self.assertTrue(False
                    ,f"TestModelActiveDirectory: Model cannot allow update(): {e}")
        else:
            self.assertTrue(False
                ,f"TestModelActiveDirectory: Model cannot allow update()")