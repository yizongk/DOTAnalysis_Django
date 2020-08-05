This is Performance Management Unit (PMU) Django Web Apps repository

Includes:
 * Indicator Web App, Django style.

        The first iteration is Access, then an attempt to migrate over to ASP.NET (Which failed dued to lack of support from IT in regards to using their Production Server to host the ASp.NET Web App), and now migrating to Django

To install the python dependencies

python -m pip install -r PMU_DjangoWebApps/python_dependencies.txt

# Database
Need SQL Server Account, need to be of the following roles:
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

## First solution: ##
```
$.ajax({
    data: {
        somedata: 'somedata',
        moredata: 'moredata',
        csrfmiddlewaretoken: '{{ csrf_token }}'
    },
```
## Second Solution: ##

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

Note that if you are using Django official doc's answer (Our 2nd solution, https://docs.djangoproject.com/en/2.2/ref/csrf/) regarding .ajaxSetup, it will not work if in your Settings.py you have: (Delete the line! or set it to False!)
```
CSRF_USE_SESSIONS = True
```
Interestingly, from the same Django official doc, the other option of setting is CSRF_COOKIE_HTTPONLY. And if set to true, it won't affect our 2nd solution. But CSRF_USE_SESSIONS = True will affect.
```
CSRF_COOKIE_HTTPONLY = True // Will not cause our 2nd solution to not work.
```

# Serving static files by Apache
In your settings.py, make sure you have
```
STATIC_URL = '/static/'
```
In django templates, when you do
```
{% load static %}  // This loads the relate url (root + STATIC_URL), so result is like www.website.com/static/
<img src="{% static 'PMU_DjangoWebApps/dot_logo.jpg' %}" alt="My image" style="height:30px; width: 50px">
```
Then that /<img/> tag will ask Apache for www.website.com/static/PMU_DjangoWebApps/dot_logo.jpg
Add the following config with your other Django config in your apache/conf/httpd.conf
```
Alias /static/ "path_to_your_static_dir"
<Directory "path_to_your_static_dir">
    Require all granted
</Directory>
```
Because your Apache aliased /static/ to "path_to_your_static_dir", and you have set the permission for that dir for the web app, your static file will not be returned to the Django template!

# For issues with "None of the “sha384” hashes in the integrity attribute match the content of the subresource."
It has to do with the JS or css script that you are including with remote url links
https://stackoverflow.com/questions/32039568/what-are-the-integrity-and-crossorigin-attributes

# Note about datetime stored in the SQL Server database
https://docs.djangoproject.com/en/3.0/ref/settings/#std:setting-TIME_ZONE, Take a look at "TIME_ZONE" section.
https://docs.djangoproject.com/en/3.0/topics/i18n/timezones/, Take a look at "Overview" section and "Naive and aware datetime objects" section.

Because I am using USE_TZ = True in the settings.py, everything Django stores into the database is in UTC time format.
And since I am using TIME_ZONE = 'America/New_York' along side USE_TZ = True, "America/New_York" (EDT time) is the default time zone that Django will use to display datetimes in templates and to interpret datetimes entered in forms.
So the WebApp WebGrid ('Updated date' column) will show the time in Eastern Daylight Time (EDT) or AKA America/New_York, but SQL Server stores the datetime as UTC. So you should use django.utils.timezone.now() instead of datetime.datetime.now(), cuz timezone is "aware" and datetime is "naive". Otherwise, you will need to convert datetime.datetime.now() to the "America/New_York" timezone.

https://stackoverflow.com/questions/11909071/using-strftime-on-a-django-datetime-produces-a-utc-time-in-the-string
Since django.utils.timezone.now() returns a datetime that is 'aware' and not 'naive', so if you were to access directly to pieces of the django.utils.timezone.now(), like %M (Such as .strftime()), it will return UTC time format, and so you got to convert it to "America/New_York".

To convert, you need to something like this (The following will return New York timezone in a readable format):
```
from django.utils import timezone
local_timestamp_str = timezone.now().astimezone(pytz.timezone('America/New_York')).strftime("%B %d, %Y, %I:%M %p")
```

# Note on python manage.py migrate and makemigrations
https://stackoverflow.com/questions/30195699/should-django-migrations-live-in-source-control
On Prod, never do makemigrations. You should only apply the migrations.

# Note on overriding queryset or ust getqueryset() for Django class view ListView
https://stackoverflow.com/questions/19707237/use-get-queryset-method-or-set-queryset-variable
Quoted from the link
> "When you set queryset, the queryset is created only once, when you start your server. On the other hand, the get_queryset method is called for every request.
>
> That means that get_queryset is useful if you want to adjust the query dynamically. For example, you could return objects that belong to the current user"

# Note Django Class view ListView and Pagination
https://docs.djangoproject.com/en/3.0/topics/pagination/

https://stackoverflow.com/questions/5907575/how-do-i-use-pagination-with-django-class-based-generic-listviews

Note, thet ```model = models.Car``` is shorthand for setting queryset = models.car.objects.all()
Pagination is built in! So you don't need to do:
```
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
```
And you have to do is populate get_queryset() and add paginate_by:
```
class WebGridPageView(generic.ListView):
    context_object_name = 'indicator_data_entries'

    paginate_by = 12

    def get_queryset(self):
        return IndicatorData.objects.all()
```
And in the front end:
```
<div class="pagination">
    <span class="step-links">
        {% if page_obj.has_previous %}
            <a href="?page=1">&laquo; first</a>
            <a href="?page={{ page_obj.previous_page_number }}">previous</a>
        {% endif %}

        <span class="current">
            Page {{ page_obj.number }} of {{ page_obj.paginator.num_pages }}.
        </span>

        {% if page_obj.has_next %}
            <a href="?page={{ page_obj.next_page_number }}">next</a>
            <a href="?page={{ page_obj.paginator.num_pages }}">last &raquo;</a>
        {% endif %}
    </span>
</div>
```
So long, in the ListView that, you have queryset attribute set to something and set paginate_by attribute to something, it will work! model attribute and get_queryset() both will set the queryset attribute

# Compatibility with browsers
Works on the following:
* Firefox v.68.6.0esr (64-bit)
* Edge 44.17763.831.0
* Chrome 84.0.4147.105 (64-bit)
Doesn't work on the following:
* Internet Explorer 11.973.17763.0CO