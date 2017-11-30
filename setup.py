from distutils.core import setup
from pip.req import parse_requirements

install_req = parse_requirements('requirements/core.txt', session='skip')
req = [str(ir.req) for ir in install_req]


def read_md(filename):
    try:
        from pypandoc import convert_file
        return convert_file(filename, 'rst')
    except (ImportError, OSError):
        return open(filename).read()


setup(
    name='django_mock_queries',
    packages=['django_mock_queries'],
    version='1.0.5',
    description='A django library for mocking queryset functions in memory for testing',
    long_description=read_md('README.md'),
    author='Phivos Stylianides',
    author_email='stphivos@gmail.com',
    url='https://github.com/stphivos/django-mock-queries',
    keywords='django orm mocking unit-testing tdd',
    classifiers=[],
    install_requires=req
)
