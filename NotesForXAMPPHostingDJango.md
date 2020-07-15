Need Microsfot C++ Build Tools
Ref: https://answers.microsoft.com/en-us/windows/forum/windows_10-windows_install/visual-c-14/f0445e6b-d461-4e40-b44f-962622628de7

Ref for mod_wsgi: https://modwsgi.readthedocs.io/en/develop/project-status.html (It's got next and previous button that will guide you to more pages on mod_wsgi)

For setting the MOD_WSGI_APACHE_ROOTDIR environmental variable, make sure to use forward slashes instead of backslashes (backslashes are interpreted by mod_wsgi-express as escapes): C:/xampp/apache
    Make sure you do this before attempting to install mod_wsgi with pip or python -m pip
    If you have done install with MOD_WSGI_APACHE_ROOTDIR set to something incorrect and not how ever you uninstall or install mod_wsgi, it's still using the old environmental variable, try removing the pip cache and then pip uninstall mod_wsgi and install it again.
        more specifically, the wheel: rm C:\Users\ykuang\AppData\Local\pip\cache\wheels\*
            This fixed the (because you were getting this error still, even though you may have changed the MOD_WSGI_APACHE_ROOTDIR env variable):
                LIBEXECDIR = 'C:\xampp\apache/lib'
                SyntaxError: (unicode error) 'unicodeescape' codec can't decode bytes in posistion 2-4: truncated \xXX escape







# For setting up Apache httpd.conf
https://stackoverflow.com/questions/36210686/importerror-no-module-named-mysite-settings-django
Make sure in your wsgi.py, add the following code, else you might get error in apache error log that "ModuleNotFoundError: No module named 'TestSite.settings'"
...
import sys
...
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)
...

https://blog.thebao.me/2020/03/python-django-host-django-project-with.html
Make sure your mod_wsgi.cp37-win_amd64.pyd is renamed to mod_wsgi.so in the xampp/apache/modules







Links that helped
https://wiki.processmaker.com/3.1/Windows_Single_SignOn
https://stackoverflow.com/questions/21102707/xampp-apache-shuts-down-unexpectedly-empty-log-file-and-no-events
https://stackoverflow.com/questions/34133019/setting-up-windows-authentication-for-apache
https://stackoverflow.com/questions/10105816/apache-2-ldap-active-directory-automatic-login-authentication-process
    But this really need 64 bit mod_auth_sspi.so for my 64 bit system. Hard to find 64 bit. But there is a 64 bit mod_authnz_sspi.sp from https://www.apachehaus.net/modules/mod_authnz_sspi/
    THIS IS THE ONE TO FOLLOW on mod_authnz_sspi.so:
        https://mid.as/active-directory-integration/configuring-apache
    And according to this link, mod_auth_sspi.so is for Apache 2.2 and mod_authnz_sspi.so is for Apache 2.4. I have Apache 2.4.
https://community.apachefriends.org/viewtopic.php?p=249529&sid=71a47a96a003daa42f5c9e16f4290cd9

https://chat.stackoverflow.com/rooms/59431/discussion-between-casey-falk-and-user3449833
https://stackoverflow.com/questions/25332433/django-grab-apache-user
https://django.readthedocs.io/en/1.4.X/howto/auth-remote-user.html
https://docs.djangoproject.com/en/dev/howto/auth-remote-user/

Wiki on ModAuthSSPI: https://cwiki.apache.org/confluence/display/HTTPD/ModAuthSSPI

https://www.maxongzb.com/why-asgi-is-replacing-wsgi-in-django-reading-time-3-mins/
https://stackoverflow.com/questions/34109324/what-makes-wsgi-is-synchronous-in-nature

https://arunrocks.com/a-guide-to-asgi-in-django-30-and-its-performance/
https://www.youtube.com/watch?v=RLo9RJhbOrQ

https://github.com/django/asgiref/issues/143, I have also added some comments to the link's github discussion.
    IMPORTANT: Use Django version 2.2.14, since in 3.0.8 when running with mod_wsgi, and the middleware specified in https://docs.djangoproject.com/en/3.0/howto/auth-remote-user/, you will get this error "ValueError: set_wakeup_fd only works in main thread" (More detailed in the link right above this line)
    The actual set up that caused the bug and crash
        python 3.8.1, apache v2.4.3, mod_authnz_sspi, mod_wsgi, django 3.0.8
            MIDDLEWARE = [
                '...',
                'django.contrib.auth.middleware.AuthenticationMiddleware',
                'django.contrib.auth.middleware.RemoteUserMiddleware',  # this causes "set_wakeup_fd only works in main thread" in django 3.0.8 but not in 2.2.14
                '...',
            ]

            AUTHENTICATION_BACKENDS = [
                'django.contrib.auth.backends.RemoteUserBackend',
            ]
    To install Django version 2.2.14: python -m pip install -Iv django==2.2.14

https://docs.djangoproject.com/en/3.0/releases/3.0/
Note on differnece between Django 2.0 and 3.0 is that 3.0 now supports ASGI support (Allowing Async operations).
    I am not planning on using ASGI (Async), I am planning on using WSGI (Synchous). Performance difference is minimal, with ASGI being a bit faster for the user base of my applications at DOT
    There was also some small upgrade of existing features, that doesn't seem very useful to my in my situation.
    Other than ASGI, doesn't seem like there's any new major features from upgrading 2.0 to 3.0



Notes on print() in Django. Any print() will appear in Apache's error log

Notes on wsgi.py
    On first time setup, you might run into error:
        mod_wsgi (pid=10266): Failed to exec Python script file '.../wsgi.py'
        https://stackoverflow.com/questions/49300999/mod-wsgi-exception-occurred-processing-wsgi-script-django-deployment
        Not the actual link that I the solution at, I couldn't find where I found the original solution(Found it, it was up at near the beginning of this file lol, https://stackoverflow.com/questions/36210686/importerror-no-module-named-mysite-settings-django), but this link is close enough.
        The actual changes you need to make to wsgi.py, add the following to wsgi.py, and it will solve the error:
        ```
        ...
        import sys
        ...
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if BASE_DIR not in sys.path:
            sys.path.append(BASE_DIR)
        ...
        ```

Notes on Disallowed Host
https://stackoverflow.com/questions/40582423/invalid-http-host-header
    You might encounter this error
    DisallowedHost at /
        Invalid HTTP_HOST header: 'dot-jckwhb2'. You may need to add 'dot-jckwhb2' to ALLOWED_HOSTS.

    This means, in your settings.py, you got to add 'dot-jckwhb2' to the allowed host, like so:
    ALLOWED_HOSTS = [
        'dot-jckwhb2'
    ]

Notes on OperationalError at /PerInd/
no such table: django_session
https://stackoverflow.com/questions/3631556/django-no-such-table-django-session/5869933
    Fixed by running the following at the root of the Django project:
    python manage.py makemigrations
    python manage.py migrate

Documenation on mod_authn_ntlm, which is similar to mod_authnz_sspi. mod_authnz_sspi is compiled from development source code (https://sourceforge.net/p/mod-auth-sspi/code/HEAD/tree/branches/mod_authnz_sspi/mod_authnz_sspi/) and no good documenation. The documentation of mod_authn_ntlm offers clues to mod_authnz_sspi.
https://github.com/TQsoft-GmbH/mod_authn_ntlm


# OVERALL Instructions
1. Install python (Check the Add to Path option), XAMPP, Visual C++ Build Tools (Required before installing mod-wsgi from python pip)
2. Set MOD_WSGI_APACHE_ROOTDIR env with your apache root dir from your Xampp installation (Typically C:/xampp/apache), and remember to use FORWARD SLASH //// not back slash, otherwise you will run into error when you install mod-wsgi and then run mod_wsgi-express module_config
3. Install Django 2.2.14, mod-wsgi 4.7.1
4. run mod_wsgi-express module-config to get two important variable values
    * wsgi_module path
    * WSGIPythonHome
5. Copy the wsgi_module path to C:/xampp/apache/modules/ as mod_wsgi.so, like so:
```
    cp {wsgi_module path} C:/xampp/apache/modules/mod_wsgi.so
```
6. Make a back up of C:\xampp\apache\conf\httpd.conf
7. Open the httpd.conf and add the following to the bottom of the file:
```
    LoadModule wsgi_module modules/mod_wsgi.so
    <IfModule wsgi_module>
        WSGIScriptAlias / "..../PMU_DjangoWebApps/PMU_DjangoWebApps/wsgi.py"
        WSGIPythonHome "{Your WSGIPythonHome variable value}"
        <Directory "{Path to one level before your django project}/PMU_DjangoWebApps">
            <Files wsgi.py>
                Allow from all
                Require all granted
            </Files>
        </Directory>
    </IfModule>
```
8. Open up your wsgi.py and add the following, to fix some include errors that will come up otherwise:
```
    ...
    import os
    ...
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if BASE_DIR not in sys.path:
        sys.path.append(BASE_DIR)
    ...
```
9. Add NTLM athentication to Apache
    * Download mod_authnz_sspi
    ```
        cp the Apache24/bin/sspipkgs to C:/xampp/apache/bin
        cp the Apache24/modules/mod_authnz_sspi.so to C:/xampp/apache/modules
    ```
    * Configure httpd.conf
        * Make sure that the following modules are uncommented (If it doesn't exists, add them to the https.conf)
        ```
            LoadModule authnz_sspi_module modules/mod_authnz_sspi.so
            LoadModule authn_core_module modules/mod_authn_core.so
            LoadModule authz_core_module modules/mod_authz_core.so
        ```
        * Add the following to the bottom of the conf, right before where you included LoadModule * wsgi_module modules/mod_wsgi.so
        ```
            LoadModule authnz_sspi_module modules/mod_authnz_sspi.so
        ```
        * Replace the content of <Files wsgi.py> </Files> with:
        ```
            Order deny,allow
            Allow from all

            AuthName "DOT Intranet"
            AuthType SSPI
            SSPIAuth On
            SSPIAuthoritative On
            SSPIOfferBasic Off
            SSPIOmitDomain On
            Require valid-user
        ```
10. Add middleware to Django project to grab from REMOTE_USER env that Apache sets for its NTLM authentication
    * Add the following to settings.py
    ```
        MIDDLEWARE = [
            '...',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.auth.middleware.RemoteUserMiddleware',
            '...',
        ]
    ```
    * In settings.py, replace ModelBackend with RemoteUserBackend in the AUTHENTICATION_BACKENDS
    ```
        AUTHENTICATION_BACKENDS = [
            'django.contrib.auth.backends.RemoteUserBackend',
        ]
    ```
    * To use, add the following codes to your webapp's Views.py
    ```
        def get_cur_client(request):
            cur_client = request.META['REMOTE_USER']
            return cur_client

        def index(request):
            cur_client = get_cur_client(request)
            return HttpResponse("Hello {}! You are at the PerInd Index".format(cur_client))
    ```
11. Run the following commands to prep the Django authen_user table, and database? Not sure what it does, but it does avoid "no such table: auth_user" error. Be at the Project's root_dir.
```
    python manage.py makemigrations
    python manage.py migrate
```
12. You should now be good to go, go start up apache in the xampp control panel, and got to 127.0.0.1 on your browser and test it out!