from django.http import HttpResponse

from analytics.api import AnalyticsApi
api = AnalyticsApi()


def active_users(*args, **kwargs):
    return HttpResponse(', '.join(
        [x.username for x in api.active_users()]
    ))
