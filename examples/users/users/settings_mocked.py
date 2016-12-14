from django_mock_queries.mocks import monkey_patch_test_db

from users.settings import *

monkey_patch_test_db()
