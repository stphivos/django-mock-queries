from datetime import date
from django.contrib.auth.models import User
from django.db.models import Count


class AnalyticsApi:
    def active_users(self):
        return User.objects.filter(is_active=True).all()

    def create_user(self, **attrs):
        return User.objects.create(**attrs)

    def today_visitors_count(self):
        result = User.objects.filter(last_login__gte=date.today()).aggregate(Count('last_login'))
        return result['last_login__count']

    def staff_usernames(self):
        return User.objects.filter(is_staff=True).values_list('username', flat=True)
