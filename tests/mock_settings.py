from model_mommy.generators import gen_string

SECRET_KEY = gen_string(50)

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'tests',
)
