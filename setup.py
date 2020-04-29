from setuptools import setup


def read_md(filename):
    try:
        from pypandoc import convert_file
        return convert_file(filename, 'rst')
    except (ImportError, OSError):
        return open(filename).read()


def parse_requirements(filename):
    reqs = []
    with open(filename, 'r') as f:
        reqs = f.read().splitlines()
    if not reqs:
        raise RuntimeError("Unable to read requirements from '%s'" % filename)
    return reqs


setup(
    name='django_mock_queries',
    version='2.1.4',
    description='A django library for mocking queryset functions in memory for testing',
    long_description=read_md('README.md'),
    url='https://github.com/stphivos/django-mock-queries',
    author='Phivos Stylianides',
    author_email='stphivos@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Testing',
        'Topic :: Software Development :: Testing :: Mocking',
        'Topic :: Software Development :: Testing :: Unit',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='django orm mocking unit-testing tdd',
    packages=['django_mock_queries'],
    install_requires=parse_requirements('requirements/core.txt'),
)
