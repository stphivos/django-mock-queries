from pathlib import Path

from setuptools import setup


def read_md(filename):
    return Path(filename).read_text(encoding='utf-8')


def parse_requirements(filename):
    reqs = Path(filename).read_text(encoding='utf-8').splitlines()
    if not reqs:
        raise RuntimeError("Unable to read requirements from '%s'" % filename)
    return reqs


setup(
    name='django_mock_queries',
    version='2.3.0',
    description='A django library for mocking queryset functions in memory for testing',
    long_description=read_md('README.md'),
    long_description_content_type='text/markdown',
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
        'Programming Language :: Python :: 3 :: Only',
    ],
    keywords='django orm mocking unit-testing tdd',
    packages=['django_mock_queries'],
    install_requires=parse_requirements('requirements/core.txt'),
    python_requires='>=3.9',
)
