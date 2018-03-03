from random import choice
from string import ascii_letters


def gen_string(max_length):
    return str(''.join(choice(ascii_letters) for _ in range(max_length)))


SECRET_KEY = gen_string(50)

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'tests',
)
