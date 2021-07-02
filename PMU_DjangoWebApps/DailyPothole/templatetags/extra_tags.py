from django import template
import datetime
register = template.Library()


## Returns the date from a given skip from today
@register.filter()
def addDaysFromToday(days):
    newDate = datetime.date.today() + datetime.timedelta(days=days)
    return newDate.strftime("%Y-%m-%d")