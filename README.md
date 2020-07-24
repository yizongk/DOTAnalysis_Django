This is Performance Management Unit (PMU) Django Web Apps repository

Includes:
 * Indicator Web App, Django style.

        The first iteration is Access, then an attempt to migrate over to ASP.NET (Which failed dued to lack of support from IT in regards to using their Production Server to host the ASp.NET Web App), and now migrating to Django

To install the python dependencies

python -m pip install -r PMU_DjangoWebApps/python_dependencies.txt

# Database
Need SQL Server Account, need to be of the following rolse:
* db_datareader
* db_datawriter
* db_ddladmin (For DDL privilege, such as CREATE, DROP, ALTER TRUNCATE, and RENAME)

Notes on generating the database model from existing database
https://dev.to/idrisrampurawala/creating-django-models-of-an-existing-db-288m
Command is like so:
```
python manage.py table1 table2 > out_model_name.py

python manage.py inspectdb Category Data_Summary_Type Data_Type Indicator_Data Indicator_List Unit User_Permissions Users Val_Multiplier Year_Month > models.py
```

# Notes on django tags functions on template htmls
It seems like you can't comment them out with <-- -->. Ex.
```
<!-- {% extends 'template.base.html' %} -->
```
Would still get procesed by django.

Only get rid of it, is by delete the line of {extends} or add some invalid character to {extends} so it will be treated by normal html:
```
{% extends 'template.base.html' %}
to
{#% extends 'template.base.html' %}
```
Which will display "{#% extends 'template.base.html' %}" on the html when rendered on the broswer

# Notes on django tag '{ extends }'
Where ever you have this line, it's where the parent template starts rendering.
So if your {extends} is on line 2 of the html, the resulting html will have a line one with something, and then at line two is where the template is rendered.

# Notes Ajax POST CSRF not set error
https://docs.djangoproject.com/en/2.2/ref/csrf/
https://stackoverflow.com/questions/5100539/django-csrf-check-failing-with-an-ajax-post-request

stackoverflow over two working answer, one is to include the CSRF cookie in the POST data body, like (Both will expose your cookie value when you inspect the POST call in dev tools of Firefox of any browser, but first method will also expose the cookie value on the html doc, as it is hardcoded on there):

First solution:
```
$.ajax({
    data: {
        somedata: 'somedata',
        moredata: 'moredata',
        csrfmiddlewaretoken: '{{ csrf_token }}'
    },
```
Second Solution:

and the second solution is similar to Django official doc's solution:

Note: Cookies.get() comes from https://github.com/js-cookie/js-cookie/, so be sure to include this script in your html doc \<head\> tag like
```
<script src="https://cdn.jsdelivr.net/npm/js-cookie@rc/dist/js.cookie.min.js"></script>
```
And for the solution:
```
var csrftoken = Cookies.get('csrftoken');

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});
```

Note that if you are using Django official doc's answer (Our 2nd solution) regarding .ajaxSetup, it will not work if in your Settings.py you have: (Delete the line! or set it to False!)
```
CSRF_USE_SESSIONS = True
```