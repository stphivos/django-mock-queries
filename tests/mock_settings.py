from django.core.exceptions import ImproperlyConfigured

try:
    from model_mommy.generators import gen_string
except ImproperlyConfigured:
    from model_mommy.random_gen import gen_string

SECRET_KEY = gen_string(50)

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'tests',
)
