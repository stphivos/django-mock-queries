from distutils.core import setup
from pip.req import parse_requirements

install_req = parse_requirements('requirements/requirements.txt', session='skip')
req = [str(ir.req) for ir in install_req]

setup(
    name='django_mock_queries',
    packages=['django_mock_queries'],
    version='0.0.16.5',
    description='A django library for mocking queryset functions in memory for testing',
    author='Phivos Stylianides',
    author_email='stphivos@gmail.com',
    url='https://github.com/stphivos/django-mock-queries',
    keywords=['django', 'mocking', 'unit-testing', 'tdd'],
    classifiers=[],
    install_requires=req
)
